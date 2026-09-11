"""Typed failures mapped to CLI exit codes."""

from __future__ import annotations


class PackError(Exception):
    """Unexpected error; CLI exits 1."""


class GateError(Exception):
    """Evidence completeness (or overlay/inheritance) failure; CLI exits 2."""

    def __init__(self, message: str, failures: list[str] | None = None) -> None:
        super().__init__(message)
        self.failures: list[str] = failures if failures is not None else [message]
