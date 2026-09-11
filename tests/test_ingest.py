from onboard_pack.ingest import parse_artifact
from onboard_pack.ingest.cyclonedx import parse_cyclonedx
from onboard_pack.ingest.trivy import parse_trivy
from tests.conftest import APP_A


def test_parse_cyclonedx_fixture_component_names() -> None:
    result = parse_cyclonedx(APP_A / "sbom" / "sbom.json")
    assert result is not None
    assert result.parsed
    assert "app-a" in result.component_names
    assert "example-lib" in result.component_names
    assert "pkg" in result.component_names
    assert len(result.component_names) == 4


def test_parse_trivy_fixture_high_cve() -> None:
    result = parse_trivy(APP_A / "scans" / "trivy.json")
    assert result is not None
    assert result.parsed
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.id == "trivy:CVE-2024-1234:pkg"
    assert finding.source == "container-scan"
    assert finding.severity.value == "HIGH"
    assert finding.title == "CVE-2024-1234"
    assert finding.target == "pkg@1.2.3"
    assert finding.controlHints == ["RA-5", "SI-2", "CA-7"]


def test_parse_artifact_yaml_copy() -> None:
    result = parse_artifact(APP_A / "network" / "data-flow.yaml", "data-flow")
    assert result.parsed
    assert result.findings == []
