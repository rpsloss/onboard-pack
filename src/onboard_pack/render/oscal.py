"""Simplified OSCAL-shaped JSON stubs."""

from __future__ import annotations

from pathlib import Path

from onboard_pack.manifest import write_json
from onboard_pack.models import ResolvedControl

DISCLAIMER = (
    "Simplified onboard-pack export; not a complete OSCAL document. "
    "Results are evidence-presence, not control assessment."
)
OSCAL_VERSION = "1.1.2"


def render_oscal(
    *,
    out_dir: Path,
    system: str,
    controls: list[ResolvedControl],
    component_names: list[str],
) -> None:
    oscal_dir = out_dir / "oscal"
    write_json(oscal_dir / "component-definition.json", _component_definition(system, component_names))
    write_json(oscal_dir / "assessment-results.json", _assessment_results(controls))
    write_json(oscal_dir / "poam.json", _poam())


def _component_definition(system: str, component_names: list[str]) -> dict[str, object]:
    components: list[dict[str, str]] = [{"name": system, "type": "application"}]
    seen = {system}
    for name in component_names:
        if name in seen:
            continue
        seen.add(name)
        components.append({"name": name, "type": "software"})
        if len(components) >= 51:  # application + 50 SBOM names
            break
    return {
        "oscalVersion": OSCAL_VERSION,
        "disclaimer": DISCLAIMER,
        "system": system,
        "components": components,
    }


def _assessment_results(controls: list[ResolvedControl]) -> dict[str, object]:
    results: list[dict[str, str]] = []
    for control in controls:
        if control.status in {"owned", "shared"} and not control.evidenceFound:
            status = "fail"
            remarks = "evidence-missing"
        elif control.status == "inherited":
            status = "other"
            remarks = "declared-inherited"
        elif control.status == "na":
            status = "other"
            remarks = "na"
        else:
            status = "other"
            remarks = "evidence-present"
        results.append(
            {
                "controlId": control.id,
                "status": status,
                "remarks": remarks,
            }
        )
    return {
        "oscalVersion": OSCAL_VERSION,
        "disclaimer": DISCLAIMER,
        "results": results,
    }


def _poam() -> dict[str, object]:
    return {
        "oscalVersion": OSCAL_VERSION,
        "disclaimer": DISCLAIMER,
        "items": [],
    }


