"""SPDX JSON SBOM parser (name + count only)."""

from __future__ import annotations

import json
from pathlib import Path

from onboard_pack.ingest.types import ParseResult


def parse_spdx(path: Path) -> ParseResult | None:
    """Return a parse result if the file is SPDX JSON, else None."""
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
    if "spdxVersion" not in data and "SPDXID" not in data:
        return None
    names: list[str] = []
    name = data.get("name")
    if isinstance(name, str) and name:
        names.append(name)
    packages = data.get("packages")
    if isinstance(packages, list):
        for item in packages:
            if isinstance(item, dict):
                pkg_name = item.get("name")
                if isinstance(pkg_name, str) and pkg_name:
                    names.append(pkg_name)
    return ParseResult(kind="sbom", parsed=True, warning=None, component_names=names)
