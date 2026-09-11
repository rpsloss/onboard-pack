from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_A = ROOT / "examples" / "fixtures" / "app-a"
MISSING_SBOM = ROOT / "examples" / "fixtures" / "app-a-missing-sbom"
OVERLAY = ROOT / "overlays" / "example.yaml"


@pytest.fixture
def app_a() -> Path:
    return APP_A


@pytest.fixture
def missing_sbom() -> Path:
    return MISSING_SBOM


@pytest.fixture
def overlay() -> Path:
    return OVERLAY
