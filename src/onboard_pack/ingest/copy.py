"""YAML copy-through for data-flow and ppsm worksheets."""

from __future__ import annotations

from pathlib import Path

import yaml

from onboard_pack.ingest.types import ParseResult


def parse_yaml_copy(path: Path, kind: str) -> ParseResult:
    """Accept any YAML mapping/list as parsed copy-through."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        return ParseResult(
            kind=kind,
            parsed=False,
            warning=f"unparsed {kind} {path.name}: {exc}",
        )
    if raw is None:
        return ParseResult(
            kind=kind,
            parsed=False,
            warning=f"unparsed {kind} {path.name}: empty document",
        )
    return ParseResult(kind=kind, parsed=True, warning=None)
