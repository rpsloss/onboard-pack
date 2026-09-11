Continue from the current repo. Re-read @AGENTS.md and @docs/SPEC.md.

Implement slice 3:

- `onboard pack` writes the pack tree and manifest.json
- Gate rules and exit codes 0 / 2
- Copy raw matched inputs into scans/sbom/stig/network
- Write inheritance.json resolved view
- Write findings/normalized.json
- `onboard validate` checks written pack
- Tests: app-a exits 0; app-a-missing-sbom exits 2

pytest -q must pass.
