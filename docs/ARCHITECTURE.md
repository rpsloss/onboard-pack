# Architecture — three planes

Green pipeline ≠ authorized system. Green pack ≠ residual risk accepted.
The pack answers: for this git commit and this image digest, which required
evidence existed, which controls are declared inherited, which gates fired,
which waivers are in force. The authorizing official answers everything else.

```
paved road (CI)  →  policy / gates  →  evidence compiler (this repo)
     artifacts/          pass/fail           onboard-pack/
```

## 1. Paved road

Reusable pipeline that *implements* technical controls and writes a
conventional artifact directory. It runs scanners; `onboard` does not.

```
artifacts/
  sbom/            CycloneDX (Syft/cdxgen) + optional attestation
  scans/           trivy.json, semgrep.json, checkov.json, gitleaks.json
  tests/           junit, coverage
  provenance/      slsa.json, cosign bundle
  network/         data-flow.yaml, ppsm.yaml
  waivers/         exceptions with expiry + POA&M id
  inheritance.yaml
```

Suggested stages: PR (secrets, SAST, tests) → merge (SBOM, Trivy, IaC, sign) →
release/promote (strict policy, network files, pack digest on the change).
Runtime re-scan and CSSP logging are ConMon (CA-7), not a CI-only story.

See `examples/pipeline/` for a copy-paste GitHub Actions template.

## 2. Policy / gates

Policy-as-code in front of promote, not `trivy --exit-code 1`. Each rule has a
stable ID, overlay control mapping, artifact kind, and fail/warn/waiver
behavior. Inherited and `na` controls do not demand app evidence. Owned and
shared controls do.

v0.1 implements **presence gates only** (required evidence files exist).
`--strict` additionally fails on CRITICAL normalized findings. KEV, SLAs,
cosign, and waiver expiry are later policy-pack work. Waivers are the only
honest POA&M feed; do not auto-open a POA&M per CVE.

## 3. Evidence compiler (`onboard`)

Local CLI. Consumes `--input` + overlay + inheritance. Emits a pack directory
at `--out`. `onboard zip` is a separate command. No eMASS client, no GUI, no
live scanner, no AI SSP.

Same engine, different overlay YAML per program (example DoD app overlay,
later CMMC L1/L2). Inheritance is a **declared** claim in v0.1, not a verified
provider package.

## Rules that do not move

- Overlay and inheritance are data. Do not invent NIST control text in code.
- `controlHints` on findings are annotations. Gates key off `requiredEvidence`.
- OSCAL JSON is stub-shaped and must not report `pass` because a file showed up.
- Do not merge these planes into a GRC.
