"""Pack orchestrator: ingest, gates, write tree, validate, zip."""

from __future__ import annotations

import json
import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

from onboard_pack.errors import PackError
from onboard_pack.gitmeta import git_metadata
from onboard_pack.hashutil import sha256_file
from onboard_pack.ingest import discover, parse_artifact
from onboard_pack.manifest import (
    artifact_digest,
    build_counts,
    build_manifest,
    utc_now,
    validate_manifest_document,
    write_json,
)
from onboard_pack.map import load_inheritance, load_overlay, resolve_controls
from onboard_pack.models import (
    KIND_DEST,
    Artifact,
    Finding,
    InputRecord,
    ResolvedControl,
    Severity,
)
from onboard_pack.render import render_human, render_oscal


@dataclass
class PackResult:
    out_dir: Path
    gates_passed: bool
    failures: list[str]
    warnings: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def run_pack(
    input_dir: Path,
    overlay_path: Path,
    inheritance_path: Path,
    out_dir: Path,
    strict: bool = False,
) -> PackResult:
    """Write a pack directory. Raises GateError after write if gates fail."""
    if not input_dir.is_dir():
        raise PackError(f"input directory not found: {input_dir}")
    input_resolved = input_dir.resolve()
    out_resolved = out_dir.expanduser().resolve()
    if input_resolved == out_resolved:
        raise PackError("--out must not be the same directory as --input")

    overlay = load_overlay(overlay_path)
    inheritance = load_inheritance(inheritance_path)
    controls = resolve_controls(overlay, inheritance)

    warnings: list[str] = []
    discovered = discover(input_resolved, out_resolved)
    kind_counts = Counter(kind for _, kind in discovered)
    for kind, count in sorted(kind_counts.items()):
        if count > 1:
            warnings.append(f"multiple files of kind {kind}: {count}")

    artifacts: list[Artifact] = []
    findings: list[Finding] = []
    component_names: list[str] = []
    for path, kind in discovered:
        digest, size = sha256_file(path)
        parsed = parse_artifact(path, kind)
        if parsed.warning:
            warnings.append(parsed.warning)
        findings.extend(parsed.findings)
        component_names.extend(parsed.component_names)
        try:
            rel = path.resolve().relative_to(input_resolved).as_posix()
        except ValueError:
            rel = path.name
        artifacts.append(
            Artifact(
                source_path=path,
                kind=kind,
                sha256=digest,
                size=size,
                parsed=parsed.parsed,
                warning=parsed.warning,
                component_names=parsed.component_names,
                dest_relpath=rel,
            )
        )

    kinds_present = sorted({item.kind for item in artifacts})
    _apply_evidence(controls, kinds_present)
    failures = _gate_failures(controls, findings, strict=strict)

    for finding in findings:
        if finding.severity is Severity.UNKNOWN:
            warnings.append(f"finding {finding.id} has UNKNOWN severity")

    git_commit, git_dirty, git_warning = git_metadata(input_resolved)
    if git_warning:
        warnings.append(git_warning)

    generated_at = utc_now()
    out_resolved.mkdir(parents=True, exist_ok=True)
    copied_inputs = _copy_artifacts(artifacts, out_resolved)

    write_json(
        out_resolved / "findings" / "normalized.json",
        [item.model_dump(mode="json") for item in findings],
    )
    write_json(
        out_resolved / "inheritance.json",
        {
            "system": inheritance.system,
            "inheritsFrom": inheritance.inheritsFrom,
            "disclaimer": "Declared inheritance, not verified.",
            "controls": [item.model_dump(mode="json") for item in controls],
        },
    )
    render_oscal(
        out_dir=out_resolved,
        system=inheritance.system,
        controls=controls,
        component_names=component_names,
    )
    render_human(
        out_dir=out_resolved,
        system=inheritance.system,
        overlay_id=overlay.id,
        generated_at=generated_at,
        git_commit=git_commit,
        controls=controls,
        findings=findings,
        kinds_present=kinds_present,
        gates_passed=not failures,
        failures=failures,
    )

    digest = artifact_digest(out_resolved)
    counts = build_counts(findings, controls)
    manifest = build_manifest(
        generated_at=generated_at,
        input_dir=input_resolved,
        overlay_id=overlay.id,
        overlay_path=overlay_path.resolve(),
        inheritance_path=inheritance_path.resolve(),
        git_commit=git_commit,
        git_dirty=git_dirty,
        inputs=copied_inputs,
        counts=counts,
        gates_passed=not failures,
        failures=failures,
        digest=digest,
    )
    write_json(out_resolved / "manifest.json", manifest)

    return PackResult(
        out_dir=out_resolved,
        gates_passed=not failures,
        failures=failures,
        warnings=warnings,
        findings=findings,
    )


def validate_pack(pack_dir: Path) -> list[str]:
    """Re-check manifest schema and gate rules. Returns failures (empty = pass)."""
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        raise PackError(f"not a pack (missing manifest.json): {pack_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackError(f"manifest.json unreadable: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PackError("manifest.json invalid: expected an object")
    try:
        validate_manifest_document(manifest)
    except jsonschema.ValidationError as exc:
        raise PackError(f"manifest schema validation failed: {exc.message}") from exc

    stored_digest = manifest.get("artifactDigest")
    actual_digest = artifact_digest(pack_dir)
    if stored_digest != actual_digest:
        raise PackError("artifactDigest does not match pack contents")

    inheritance_path = pack_dir / "inheritance.json"
    if not inheritance_path.is_file():
        raise PackError("pack missing inheritance.json")
    try:
        inheritance = json.loads(inheritance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackError(f"inheritance.json unreadable: {exc}") from exc

    kinds = {
        item.get("kind")
        for item in manifest.get("inputs", [])
        if isinstance(item, dict)
    }
    failures: list[str] = []
    controls = inheritance.get("controls") if isinstance(inheritance, dict) else None
    if not isinstance(controls, list):
        raise PackError("inheritance.json invalid: controls must be a list")
    for control in controls:
        if not isinstance(control, dict):
            continue
        status = control.get("status")
        control_id = control.get("id", "?")
        required = control.get("requiredEvidence") or []
        if status in {"owned", "shared"}:
            for kind in required:
                if kind not in kinds:
                    failures.append(
                        f"owned/shared control {control_id} missing required evidence kind {kind}"
                    )
    stored = manifest.get("gates") or {}
    if stored.get("passed") and failures:
        failures.append("manifest gates.passed is true but evidence is missing")
    return failures


def zip_pack(pack_dir: Path, out_file: Path) -> Path:
    """Zip the pack tree so manifest.json is in the archive."""
    root = pack_dir.resolve()
    if not (root / "manifest.json").is_file():
        raise PackError(f"not a pack (missing manifest.json): {pack_dir}")
    out_file = out_file.expanduser()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            archive.write(path, path.relative_to(root).as_posix())
    return out_file


def diff_packs(from_dir: Path, to_dir: Path) -> str:
    """Markdown diff of findings and gate flips."""
    from_findings = _load_findings(from_dir)
    to_findings = _load_findings(to_dir)
    from_ids = {item["id"]: item for item in from_findings if "id" in item}
    to_ids = {item["id"]: item for item in to_findings if "id" in item}
    added = [to_ids[key] for key in sorted(set(to_ids) - set(from_ids))]
    removed = [from_ids[key] for key in sorted(set(from_ids) - set(to_ids))]
    from_gates = _load_gates(from_dir)
    to_gates = _load_gates(to_dir)

    lines = ["# Pack diff", ""]
    lines.append("## Findings added")
    if added:
        for item in added:
            lines.append(
                f"- {item.get('severity', '?')} {item.get('title', item['id'])} "
                f"({item.get('target', '')}) `{item['id']}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Findings removed"])
    if removed:
        for item in removed:
            lines.append(
                f"- {item.get('severity', '?')} {item.get('title', item['id'])} `{item['id']}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Gate flips"])
    if from_gates.get("passed") != to_gates.get("passed"):
        lines.append(
            f"- passed: {from_gates.get('passed')} -> {to_gates.get('passed')}"
        )
    from_fail = set(from_gates.get("failures") or [])
    to_fail = set(to_gates.get("failures") or [])
    for item in sorted(to_fail - from_fail):
        lines.append(f"- added failure: {item}")
    for item in sorted(from_fail - to_fail):
        lines.append(f"- cleared failure: {item}")
    if from_gates.get("passed") == to_gates.get("passed") and from_fail == to_fail:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _apply_evidence(controls: list[ResolvedControl], kinds_present: list[str]) -> None:
    present = set(kinds_present)
    for control in controls:
        found_kinds = [kind for kind in control.requiredEvidence if kind in present]
        control.kindsPresent = found_kinds
        if control.status in {"inherited", "na"}:
            control.evidenceFound = True
        else:
            missing = [kind for kind in control.requiredEvidence if kind not in present]
            control.evidenceFound = not missing


def _gate_failures(
    controls: list[ResolvedControl],
    findings: list[Finding],
    *,
    strict: bool,
) -> list[str]:
    failures: list[str] = []
    for control in controls:
        if control.status in {"owned", "shared"}:
            for kind in control.requiredEvidence:
                if kind not in control.kindsPresent:
                    failures.append(
                        f"owned/shared control {control.id} missing required evidence kind {kind}"
                    )
    if strict:
        critical = [item for item in findings if item.severity is Severity.CRITICAL]
        if critical:
            failures.append(f"--strict: {len(critical)} CRITICAL finding(s)")
    return failures


def _copy_artifacts(artifacts: list[Artifact], out_dir: Path) -> list[InputRecord]:
    used_names: dict[str, int] = {}
    records: list[InputRecord] = []
    for artifact in artifacts:
        dest_dir = out_dir / KIND_DEST.get(artifact.kind, "scans")
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = artifact.source_path.name
        key = f"{dest_dir.name}/{name}"
        used_names[key] = used_names.get(key, 0) + 1
        if used_names[key] > 1:
            name = f"{artifact.source_path.stem}-{artifact.sha256[:8]}{artifact.source_path.suffix}"
        dest = dest_dir / name
        shutil.copy2(artifact.source_path, dest)
        records.append(
            InputRecord(
                path=artifact.dest_relpath,
                kind=artifact.kind,
                sha256=artifact.sha256,
                bytes=artifact.size,
            )
        )
    return records


def _load_findings(pack_dir: Path) -> list[dict[str, object]]:
    path = pack_dir / "findings" / "normalized.json"
    if not path.is_file():
        raise PackError(f"pack missing findings/normalized.json: {pack_dir}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackError(f"findings unreadable: {exc}") from exc
    if not isinstance(data, list):
        raise PackError("findings/normalized.json must be a list")
    return [item for item in data if isinstance(item, dict)]


def _load_gates(pack_dir: Path) -> dict[str, object]:
    path = pack_dir / "manifest.json"
    if not path.is_file():
        raise PackError(f"not a pack (missing manifest.json): {pack_dir}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackError(f"manifest unreadable: {exc}") from exc
    gates = manifest.get("gates") if isinstance(manifest, dict) else None
    if not isinstance(gates, dict):
        return {"passed": None, "failures": []}
    return gates
