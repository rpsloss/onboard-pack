"""CycloneDX JSON SBOM parser."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from onboard_pack.ingest.types import ParseResult


def parse_cyclonedx(path: Path) -> ParseResult | None:
    """Return a parse result if the file is CycloneDX JSON, else None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return ParseResult(
            kind="sbom",
            parsed=False,
            warning=f"unparsed sbom {path.name}: {exc}",
        )
    if not isinstance(data, dict):
        return None
    if data.get("bomFormat") != "CycloneDX" and "specVersion" not in data:
        return None
    names = _component_names(data)
    return ParseResult(
        kind="sbom",
        parsed=True,
        warning=None,
        component_names=names,
    )


def _component_names(data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        component = metadata.get("component")
        if isinstance(component, dict):
            name = component.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    components = data.get("components")
    if isinstance(components, list):
        for item in components:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name:
                    names.append(name)
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique
