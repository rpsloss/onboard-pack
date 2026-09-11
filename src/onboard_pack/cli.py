"""Typer CLI for onboard-pack."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from onboard_pack.errors import GateError, PackError
from onboard_pack.pack import diff_packs, run_pack, validate_pack, zip_pack

app = typer.Typer(
    name="onboard",
    help="Compile a DoW/DoD application-onboarding evidence pack from CI artifacts.",
    no_args_is_help=True,
    add_completion=False,
)


def _emit_warnings(warnings: list[str]) -> None:
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)


@app.command()
def pack(
    input: Path = typer.Option(..., "--input", help="Directory of CI artifacts."),
    overlay: Path = typer.Option(..., "--overlay", help="Control overlay YAML."),
    inheritance: Path = typer.Option(..., "--inheritance", help="Inheritance YAML."),
    out: Path = typer.Option(..., "--out", help="Pack output directory (pack root)."),
    strict: bool = typer.Option(False, "--strict", help="Also fail on CRITICAL findings."),
) -> None:
    """Write an evidence pack directory from inputs + overlay + inheritance."""
    try:
        result = run_pack(input, overlay, inheritance, out, strict=strict)
    except GateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    except PackError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    _emit_warnings(result.warnings)
    if not result.gates_passed:
        typer.echo("gate failed:", err=True)
        for item in result.failures:
            typer.echo(f"- {item}", err=True)
        typer.echo(str(result.out_dir))
        raise typer.Exit(2)
    typer.echo(str(result.out_dir))


@app.command()
def validate(
    pack_dir: Path = typer.Option(..., "--pack", help="Existing pack directory."),
) -> None:
    """Re-check manifest schema and gate rules from a written pack."""
    try:
        failures = validate_pack(pack_dir)
    except PackError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    if failures:
        typer.echo("gate failed:", err=True)
        for item in failures:
            typer.echo(f"- {item}", err=True)
        raise typer.Exit(2)
    typer.echo("ok")


@app.command()
def diff(
    from_dir: Path = typer.Option(..., "--from", help="Previous pack directory."),
    to_dir: Path = typer.Option(..., "--to", help="Newer pack directory."),
    out: Optional[Path] = typer.Option(None, "--out", help="Optional Markdown output path."),
) -> None:
    """Print a Markdown diff of two packs."""
    try:
        markdown = diff_packs(from_dir, to_dir)
    except PackError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(markdown, nl=False)
    if not markdown.endswith("\n"):
        typer.echo("")
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown if markdown.endswith("\n") else markdown + "\n", encoding="utf-8")


@app.command()
def zip(
    pack_dir: Path = typer.Option(..., "--pack", help="Pack directory to archive."),
    out: Path = typer.Option(..., "--out", help="Zip file to write."),
) -> None:
    """Zip a pack directory."""
    try:
        written = zip_pack(pack_dir, out)
    except PackError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(str(written))


if __name__ == "__main__":
    app()
