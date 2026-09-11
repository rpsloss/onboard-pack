from typer.testing import CliRunner

from onboard_pack.cli import app

runner = CliRunner()


def test_root_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    stdout = result.stdout
    assert "pack" in stdout
    assert "validate" in stdout
    assert "diff" in stdout
    assert "zip" in stdout


def test_pack_help() -> None:
    result = runner.invoke(app, ["pack", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.stdout
    assert "--overlay" in result.stdout
    assert "--inheritance" in result.stdout
    assert "--out" in result.stdout
