# NEXUS V2 Phase 12 — Release Pipeline Foundation Benchmark

## Decision

NEXUS V2 uses GitHub Actions as the off-production release builder and GHCR as
the first canonical container registry target. A release image is valid only
after source verification succeeds and the registry returns a `sha256:` digest.

## Mature references reviewed

- GitHub Actions / GitHub Container Registry publishing guidance.
- Docker Buildx and Build Push GitHub Actions.
- GitHub artifact attestation guidance for container digests.

## Adopted patterns

1. CI verification is a hard dependency of image publishing.
2. The build occurs on GitHub-hosted CI, never on the production runtime host.
3. GHCR authentication uses the workflow `GITHUB_TOKEN` with least-privilege
   `packages: write` only on the publishing job.
4. Release identity includes full Git commit identity and the registry digest.
5. The runtime image uses a digest-pinned Python base and a non-root user.
6. Deployment is deliberately absent from the foundation workflow.

## Deferred to next Phase 12 slices

- SBOM generation/attachment;
- artifact/container provenance attestation;
- production compose/deploy manifest pinned by digest;
- backup/restore drill integration;
- rollback-by-digest runbook and verification;
- dependency update automation and broader release security scanning.

## Gate impact

This slice does **not** close `NEXUS_V2_RELEASE_PIPELINE_OK`. It establishes the
first required dependency: verified CI-only image build/publish with immutable
digest evidence.
