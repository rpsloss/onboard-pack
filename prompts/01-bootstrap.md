Read @AGENTS.md and @docs/SPEC.md.

Implement slice 1 of onboard-pack v0.1 only:

1. Create `pyproject.toml` with project name `onboard-pack`, python >=3.11, scripts.entry `onboard = onboard_pack.cli:app`, deps: typer, pydantic, pyyaml, jinja2, jsonschema. Dev extras: pytest.
2. Create package layout under `src/onboard_pack/` with a Typer app that has pack, validate, diff, zip commands. Commands may be stubs that print "not implemented" and exit 1 except a `--help` that works.
3. Write `overlays/example.yaml` exactly as specified in docs/SPEC.md.
4. Write `examples/fixtures/app-a/` with:
   - small CycloneDX 1.5 JSON SBOM (3 components)
   - small Trivy JSON with one HIGH vulnerability
   - `data-flow.yaml` (2 flows)
   - `ppsm.yaml` (2 ports)
   - conventional layout: `sbom/sbom.json`, `scans/trivy.json`, `network/data-flow.yaml`, `network/ppsm.yaml`
   - `inheritance.yaml` as in the spec (CM-6 inherited, CA-7 shared, CM-2 na, SA-15 na, remaining owned)
5. Write `examples/fixtures/app-a-missing-sbom/` as a copy without the SBOM.
6. Add `tests/test_cli_help.py` that runs `--help` successfully.
7. Add a short root README usage section only if missing.

Do not implement ingest or pack logic yet.
Do not add a web server or eMASS client.
Run `pytest -q` before you stop and report what is left for slice 2.
