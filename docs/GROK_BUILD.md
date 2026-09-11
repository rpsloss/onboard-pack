# Feeding this repo to Grok Build

Grok Build (`grok`) loads `AGENTS.md` automatically from the repo root. Put the spec in `docs/` and point at it with `@`. Do not paste the entire spec into the TUI every session.

## One-time setup

```bash
# macOS / Linux
curl -fsSL https://x.ai/cli/install.sh | bash
grok --version

mkdir -p ~/src && cd ~/src
# copy this onboard-pack folder here, then:
cd onboard-pack
git init
git add AGENTS.md docs schemas prompts examples
git commit -m "chore: seed onboard-pack spec for grok build"
```

`git init` matters: Grok only walks repo-root → cwd for `AGENTS.md` when you are inside a git repo.

Confirm discovery:

```bash
cd onboard-pack
grok inspect
```

You should see `AGENTS.md` listed.

## Best way: interactive plan mode (recommended)

```bash
cd onboard-pack
grok
```

First message (copy-paste):

```
Read @AGENTS.md and @docs/SPEC.md.

Work in plan mode. Propose the v0.1 implementation plan only.
Do not write code until I approve.

Scope: Onboard Pack Compiler v0.1. No eMASS client, no GUI, no inheritance-graph product.
```

Approve or edit the plan, then let it implement. After the first session:

```
Continue v0.1 from @docs/SPEC.md. Run pytest before you stop.
```

Resume later from the same directory:

```bash
grok -c
```

## Headless / scripted kickoff

Use a prompt file so the TUI is optional:

```bash
cd onboard-pack
grok --prompt-file prompts/01-bootstrap.md
```

Or one-shot:

```bash
grok -p "Implement v0.1 per @docs/SPEC.md and @AGENTS.md. Stop after pytest passes."
```

`--prompt-file` is better than a giant `-p` string. Keep session-specific instructions in `prompts/`, not in `AGENTS.md`.

## What to put where

| File | Loaded automatically? | Role |
|---|---|---|
| `AGENTS.md` | Yes, every session | Short rules, stack, layout, definition of done |
| `docs/SPEC.md` | No — `@` it | Product behavior, schemas, gates |
| `docs/GROK_BUILD.md` | No | Human instructions for you |
| `prompts/*.md` | No — `--prompt-file` or `@` | One task per file |
| `schemas/` | Only if `@` or the agent opens them | Machine contract |

Keep `AGENTS.md` short. Long policy belongs in `SPEC.md`. Grok follows short, specific rules more reliably.

## Session slicing (do not one-shot the whole product)

Use a new prompt per slice. That keeps diffs reviewable.

1. `prompts/01-bootstrap.md` — package + CLI stubs + fixtures
2. `prompts/02-ingest.md` — parsers + normalized findings
3. `prompts/03-pack.md` — pack writer, gates, manifest
4. `prompts/04-render.md` — checklist, OSCAL stubs, diff/zip/validate
5. `prompts/05-tests.md` — fill coverage, fix fixtures

After each slice: glance at the diff, run `pytest -q`, commit, then start the next prompt (`grok -c` or a new session).

## Plan mode vs yolo

- Complex / first session: default plan mode. Review the file list.
- Mechanical follow-ups after the layout exists: `grok -c` is enough.
- Avoid `--always-approve` / `--yolo` until tests exist.

## If it drifts

```
Stop. Re-read @AGENTS.md and @docs/SPEC.md.
You are only implementing v0.1 commands: pack, validate, diff, zip.
Delete any GUI, HTTP client, or extra subcommand you added.
```
