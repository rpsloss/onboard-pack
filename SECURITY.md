# Security policy

onboard-pack compiles **unclassified** onboarding evidence stubs from CI artifacts you supply. It does not scan systems and is not eMASS.

- Do not commit real SBOMs, STIG results, PPSM files, or customer overlays.
- Examples in this repo are fixtures. Treat `artifacts/` from a live pipeline as sensitive.
- Do not put secrets, private keys, or CUI in notes fields or zip contents.

## Reporting

Open a GitHub issue on [rpsloss/onboard-pack](https://github.com/rpsloss/onboard-pack) for defects in the compiler itself.

Do **not** attach live pipeline output or secrets to issues.
