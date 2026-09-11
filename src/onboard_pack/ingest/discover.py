"""Find evidence files under --input without following junk trees."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".eggs",
    "dist",
    "build",
}

# (kind, filename patterns) — first match wins.
_KIND_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("sbom", ("sbom*.json", "*cyclonedx*.json", "*spdx*.json")),
    ("container-scan", ("*trivy*.json", "*grype*.json", "container-scan.json")),
    ("iac-scan", ("*checkov*.json", "iac-scan.json")),
    ("sast", ("*semgrep*.json", "sast.json")),
    ("data-flow", ("data-flow.yaml", "data-flow.yml")),
    ("ppsm", ("ppsm.yaml", "ppsm.yml")),
    ("stig", ("*.ckl", "*.cklb")),
]

_STIG_XML_HINTS = ("xccdf", "oval", "scap", "openscap", "cpe-dictionary")


def discover(input_dir: Path, out_dir: Path | None = None) -> list[tuple[Path, str]]:
    """Return (absolute path, kind) for files that match ingest globs."""
    root = input_dir.resolve()
    out_resolved = out_dir.resolve() if out_dir is not None else None
    found: list[tuple[Path, str]] = []
    for path in _walk_files(root, out_resolved):
        kind = classify(path)
        if kind is not None:
            found.append((path, kind))
    found.sort(key=lambda item: (item[1], item[0].as_posix()))
    return found


def classify(path: Path) -> str | None:
    name = path.name.lower()
    for kind, patterns in _KIND_PATTERNS:
        if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
            return kind
    if name.endswith(".xml") and _xml_looks_like_stig(path):
        return "stig"
    return None


def _walk_files(root: Path, out_resolved: Path | None) -> list[Path]:
    files: list[Path] = []
    for current_str, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(current_str)
        resolved = current.resolve()
        if out_resolved is not None and _is_under(resolved, out_resolved):
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIR_NAMES and not name.startswith(".")
        ]
        if out_resolved is not None:
            dirnames[:] = [
                name
                for name in dirnames
                if (current / name).resolve() != out_resolved
            ]
        for filename in filenames:
            path = current / filename
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)
    return files


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _xml_looks_like_stig(path: Path) -> bool:
    name = path.name.lower()
    if any(hint in name for hint in _STIG_XML_HINTS):
        return True
    try:
        sample = path.read_bytes()[:4096].decode("utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(hint in sample for hint in _STIG_XML_HINTS)
