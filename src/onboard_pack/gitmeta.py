"""Optional git metadata for the pack source."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_metadata(path: Path) -> tuple[str | None, bool | None, str | None]:
    """Return (commit, dirty, warning). Warning is set when git is unavailable."""
    try:
        commit_proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None, None, "git metadata unavailable"
    if commit_proc.returncode != 0:
        return None, None, "git metadata unavailable"
    dirty_proc = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = bool(dirty_proc.stdout.strip()) if dirty_proc.returncode == 0 else None
    return commit_proc.stdout.strip() or None, dirty, None
