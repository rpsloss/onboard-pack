# Paved-road pipeline template

Copy `github-actions.yaml` into an application repo as
`.github/workflows/onboard.yml`. This is plane 1 (paved road). It **runs**
scanners and writes `artifacts/`; `onboard pack` (plane 3) only consumes that
directory.

This template does not authorize a system. A green job means evidence was
produced and presence gates passed.

## Expected output layout

```
artifacts/
  sbom/sbom.json
  scans/trivy.json
  network/data-flow.yaml
  network/ppsm.yaml
  inheritance.yaml
```

Point `--overlay` at a program overlay (start from `overlays/example.yaml`).
Point `--inheritance` at the app's declared inheritance file.

## Local dry run (this repo)

```bash
pip install -e ".[dev]"
# after slice 3 implements pack:
onboard pack \
  --input examples/fixtures/app-a \
  --overlay overlays/example.yaml \
  --inheritance examples/fixtures/app-a/inheritance.yaml \
  --out ./pack-out
onboard zip --pack ./pack-out --out ./onboard-pack.zip
```

Replace the fixture input with `artifacts/` once Syft/Trivy run in CI.
