Continue from the current repo. Re-read @AGENTS.md and @docs/SPEC.md.

Implement slice 2:

- Load overlay YAML and inheritance YAML.
- Resolve inheritance (missing controls default to owned).
- Ingest adapters for sbom (CycloneDX), container-scan (Trivy), data-flow, ppsm. Other kinds may be opaque copy + warning.
- Emit normalized findings with the static source→controlHints table from the spec.
- Unit tests using examples/fixtures/app-a.

Do not write the full pack directory yet.
pytest -q must pass.
