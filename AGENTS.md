# Onboard Pack Compiler

You are building **onboard-pack**, a CLI that compiles DoW/DoD application-onboarding evidence from CI artifacts.

Read `docs/SPEC.md` before writing code. Implement **v0.1 only**. Do not build the inheritance graph product or the evidence locker unless the user explicitly expands scope.

## Product constraints

- Evidence is a build artifact. Every successful `pack` run writes a pack directory at `--out`. Zip is a separate `onboard zip` command.
- Gates measure evidence completeness, not residual risk or authorization. Do not claim ATO.
- OSCAL-shaped JSON first; human PDF/Markdown second; eMASS upload is a later optional flag (stub only in v0.1).
- No SaaS phone-home. No cloud APIs required for the happy path.
- Do not invent NIST control text. Map findings to control IDs from `overlays/` YAML only.
- Read `docs/ARCHITECTURE.md`. Implement plane 3 (compiler) only unless the user expands scope.

## Stack

- Language: Python 3.11+
- Packaging: `pyproject.toml` with a console script `onboard`
- CLI: Typer
- Tests: pytest
- Rendering: Jinja2 for Markdown; weasyprint or reportlab only if PDF is easy; otherwise Markdown + note that PDF is v0.2
- Schema: JSON Schema draft 2020-12 in `schemas/`
- No Django/Flask. No GUI.

## Layout

```
src/onboard_pack/
  __init__.py
  cli.py
  pack.py
  manifest.py
  ingest/
  map/
  render/
  models.py
overlays/
schemas/
examples/fixtures/
tests/
docs/
```

## Commands to implement in v0.1

- `onboard pack --input DIR --overlay FILE --inheritance FILE --out DIR`
- `onboard diff --from DIR --to DIR`
- `onboard validate --pack DIR`
- `onboard zip --pack DIR --out FILE`

Exit 0 on success. Exit 2 if required evidence is missing (see SPEC gate rules). Exit 1 on unexpected errors.

## Engineering rules

- Type hints on public functions.
- No bare `except`. Fail with a clear message and exit code.
- Golden tests against `examples/fixtures/`.
- Do not commit secrets, CAC certs, or real scan data from a live system.
- Conventional commits.
- Keep modules small. Ingest adapters are one file per tool format.

## Verification

```
python -m pip install -e ".[dev]"
pytest -q
onboard pack --input examples/fixtures/app-a --overlay overlays/example.yaml --inheritance examples/fixtures/app-a/inheritance.yaml --out /tmp/onboard-out
onboard validate --pack /tmp/onboard-out
```

Stop and ask if the spec is ambiguous rather than inventing program-specific RMF policy.
