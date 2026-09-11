"""Ingest adapters — one module per tool format."""

from __future__ import annotations

from pathlib import Path

from onboard_pack.ingest.copy import parse_yaml_copy
from onboard_pack.ingest.cyclonedx import parse_cyclonedx
from onboard_pack.ingest.discover import classify, discover
from onboard_pack.ingest.opaque import opaque
from onboard_pack.ingest.spdx import parse_spdx
from onboard_pack.ingest.trivy import parse_trivy
from onboard_pack.ingest.types import ParseResult


def parse_artifact(path: Path, kind: str) -> ParseResult:
    """Parse one file. Never raises for unknown formats — hash-copy + warning."""
    if kind == "sbom":
        cdx = parse_cyclonedx(path)
        if cdx is not None and cdx.parsed:
            return cdx
        spdx = parse_spdx(path)
        if spdx is not None and spdx.parsed:
            return spdx
        warning = None
        if cdx is not None and cdx.warning:
            warning = cdx.warning
        elif spdx is not None and spdx.warning:
            warning = spdx.warning
        return opaque(path, kind, warning)
    if kind == "container-scan":
        trivy = parse_trivy(path)
        if trivy is not None and trivy.parsed:
            return trivy
        warning = trivy.warning if trivy is not None else None
        if warning is None:
            warning = f"unparsed container-scan {path.name}: not Trivy JSON (opaque copy)"
        return opaque(path, kind, warning)
    if kind in {"data-flow", "ppsm"}:
        return parse_yaml_copy(path, kind)
    return opaque(path, kind)


__all__ = ["discover", "classify", "parse_artifact", "ParseResult"]
