# NEXUS V2 Local Development Baseline

## Status

Phase 0 local development baseline.

This runbook defines the minimum reproducible development environment required before Phase 1 implementation begins.

## Principles

- Development happens off-production.
- `nexus-bot` remains a runtime/reference host only.
- No build, dependency installation, backtest, ML workload, or development activity is performed on production.
- Live trading authority remains disabled.
- No exchange credential is required for the Phase 0 development environment.
- Legacy source code is not copied wholesale into NEXUS V2.

## Python contract

NEXUS V2 Phase 0 pins the development baseline to Python 3.13.

Local verification:

```powershell
py -3 .\infra\github\repo_baseline_check.py
py -3 .\scripts\dev_check.py
```

Both checks must pass before a Phase 0 development-baseline change is committed.

## Dev container

Canonical configuration:

```text
.devcontainer/devcontainer.json
```

The dev container:

- uses a Python 3.13 development image;
- sets `NEXUS_ENV=development`;
- sets `NEXUS_LIVE_AUTHORITY=disabled`;
- does not mount Docker socket;
- does not include production SSH access;
- does not contain exchange credentials;
- runs the repository and local-development checks after creation.

The dev container is for development/Codespaces only. It is not the production runtime image.

## Repository configuration

Canonical files:

```text
pyproject.toml
.python-version
.devcontainer/devcontainer.json
scripts/dev_check.py
```

`pyproject.toml` is a Phase 0 metadata/runtime contract only. It does not yet define application dependencies.

Dependencies should be introduced only when required by the active Phase and reviewed against `docs/architecture/DEPENDENCY_BOUNDARIES.md`.

## Public repository safety

Never commit:

- `.env`;
- exchange API keys/secrets;
- private keys;
- production credentials;
- database dumps;
- secret-bearing logs/backups;
- local research datasets/models unless explicitly approved and sanitized.

## Verification

Required Phase 0 checks:

```powershell
py -3 .\infra\github\repo_baseline_check.py
py -3 .\scripts\dev_check.py
git diff --check
```

GitHub Actions must also pass before the local-development baseline is marked TEST VERIFIED.

## Production safety

This baseline does not grant:

- production build authority;
- production deployment authority;
- Restricted Live;
- Full Live;
- AI direct exchange access.

All remain disabled until their explicit future gates.
