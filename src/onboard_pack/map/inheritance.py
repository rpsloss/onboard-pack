"""Load inheritance YAML and resolve against an overlay."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from onboard_pack.errors import GateError
from onboard_pack.models import (
    InheritanceEntry,
    InheritanceFile,
    Overlay,
    ResolvedControl,
)

VALID_STATUSES = {"inherited", "owned", "shared", "na"}


def load_inheritance(path: Path) -> InheritanceFile:
    """Load and validate an inheritance file. Missing/invalid is a gate failure."""
    if not path.is_file():
        raise GateError(f"inheritance file missing: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GateError(f"inheritance file unreadable: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise GateError(f"inheritance file invalid: {exc}") from exc
    if not isinstance(raw, dict):
        raise GateError("inheritance file invalid: expected a mapping")
    controls_raw = raw.get("controls") or {}
    if not isinstance(controls_raw, dict):
        raise GateError("inheritance file invalid: controls must be a mapping")
    normalized: dict[str, object] = dict(raw)
    entries: dict[str, InheritanceEntry] = {}
    for control_id, value in controls_raw.items():
        if not isinstance(value, dict):
            raise GateError(
                f"inheritance file invalid: control {control_id} must be a mapping"
            )
        status = value.get("status")
        if status not in VALID_STATUSES:
            raise GateError(
                f"inheritance file invalid: control {control_id} has status {status!r}"
            )
        try:
            entries[str(control_id)] = InheritanceEntry.model_validate(value)
        except ValidationError as exc:
            raise GateError(f"inheritance file invalid: {control_id}: {exc}") from exc
    normalized["controls"] = {key: entry.model_dump() for key, entry in entries.items()}
    try:
        return InheritanceFile.model_validate(normalized)
    except ValidationError as exc:
        raise GateError(f"inheritance file invalid: {exc}") from exc


def resolve_controls(overlay: Overlay, inheritance: InheritanceFile) -> list[ResolvedControl]:
    """Every overlay control appears; missing inheritance keys default to owned."""
    declared = inheritance.controls
    resolved: list[ResolvedControl] = []
    for control in overlay.controls:
        extra: InheritanceEntry | None = declared.get(control.id)
        if extra is None:
            status = "owned"
            provider = None
            note = None
        else:
            status = extra.status
            provider = extra.provider
            note = extra.note
        resolved.append(
            ResolvedControl(
                id=control.id,
                title=control.title,
                family=control.family,
                status=status,
                provider=provider,
                note=note,
                requiredEvidence=list(control.requiredEvidence),
            )
        )
    return resolved
