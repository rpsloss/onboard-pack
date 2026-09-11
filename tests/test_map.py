from pathlib import Path

import pytest

from onboard_pack.errors import GateError
from onboard_pack.map import load_inheritance, load_overlay, resolve_controls
from tests.conftest import APP_A, OVERLAY


def test_overlay_loads_example_controls() -> None:
    overlay = load_overlay(OVERLAY)
    assert overlay.id == "example-app-overlay"
    assert [item.id for item in overlay.controls] == [
        "CM-8",
        "RA-5",
        "SI-2",
        "CM-2",
        "CM-6",
        "CA-7",
        "SA-15",
        "SR-3",
        "AC-4",
        "SC-7",
    ]


def test_inheritance_defaults_missing_keys_to_owned() -> None:
    overlay = load_overlay(OVERLAY)
    inheritance = load_inheritance(APP_A / "inheritance.yaml")
    resolved = {item.id: item for item in resolve_controls(overlay, inheritance)}
    assert resolved["CM-6"].status == "inherited"
    assert resolved["CA-7"].status == "shared"
    assert resolved["CM-2"].status == "na"
    assert resolved["SA-15"].status == "na"
    assert resolved["RA-5"].status == "owned"
    assert resolved["SI-2"].status == "owned"
    assert resolved["SR-3"].status == "owned"


def test_missing_overlay_is_gate_error(tmp_path: Path) -> None:
    with pytest.raises(GateError, match="missing"):
        load_overlay(tmp_path / "nope.yaml")
