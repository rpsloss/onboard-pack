"""Ingest parse result."""

from __future__ import annotations

from dataclasses import dataclass, field

from onboard_pack.models import Finding


@dataclass
class ParseResult:
    kind: str
    parsed: bool
    warning: str | None = None
    findings: list[Finding] = field(default_factory=list)
    component_names: list[str] = field(default_factory=list)
