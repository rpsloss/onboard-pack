"""Opaque hash-copy for unparsed but present artifacts."""

from __future__ import annotations

from pathlib import Path

from onboard_pack.ingest.types import ParseResult


def opaque(path: Path, kind: str, reason: str | None = None) -> ParseResult:
    warning = reason or f"unparsed {kind} {path.name}: treated as opaque artifact"
    return ParseResult(kind=kind, parsed=False, warning=warning)
