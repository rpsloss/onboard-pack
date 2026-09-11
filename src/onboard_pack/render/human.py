"""Human Markdown: checklist and control-status cheat sheet."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from onboard_pack.models import SEVERITY_ORDER, Finding, ResolvedControl, Severity

_ENV = Environment(
    loader=PackageLoader("onboard_pack.render", "templates"),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_human(
    *,
    out_dir: Path,
    system: str,
    overlay_id: str,
    generated_at: str,
    git_commit: str | None,
    controls: list[ResolvedControl],
    findings: list[Finding],
    kinds_present: list[str],
    gates_passed: bool,
    failures: list[str],
) -> None:
    human_dir = out_dir / "human"
    human_dir.mkdir(parents=True, exist_ok=True)
    finding_counts = _counts_by_control(controls, findings)
    top = sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], item.id))[:25]
    network = {
        "data-flow": "data-flow" in kinds_present,
        "ppsm": "ppsm" in kinds_present,
    }

    def evidence_cell(control: ResolvedControl) -> str:
        if control.status in {"inherited", "na"}:
            return "n-a"
        return "yes" if control.evidenceFound else "no"

    def finding_cell(control_id: str) -> str:
        counts = finding_counts[control_id]
        return (
            f"{counts['CRITICAL']}/{counts['HIGH']}/"
            f"{counts['MEDIUM']}/{counts['LOW']}"
        )

    def control_line(control: ResolvedControl) -> str:
        if control.status == "inherited":
            provider = control.provider or "unspecified"
            return f"{control.id} inherited (declared) from {provider}"
        if control.status == "shared":
            kinds = ", ".join(control.kindsPresent) or "none"
            provider = control.provider or "unspecified"
            return f"{control.id} shared with {provider}; evidence: {kinds}"
        if control.status == "na":
            suffix = f": {control.note}" if control.note else ""
            return f"{control.id} na{suffix}"
        if not control.evidenceFound:
            missing = [
                kind
                for kind in control.requiredEvidence
                if kind not in control.kindsPresent
            ]
            return f"MISSING: {control.id} owned; missing {', '.join(missing)}"
        kinds = ", ".join(control.requiredEvidence) or "none"
        return f"{control.id} owned; evidence: {kinds}"

    checklist = _ENV.get_template("onboard-checklist.md.j2").render(
        system=system,
        overlay_id=overlay_id,
        generated_at=generated_at,
        git_commit=git_commit or "unavailable",
        gates_passed=gates_passed,
        failures=failures,
        controls=controls,
        top_findings=top,
        network=network,
        pack_dir=str(out_dir),
        evidence_cell=evidence_cell,
        finding_cell=finding_cell,
    )
    (human_dir / "onboard-checklist.md").write_text(checklist, encoding="utf-8")
    delta = _ENV.get_template("delta-ssp.md.j2").render(
        controls=controls,
        control_line=control_line,
    )
    (human_dir / "delta-ssp.md").write_text(delta, encoding="utf-8")


def _counts_by_control(
    controls: list[ResolvedControl],
    findings: list[Finding],
) -> dict[str, dict[str, int]]:
    empty = {item.value: 0 for item in Severity}
    counts: dict[str, dict[str, int]] = {control.id: dict(empty) for control in controls}
    for finding in findings:
        for hint in finding.controlHints:
            if hint in counts:
                counts[hint][finding.severity.value] += 1
    return counts
