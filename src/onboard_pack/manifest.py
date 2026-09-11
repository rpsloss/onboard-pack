"""Manifest build, digest, and schema validation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from onboard_pack import __version__
from onboard_pack.errors import PackError
from onboard_pack.hashutil import sha256_bytes, sha256_file
from onboard_pack.models import Finding, InputRecord, ResolvedControl, Severity


def artifact_digest(pack_dir: Path) -> str:
    """SHA-256 of sorted path\\thash lines for every pack file except manifest.json."""
    root = pack_dir.resolve()
    lines: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "manifest.json":
            continue
        file_hash, _ = sha256_file(path)
        lines.append(f"{rel}\t{file_hash}\n")
    payload = "".join(lines).encode("utf-8")
    return sha256_bytes(payload)


def build_counts(
    findings: list[Finding],
    controls: list[ResolvedControl],
) -> dict[str, dict[str, int]]:
    finding_counts = {item.value: 0 for item in Severity}
    for finding in findings:
        finding_counts[finding.severity.value] += 1
    control_counts = {
        "inherited": 0,
        "owned": 0,
        "shared": 0,
        "na": 0,
        "missing-evidence": 0,
    }
    for control in controls:
        control_counts[control.status] += 1
        if control.status in {"owned", "shared"} and not control.evidenceFound:
            control_counts["missing-evidence"] += 1
    return {"findings": finding_counts, "controls": control_counts}


def build_manifest(
    *,
    generated_at: str,
    input_dir: Path,
    overlay_id: str,
    overlay_path: Path,
    inheritance_path: Path,
    git_commit: str | None,
    git_dirty: bool | None,
    inputs: list[InputRecord],
    counts: dict[str, dict[str, int]],
    gates_passed: bool,
    failures: list[str],
    digest: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": "0.1.0",
        "generatedAt": generated_at,
        "toolVersion": __version__,
        "source": {
            "inputDir": str(input_dir),
            "gitCommit": git_commit,
            "gitDirty": git_dirty,
        },
        "overlayId": overlay_id,
        "overlayPath": str(overlay_path),
        "inheritancePath": str(inheritance_path),
        "artifactDigest": digest,
        "inputs": [item.model_dump() for item in inputs],
        "counts": counts,
        "gates": {"passed": gates_passed, "failures": failures},
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def schema_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "schemas" / "pack.manifest.schema.json",
        here.parent / "data" / "pack.manifest.schema.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise PackError("manifest schema not found (schemas/pack.manifest.schema.json)")


def validate_manifest_document(document: dict[str, Any]) -> None:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    jsonschema.validate(instance=document, schema=schema)


def write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
