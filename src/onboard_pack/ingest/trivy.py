"""Trivy JSON SchemaVersion 2 parser."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from onboard_pack.ingest.types import ParseResult
from onboard_pack.models import CONTROL_HINTS, Finding, Severity

_HINTS = CONTROL_HINTS["container-scan"]


def parse_trivy(path: Path) -> ParseResult | None:
    """Return a parse result if the file looks like Trivy JSON, else None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return ParseResult(
            kind="container-scan",
            parsed=False,
            warning=f"unparsed container-scan {path.name}: {exc}",
        )
    if not isinstance(data, dict):
        return None
    if "Results" not in data and "SchemaVersion" not in data:
        return None
    findings: list[Finding] = []
    results = data.get("Results")
    if isinstance(results, list):
        for result in results:
            if not isinstance(result, dict):
                continue
            vulns = result.get("Vulnerabilities") or []
            if not isinstance(vulns, list):
                continue
            for vuln in vulns:
                if isinstance(vuln, dict):
                    findings.append(_finding(vuln))
    return ParseResult(
        kind="container-scan",
        parsed=True,
        warning=None,
        findings=findings,
    )


def _finding(vuln: dict[str, Any]) -> Finding:
    vuln_id = str(vuln.get("VulnerabilityID") or "UNKNOWN")
    pkg = str(vuln.get("PkgName") or "unknown")
    version = str(vuln.get("InstalledVersion") or "")
    target = f"{pkg}@{version}" if version else pkg
    severity = _severity(vuln.get("Severity"))
    return Finding(
        id=f"trivy:{vuln_id}:{pkg}",
        source="container-scan",
        severity=severity,
        title=vuln_id,
        target=target,
        controlHints=list(_HINTS),
    )


def _severity(value: object) -> Severity:
    if isinstance(value, str):
        try:
            return Severity[value.upper()]
        except KeyError:
            return Severity.UNKNOWN
    return Severity.UNKNOWN
