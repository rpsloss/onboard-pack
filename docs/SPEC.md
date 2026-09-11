# Onboard Pack Compiler — v0.1 Spec

Read `docs/ARCHITECTURE.md` first. This spec is plane 3 (the compiler) only.

## Problem

DoW application onboarding to a network still collects evidence by hand: scan files, SBOMs, STIG results, data-flow notes, and inheritance statements live in different places. CSRMC names this the **Onboard** phase. This tool compiles a repeatable evidence pack from pipeline artifacts so an ISSM reviews a package instead of assembling one.

This is not a GRC, not eMASS, and not an authorizing system. A successful pack means **required evidence was present**, not that residual risk is accepted.

## Goals (v0.1)

1. Ingest common CI security artifacts from a directory.
2. Normalize them into an internal finding model.
3. Apply a control overlay + inheritance file.
4. Emit a pack directory (manifest, normalized findings, OSCAL-shaped JSON stubs, human checklist).
5. Diff two packs.
6. Fail the run if required evidence files are missing.

## Non-goals (v0.1)

- eMASS API POST (checklist instructions only; no HTTP client)
- Full NIST OSCAL profile resolution
- Live scanner execution (Trivy, Nessus, etc.)
- GUI / dashboard
- Inheritance graph product
- Evidence locker / hash chain
- Screenshot collection
- AI-written SSP narratives
- Policy pack beyond presence gates and optional `--strict` (KEV, SLAs, cosign, waiver expiry are later)

## Users

- App team: runs `onboard pack` in CI after scans.
- ISSM/ISSO: opens `human/onboard-checklist.md` and the zip.
- Connection reviewer: reads the control-status file + network files.

## Pack layout

`--out` **is** the pack root. Version lives in `manifest.generatedAt` and `toolVersion`. Do not wrap an extra `v1/` directory.

```
<out>/
  manifest.json
  oscal/
    component-definition.json
    assessment-results.json
    poam.json
  findings/
    normalized.json
  scans/                 # copies of raw scan inputs
  sbom/
  stig/
  network/
    data-flow.yaml       # copied from input if present
    ppsm.yaml            # copied from input if present
  inheritance.json       # resolved view
  human/
    onboard-checklist.md
    delta-ssp.md         # control-status cheat sheet, not an SSP
```

`pack` writes this tree only. `onboard zip --pack DIR --out FILE` produces a zip of that tree. Pack does not zip unless `zip` is invoked.

## manifest.json

Required fields (must match `schemas/pack.manifest.schema.json`):

| Field | Type | Notes |
|---|---|---|
| schemaVersion | string | `0.1.0` |
| generatedAt | string | UTC ISO-8601 |
| toolVersion | string | package version |
| source | object | `inputDir`, optional `gitCommit`, `gitDirty` |
| overlayId | string | from overlay file |
| overlayPath | string | |
| inheritancePath | string | |
| artifactDigest | string | 64-char lowercase hex; see below |
| inputs | array | `{path, kind, sha256, bytes}` for each ingested file |
| counts | object | findings by severity; controls by status |
| gates | object | `{passed: bool, failures: [string]}` |

### artifactDigest

1. List every file under the pack root except `manifest.json`.
2. Sort relative paths as POSIX (`/`), UTF-8, bytewise.
3. For each path, write one UTF-8 line: `{relativePath}\t{sha256hex(file bytes)}\n`.
4. `artifactDigest` is SHA-256 (lowercase hex) of that byte string.
5. Write `manifest.json` **after** the digest is computed so the manifest is not part of its own hash.

Do not hash a zip. Zip metadata is not stable across tools.

### counts

```json
{
  "findings": {
    "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0, "UNKNOWN": 0
  },
  "controls": {
    "inherited": 0, "owned": 0, "shared": 0, "na": 0, "missing-evidence": 0
  }
}
```

`missing-evidence` counts overlay controls whose status is `owned` or `shared` and whose `requiredEvidence` kinds were not found.

## Overlay file (`overlays/*.yaml`)

```yaml
id: example-app-overlay
title: Example application overlay
version: "0.1"
controls:
  - id: CM-8
    title: System Component Inventory
    family: CM
    requiredEvidence: [sbom]
  - id: RA-5
    title: Vulnerability Monitoring and Scanning
    family: RA
    requiredEvidence: [container-scan]
  - id: SI-2
    title: Flaw Remediation
    family: SI
    requiredEvidence: [container-scan]
  - id: CM-2
    title: Baseline Configuration
    family: CM
    requiredEvidence: [iac-scan]
  - id: CM-6
    title: Configuration Settings
    family: CM
    requiredEvidence: [stig]
  - id: CA-7
    title: Continuous Monitoring
    family: CA
    requiredEvidence: [container-scan]
  - id: SA-15
    title: Development Process, Standards, and Tools
    family: SA
    requiredEvidence: [sast]
  - id: SR-3
    title: Supply Chain Controls
    family: SR
    requiredEvidence: [sbom]
  - id: AC-4
    title: Information Flow Enforcement
    family: AC
    requiredEvidence: [data-flow]
  - id: SC-7
    title: Boundary Protection
    family: SC
    requiredEvidence: [ppsm]
```

Keep the example overlay small. Programs replace this file. Titles here are labels only; do not invent additional NIST control text.

## Inheritance file

```yaml
system: app-a
inheritsFrom: example-enclave
controls:
  CM-6:
    status: inherited
    provider: example-enclave
    note: Host STIG inherited from enclave gold image
  CA-7:
    status: shared
    provider: example-cssp
    note: CSSP ConMon plus app pipeline scans
  CM-2:
    status: na
    note: Example app has no IaC in v0.1 fixtures
  SA-15:
    status: na
    note: Example app has no SAST fixture; not in scope
  AC-4:
    status: owned
  SC-7:
    status: owned
  CM-8:
    status: owned
```

Statuses: `inherited` | `owned` | `shared` | `na`.

Resolved `inheritance.json` must include every overlay control. Missing keys default to `owned`. Inheritance in v0.1 is a **declared** claim, not a verified provider package. The checklist must say declared.

`inherited` and `na` do not require app evidence files. `owned` and `shared` do (shared CA-7 still needs the app container scan).

## Ingest kinds

Prefer a conventional input layout when present (`sbom/`, `scans/`, `stig/`, `network/` under `--input`). Globs below are the fallback so messy CI directories still work.

Never recurse into `node_modules`, `.git`, `__pycache__`, `.venv`, or the `--out` directory.

| Kind | Default globs | Parser |
|---|---|---|
| sbom | `**/sbom*.json`, `**/*cyclonedx*.json`, `**/*spdx*.json` | CycloneDX JSON (primary) or SPDX JSON; record component count + name |
| container-scan | `**/*trivy*.json`, `**/*grype*.json`, `**/container-scan.json` | Trivy JSON SchemaVersion 2 (primary); Grype JSON opaque+warn in v0.1 if not parsed |
| iac-scan | `**/*checkov*.json`, `**/iac-scan.json` | Checkov JSON if present; else treat file as opaque + warn |
| sast | `**/*semgrep*.json`, `**/sast.json` | Semgrep JSON if present; else opaque + warn |
| stig | `**/*.xml` with OpenSCAP/XCCDF hints, `**/*.ckl`, `**/*.cklb` | Best-effort: if not parsed, record as opaque artifact with kind=stig |
| data-flow | `**/data-flow.yaml`, `**/data-flow.yml` | Copy through |
| ppsm | `**/ppsm.yaml`, `**/ppsm.yml` | Copy through |

Unknown files are ignored unless they match a glob.

If a format cannot be fully parsed, still hash-copy it into the pack and emit a warning. Do not crash.

If multiple files match one kind: ingest all, hash all, union findings, emit a warning. Do not fail the gate for multiplicity.

v0.1 parsers that must actually parse: CycloneDX JSON, Trivy JSON. Everything else may be opaque copy + warning.

### Normalized finding

```json
{
  "id": "trivy:CVE-2024-1234:pkg",
  "source": "container-scan",
  "severity": "HIGH",
  "title": "CVE-2024-1234",
  "target": "pkg@1.2.3",
  "controlHints": ["RA-5", "SI-2"]
}
```

Severity enum: `CRITICAL` | `HIGH` | `MEDIUM` | `LOW` | `INFO` | `UNKNOWN`.

`controlHints` come from a static source→control table in code (not LLM):

- sbom → CM-8, SR-3
- container-scan → RA-5, SI-2, CA-7
- iac-scan → CM-2
- sast → SA-15
- stig → CM-6
- data-flow → AC-4
- ppsm → SC-7

Hints annotate findings. Gates key off overlay `requiredEvidence`, not hints. A HIGH CVE does not fail RA-5 in v0.1 (presence gate). `--strict` is the only finding-severity fail.

## Gate rules

`pack` exits 2 if any of these fail:

1. Overlay file missing or invalid.
2. Inheritance file missing or invalid.
3. A control with `status` in `{owned, shared}` has a `requiredEvidence` kind that was not found in inputs.
4. `inherited` and `na` controls do not require app evidence files.

v0.1 gates are **evidence completeness**, not security posture. An empty-but-present SBOM satisfies CM-8. A HIGH CVE does not fail the pack. The checklist header must say this.

Warnings (do not fail):

- Unparsed but present artifact.
- Findings with UNKNOWN severity.
- Git metadata unavailable.
- Multiple files of the same kind.

`--strict` (optional flag): also fail if any CRITICAL normalized finding exists.

Exit 0 on success. Exit 2 on gate failure. Exit 1 on unexpected errors (IO, parse crash that is not an opaque-copy path, invalid CLI).

## OSCAL-shaped outputs (stubs, valid-enough JSON)

Do **not** implement a full OSCAL library in v0.1. Emit simplified documents that are clearly marked:

```json
{
  "oscalVersion": "1.1.2",
  "disclaimer": "Simplified onboard-pack export; not a complete OSCAL document. Results are evidence-presence, not control assessment.",
  ...
}
```

- `component-definition.json`: system title from inheritance.system; list of components from SBOM names (cap at 50) plus the application itself.
- `assessment-results.json`: one result per overlay control.
  - `fail` if status is `owned` or `shared` and required evidence is missing.
  - `other` in every other case (inherited, na, or evidence present).
  - **Never `pass`.** Evidence present is not a control assessment. Put a `remarks` string on each result (`declared-inherited`, `na`, `evidence-present`, `evidence-missing`).
- `poam.json`: waiver/accepted items only. v0.1 has no waiver ingest, so `items` is an empty array. CRITICAL/HIGH findings stay in `findings/normalized.json`. Do not auto-open a POA&M per CVE.

## Human outputs

### onboard-checklist.md

Sections:

1. Header: system, overlay, generatedAt, commit. One line: `Gates measure evidence completeness, not residual risk or authorization.`
2. Gate result (`passed` / failures)
3. Control table: ID, status (declared), evidence found (yes/no/n-a), finding counts
4. Top findings (max 25): severity, title, target
5. Network files present or missing
6. How to zip / attach to eMASS (plain instructions, no API)

### delta-ssp.md

Control-status cheat sheet, **not** a delta SSP. First line: `Control status from overlay + inheritance + evidence presence. Not an SSP.`

Short control-by-control bullets:

- Inherited: one line naming provider (declared)
- Shared: provider + evidence kinds
- Owned: one line naming evidence file kinds used
- NA: one line
- Missing: prefixed `MISSING:`

If `onboard diff` is used, append a "Changes since previous pack" section listing added/removed findings and gate flips.

## CLI details

```
onboard pack --input PATH --overlay PATH --inheritance PATH --out PATH [--strict]
onboard validate --pack PATH
onboard diff --from PATH --to PATH
onboard zip --pack PATH --out FILE
```

`validate` re-checks schema of `manifest.json` and gate rules from the written pack.

`diff` prints Markdown to stdout and can write `human/delta.md` if `--out` is given.

## Fixtures

Use **real** CycloneDX 1.5 JSON and **real** Trivy `SchemaVersion` 2 JSON, not lookalikes. Layout:

```
examples/fixtures/app-a/
  sbom/sbom.json
  scans/trivy.json
  network/data-flow.yaml
  network/ppsm.yaml
  inheritance.yaml
```

- CycloneDX 1.5 SBOM (3 components)
- Trivy JSON with one HIGH CVE
- data-flow.yaml (2 flows) and ppsm.yaml (2 ports)
- inheritance.yaml as in this spec: CM-6 inherited, CA-7 shared, CM-2 `na`, SA-15 `na`, remaining overlay controls owned (by explicit keys or default)
- no STIG and no SAST files (covered by inherited / na)

Happy path must exit 0 against the example overlay. That is why CM-2 and SA-15 are `na` in the fixture, not because those controls are optional in a real program.

- `app-a`: complete owned/shared evidence + inherited/na as above → pack exits 0
- `app-a-missing-sbom`: same tree without `sbom/` → pack exits 2 (CM-8 and SR-3 owned, sbom missing)

## Tests

Minimum:

- parse CycloneDX and Trivy fixtures
- resolve inheritance defaults (missing overlay control → owned)
- CM-2 and SA-15 `na` do not fail app-a
- pack success / missing-evidence failure
- manifest schema validates, including `artifactDigest`
- zip contains manifest.json
- diff detects added CVE
- assessment-results contain no `"pass"` status

## Implementation order for Grok Build

1. pyproject.toml, package layout, empty CLI
2. schemas + Pydantic (or dataclasses + jsonschema) models
3. overlay + inheritance loaders
4. ingest adapters + normalized findings
5. pack writer + gates
6. human renderers
7. oscal stubs
8. diff / validate / zip
9. fixtures + pytest
10. README usage

Do not start a web app. Do not add eMASS HTTP clients in v0.1.
