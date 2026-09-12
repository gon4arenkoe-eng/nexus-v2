# NEXUS V2 digest-pinned deployment and rollback foundation

## Scope

This runbook defines the Phase 12 deployment identity and rollback contract. It does **not** authorize a production cutover. Production cutover remains Phase 16 and requires separate explicit authorization.

## Immutable release identity

Every candidate must use the exact GHCR repository and an `image@sha256:<64-hex>` reference. A mutable tag (`latest`, release tag, branch tag, or commit tag without a digest) is not sufficient deployment evidence.

The required evidence record binds:

- source commit;
- immutable image digest;
- SBOM attestation;
- provenance attestation;
- Alembic head;
- pre-cutover backup reference and SHA-256;
- previous verified digest;
- timestamp and authorization state.

## Pre-cutover validation

1. Confirm the source commit has passed the required CI gates.
2. Confirm the release image exists in GHCR and the digest matches release evidence.
3. Confirm SBOM and provenance evidence are attached to that release image.
4. Validate the image reference with `scripts/validate_deploy_ref.py`.
5. Render/validate the Compose contract with `docker compose config`; do not add a `build:` section.
6. Pull and run only the `release-validation` profile before any controlled cutover decision.
7. Confirm current Alembic head and migration compatibility.
8. Confirm the pre-cutover backup evidence exists.
9. Confirm reconciliation/startup safety remains fail-closed.

## Rollback contract

Rollback means selecting the **previous verified digest**, not rebuilding old source and not moving a mutable tag backwards.

Before rollback:

1. identify the previous verified digest and its source commit;
2. verify its release evidence/SBOM/provenance;
3. verify database schema compatibility with that image;
4. stop if rollback would require an unapproved destructive DB restore or migration reversal;
5. retain the current failed-candidate digest and evidence for incident analysis;
6. require reconciliation before strategy execution after restart.

A rollback candidate is expressed as the previous `image@sha256:<digest>` and is validated by the same manifest/policy checks as a forward candidate.

## Production safety

- **NO BUILD ON PRODUCTION**.
- No source compilation, `docker build`, heavy backtest, ML sweep, or dataset preparation on `nexus-bot`.
- This Phase 12 foundation contains no SSH/SCP/remote deployment automation.
- Phase 16 remains the only controlled production cutover phase and requires explicit authorization.
- AI direct exchange access remains blocked.
