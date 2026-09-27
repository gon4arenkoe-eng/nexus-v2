# Phase 11 observer recovery — deploy / rollback runbook

Status: PLAN / NOT AUTHORIZED FOR PRODUCTION EXECUTION.

## Candidate identity

Source commit:

`b88e5d0fb8c60cf9373f7c2030cdc9f96a6b73dd`

Immutable image:

`ghcr.io/gon4arenkoe-eng/nexus-v2@sha256:5e23e1c051feee70497a5a692ae329a376e80a750eda667ab59b62410a53009f`

Runtime:

`python -m scripts.bingx_vst_observer_runtime`

Target container:

`nexus-v2-core`

Target port:

`127.0.0.1:18081 -> 8080`

Networks:

- `nexus-v2-foundation`
- `nexus-engine_default`

The second network exists only to reach the isolated PostgreSQL V2 database through
`nexus-postgres`. It does not grant new exchange write authority.

## Required runtime configuration

Secrets are never committed to Git.

Required external runtime values:

- `BINGX_VST_API_KEY`
- `BINGX_VST_SECRET_KEY`
- `NEXUS_RUNTIME_MODE`
- `NEXUS_V2_DATABASE_URL`
- `NEXUS_CONTROL_PLANE_USER_ID`
- `NEXUS_PORTFOLIO_RISK_LIMITS_JSON`
- `NEXUS_PORTFOLIO_RISK_STALE_SECONDS`
- `NEXUS_VST_EQUITY_ASSET`
- `NEXUS_OBSERVER_INTERVAL_SECONDS`

Portfolio Risk recording is fixed by the candidate manifest to:

`NEXUS_VST_PORTFOLIO_RISK_RECORDING=ENABLED`

Risk limits MUST come from approved runtime configuration. They are not hardcoded in
this repository or in the deploy manifest.

## Mandatory preconditions before any replacement

The following must be true before production execution of this runbook:

1. candidate manifest is committed and pushed;
2. CI is green;
3. immutable candidate digest is unchanged;
4. production `nexus_v2` backup exists;
5. production `nexus_v2` migration from `e9b1c7d3a246` to `f2c4e6a8b013`
   has separate explicit authorization;
6. current `nexus-v2-core` image identity is still
   `sha256:5d0e70d96179357fc6c1d9f67e7228f7e4a4fe66dcbd61dfecf3cb7af7abb354`;
7. current BingX VST observer credentials remain read-only observer credentials;
8. Restricted Live and Full Live remain disabled.

This document does NOT authorize those operations.

## Candidate verification after a future authorized replacement

Verify:

- container image digest is the candidate digest;
- process command is `scripts.bingx_vst_observer_runtime`;
- root filesystem is read-only;
- port remains bound only to `127.0.0.1:18081`;
- both required Docker networks are present;
- V2 DB Alembic revision is `f2c4e6a8b013`;
- observer reports no exchange writes;
- Portfolio Risk snapshot records use source `BINGX_VST_OBSERVER_REAL`;
- Portfolio Risk trading state remains `HALTED`;
- Control Plane reads the persisted snapshot;
- no Restricted Live / Full Live authority is enabled.

## Container rollback identity

Rollback image:

`ghcr.io/gon4arenkoe-eng/nexus-v2@sha256:5d0e70d96179357fc6c1d9f67e7228f7e4a4fe66dcbd61dfecf3cb7af7abb354`

Rollback runtime:

`python -m scripts.bingx_vst_observer_runtime`

Rollback network topology returns to the current proven state:

- `nexus-v2-foundation` only;
- no V2 PostgreSQL network attachment required by the old observer.

## Database rollback

Container rollback and database rollback are separate operations.

Do NOT automatically downgrade the V2 database merely because the container is rolled
back.

A database downgrade from `f2c4e6a8b013` to `e9b1c7d3a246` is destructive with respect
to the new `portfolio_risk_snapshots` table and therefore requires:

- backup preservation;
- separate explicit authorization;
- evidence capture before downgrade.

No database downgrade command is embedded in either compose manifest.

## Production authority

This recovery deployment does not expand trading authority.

- AI promotion: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED
- server source build: FORBIDDEN