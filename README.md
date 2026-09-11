# onboard-pack

CLI that compiles a DoW/DoD **application network-onboarding evidence pack** from CI artifacts (SBOM, container/IaC/SAST scans, STIG files, data-flow, PPSM) plus an overlay and inheritance file.

This repo is plane 3 of the system (the evidence compiler). The paved-road pipeline and policy pack are described in `docs/ARCHITECTURE.md`. v0.1 compiler behavior is in `docs/SPEC.md`. A copy-paste CI template lives in `examples/pipeline/`.

Gates measure **evidence completeness**, not residual risk or authorization.

## What this is

- A pipeline-native **evidence compiler**
- OSCAL-shaped JSON stubs + a human checklist + a zip an ISSM can attach
- Fail-the-build when owned/shared controls lack required evidence files

## What this is not

- eMASS
- A GRC / SSP author
- An authorizing official
- A scanner (it consumes scanner output)

## Feed this to Grok Build

See `docs/GROK_BUILD.md`. Short version:

```bash
cd onboard-pack
git init && git add . && git commit -m "chore: seed spec"
grok
```

Then paste:

```
Read @AGENTS.md and @docs/SPEC.md. Plan v0.1 only, then wait for approval.
```

Or:

```bash
grok --prompt-file prompts/01-bootstrap.md
```

## Layout of CI inputs

Put pipeline outputs in a conventional directory (see `examples/pipeline/`):

```
artifacts/sbom/sbom.json
artifacts/scans/trivy.json
artifacts/network/data-flow.yaml
artifacts/network/ppsm.yaml
artifacts/inheritance.yaml
```

## After it is built

```bash
pip install -e ".[dev]"
onboard pack \
  --input examples/fixtures/app-a \
  --overlay overlays/example.yaml \
  --inheritance examples/fixtures/app-a/inheritance.yaml \
  --out /tmp/onboard-out
onboard validate --pack /tmp/onboard-out
onboard zip --pack /tmp/onboard-out --out /tmp/onboard-pack.zip
```

## Roadmap (do not implement until v0.1 works)

1. Inheritance & reciprocity graph
2. Evidence locker + optional eMASS artifact POST via MITRE eMASSer/SAF
3. Program-specific overlays (real CNSSI / system baseline)
