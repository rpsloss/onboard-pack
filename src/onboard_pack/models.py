"""Shared v0.1 types."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"


SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
    Severity.UNKNOWN: 5,
}

ControlStatus = Literal["inherited", "owned", "shared", "na"]

EVIDENCE_KINDS = (
    "sbom",
    "container-scan",
    "iac-scan",
    "sast",
    "stig",
    "data-flow",
    "ppsm",
    "other",
)

CONTROL_HINTS: dict[str, list[str]] = {
    "sbom": ["CM-8", "SR-3"],
    "container-scan": ["RA-5", "SI-2", "CA-7"],
    "iac-scan": ["CM-2"],
    "sast": ["SA-15"],
    "stig": ["CM-6"],
    "data-flow": ["AC-4"],
    "ppsm": ["SC-7"],
}

KIND_DEST: dict[str, str] = {
    "sbom": "sbom",
    "container-scan": "scans",
    "iac-scan": "scans",
    "sast": "scans",
    "stig": "stig",
    "data-flow": "network",
    "ppsm": "network",
    "other": "scans",
}


class OverlayControl(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str = ""
    family: str = ""
    requiredEvidence: list[str] = Field(default_factory=list)


class Overlay(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str = ""
    version: str = ""
    controls: list[OverlayControl]


class InheritanceEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: ControlStatus
    provider: str | None = None
    note: str | None = None


class InheritanceFile(BaseModel):
    model_config = ConfigDict(extra="allow")

    system: str
    inheritsFrom: str | None = None
    controls: dict[str, InheritanceEntry] = Field(default_factory=dict)


class Finding(BaseModel):
    id: str
    source: str
    severity: Severity
    title: str
    target: str
    controlHints: list[str] = Field(default_factory=list)


class InputRecord(BaseModel):
    path: str
    kind: str
    sha256: str
    bytes: int


class ResolvedControl(BaseModel):
    id: str
    title: str = ""
    family: str = ""
    status: ControlStatus
    provider: str | None = None
    note: str | None = None
    requiredEvidence: list[str] = Field(default_factory=list)
    evidenceFound: bool = False
    kindsPresent: list[str] = Field(default_factory=list)


class Artifact(BaseModel):
    source_path: Path
    kind: str
    sha256: str
    size: int
    parsed: bool = False
    warning: str | None = None
    component_names: list[str] = Field(default_factory=list)
    dest_relpath: str = ""
