# NEXUS V2 Phase 12 — Digest-Pinned Deployment & Rollback Benchmark

## Decision

NEXUS production release identity is an immutable GHCR image reference pinned as `image@sha256:<digest>`. Tags remain discoverability metadata only and are not sufficient deployment identity.

## Mature references reviewed

### Docker Compose

Docker Compose accepts image references with an OCI digest (`image: repository@sha256:...`). `docker compose config` can render and validate the effective configuration and can resolve/lock image digests.

### Docker image digests

Docker documents SHA-256 image digests as immutable identifiers and recommends digest pulls when an exact image version must be guaranteed across environments.

### Immutable infrastructure

The deployment model replaces artifacts rather than patching production containers in place. Release updates therefore continue to flow through CI rather than being built or modified on `nexus-bot`.

## NEXUS-specific constraints

1. `NO BUILD ON PRODUCTION` is non-negotiable.
2. A forward candidate and a rollback candidate use the same digest validation policy.
3. Rollback selects a previous verified digest; it does not rebuild previous source.
4. DB compatibility is checked before rollback; destructive DB restore is never automatic.
5. Reconciliation remains required after restart before strategy execution.
6. Phase 12 defines the deploy/rollback contract but does not authorize Phase 16 cutover.
7. Phase 15 remains responsible for the production backup/restore drill.
