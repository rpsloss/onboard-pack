"""Typer CLI for onboard-pack."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="onboard",
    help="Compile a DoW/DoD application-onboarding evidence pack from CI artifacts.",
    no_args_is_help=True,
    add_completion=False,
)


def _not_implemented() -> None:
    typer.echo("not implemented", err=True)
    raise typer.Exit(1)


@app.command()
def pack(
    input: Path = typer.Option(..., "--input", help="Directory of CI artifacts."),
    overlay: Path = typer.Option(..., "--overlay", help="Control overlay YAML."),
    inheritance: Path = typer.Option(..., "--inheritance", help="Inheritance YAML."),
    out: Path = typer.Option(..., "--out", help="Pack output directory (pack root)."),
    strict: bool = typer.Option(False, "--strict", help="Also fail on CRITICAL findings."),
) -> None:
    """Write an evidence pack directory from inputs + overlay + inheritance."""
    _ = (input, overlay, inheritance, out, strict)
    _not_implemented()


@app.command()
def validate(
    pack_dir: Path = typer.Option(..., "--pack", help="Existing pack directory."),
) -> None:
    """Re-check manifest schema and gate rules from a written pack."""
    _ = pack_dir
    _not_implemented()


@app.command()
def diff(
    from_dir: Path = typer.Option(..., "--from", help="Previous pack directory."),
    to_dir: Path = typer.Option(..., "--to", help="Newer pack directory."),
    out: Optional[Path] = typer.Option(None, "--out", help="Optional Markdown output path."),
) -> None:
    """Print a Markdown diff of two packs."""
    _ = (from_dir, to_dir, out)
    _not_implemented()


@app.command()
def zip(
    pack_dir: Path = typer.Option(..., "--pack", help="Pack directory to archive."),
    out: Path = typer.Option(..., "--out", help="Zip file to write."),
) -> None:
    """Zip a pack directory."""
    _ = (pack_dir, out)
    _not_implemented()


if __name__ == "__main__":
    app()
