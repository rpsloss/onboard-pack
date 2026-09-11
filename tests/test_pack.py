from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from onboard_pack.cli import app
from onboard_pack.manifest import validate_manifest_document
from tests.conftest import APP_A, MISSING_SBOM, OVERLAY

runner = CliRunner()


def _pack(input_dir: Path, out_dir: Path, strict: bool = False) -> tuple[int, str]:
    args = [
        "pack",
        "--input",
        str(input_dir),
        "--overlay",
        str(OVERLAY),
        "--inheritance",
        str(input_dir / "inheritance.yaml"),
        "--out",
        str(out_dir),
    ]
    if strict:
        args.append("--strict")
    result = runner.invoke(app, args)
    combined = f"{result.stdout}{result.stderr}"
    return result.exit_code, combined


def test_pack_app_a_exits_0(tmp_path: Path) -> None:
    out = tmp_path / "pack"
    code, _ = _pack(APP_A, out)
    assert code == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    validate_manifest_document(manifest)
    assert manifest["gates"]["passed"] is True
    assert manifest["overlayId"] == "example-app-overlay"
    assert manifest["counts"]["findings"]["HIGH"] == 1
    assert manifest["counts"]["controls"]["na"] == 2
    assert manifest["counts"]["controls"]["missing-evidence"] == 0
    findings = json.loads((out / "findings" / "normalized.json").read_text(encoding="utf-8"))
    assert findings[0]["id"] == "trivy:CVE-2024-1234:pkg"
    checklist = (out / "human" / "onboard-checklist.md").read_text(encoding="utf-8")
    assert "Gates measure evidence completeness" in checklist
    delta = (out / "human" / "delta-ssp.md").read_text(encoding="utf-8")
    assert "Not an SSP" in delta
    assert "MISSING:" not in delta


def test_pack_missing_sbom_exits_2(tmp_path: Path) -> None:
    out = tmp_path / "pack"
    code, output = _pack(MISSING_SBOM, out)
    assert code == 2
    assert "CM-8" in output
    assert "SR-3" in output
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["gates"]["passed"] is False
    assert manifest["counts"]["controls"]["missing-evidence"] >= 2
    delta = (out / "human" / "delta-ssp.md").read_text(encoding="utf-8")
    assert "MISSING: CM-8" in delta


def test_assessment_results_never_pass(tmp_path: Path) -> None:
    out = tmp_path / "pack"
    code, _ = _pack(APP_A, out)
    assert code == 0
    oscal = json.loads((out / "oscal" / "assessment-results.json").read_text(encoding="utf-8"))
    statuses = {item["status"] for item in oscal["results"]}
    assert "pass" not in statuses
    poam = json.loads((out / "oscal" / "poam.json").read_text(encoding="utf-8"))
    assert poam["items"] == []
    inherited = [item for item in oscal["results"] if item["controlId"] == "CM-6"][0]
    assert inherited["status"] == "other"
    assert inherited["remarks"] == "declared-inherited"


def test_validate_success_and_failure(tmp_path: Path) -> None:
    good = tmp_path / "good"
    bad = tmp_path / "bad"
    assert _pack(APP_A, good)[0] == 0
    assert _pack(MISSING_SBOM, bad)[0] == 2
    ok = runner.invoke(app, ["validate", "--pack", str(good)])
    assert ok.exit_code == 0
    failed = runner.invoke(app, ["validate", "--pack", str(bad)])
    assert failed.exit_code == 2


def test_zip_contains_manifest(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    zip_path = tmp_path / "onboard-pack.zip"
    assert _pack(APP_A, pack_dir)[0] == 0
    result = runner.invoke(app, ["zip", "--pack", str(pack_dir), "--out", str(zip_path)])
    assert result.exit_code == 0
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    assert "manifest.json" in names
    assert "findings/normalized.json" in names


def test_diff_detects_added_cve(tmp_path: Path) -> None:
    from_dir = tmp_path / "from"
    to_dir = tmp_path / "to"
    assert _pack(APP_A, from_dir)[0] == 0
    shutil.copytree(from_dir, to_dir)
    findings_path = to_dir / "findings" / "normalized.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    findings.append(
        {
            "id": "trivy:CVE-2024-9999:other",
            "source": "container-scan",
            "severity": "HIGH",
            "title": "CVE-2024-9999",
            "target": "other@0.0.1",
            "controlHints": ["RA-5", "SI-2", "CA-7"],
        }
    )
    findings_path.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    result = runner.invoke(
        app, ["diff", "--from", str(from_dir), "--to", str(to_dir)]
    )
    assert result.exit_code == 0
    assert "CVE-2024-9999" in result.stdout
    assert "trivy:CVE-2024-9999:other" in result.stdout


def test_strict_fails_on_critical(tmp_path: Path) -> None:
    src = tmp_path / "input"
    shutil.copytree(APP_A, src)
    trivy_path = src / "scans" / "trivy.json"
    data = json.loads(trivy_path.read_text(encoding="utf-8"))
    data["Results"][0]["Vulnerabilities"][0]["Severity"] = "CRITICAL"
    trivy_path.write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "pack"
    code, output = _pack(src, out, strict=True)
    assert code == 2
    assert "CRITICAL" in output
    code_ok, _ = _pack(src, tmp_path / "pack-nonstrict", strict=False)
    assert code_ok == 0


def test_validate_detects_tampered_digest(tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    assert _pack(APP_A, pack_dir)[0] == 0
    findings_path = pack_dir / "findings" / "normalized.json"
    findings_path.write_text(findings_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", "--pack", str(pack_dir)])
    assert result.exit_code == 1
    assert "artifactDigest" in f"{result.stdout}{result.stderr}"


def test_missing_overlay_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "pack",
            "--input",
            str(APP_A),
            "--overlay",
            str(tmp_path / "missing.yaml"),
            "--inheritance",
            str(APP_A / "inheritance.yaml"),
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 2
