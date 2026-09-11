"""Load overlay YAML."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from onboard_pack.errors import GateError
from onboard_pack.models import Overlay


def load_overlay(path: Path) -> Overlay:
    """Load and validate an overlay file. Missing/invalid is a gate failure."""
    if not path.is_file():
        raise GateError(f"overlay file missing: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GateError(f"overlay file unreadable: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise GateError(f"overlay file invalid: {exc}") from exc
    if not isinstance(raw, dict):
        raise GateError("overlay file invalid: expected a mapping")
    try:
        overlay = Overlay.model_validate(raw)
    except ValidationError as exc:
        raise GateError(f"overlay file invalid: {exc}") from exc
    if not overlay.controls:
        raise GateError("overlay file invalid: controls list is empty")
    ids = [item.id for item in overlay.controls]
    if len(ids) != len(set(ids)):
        raise GateError("overlay file invalid: duplicate control ids")
    return overlay
