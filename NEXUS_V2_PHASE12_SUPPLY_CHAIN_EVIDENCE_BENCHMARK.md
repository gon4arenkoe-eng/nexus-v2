# NEXUS V2 — Phase 12 Supply-Chain Evidence Benchmark

## Scope

Phase 12 slice: SBOM + provenance/attestation for the verified release image pipeline.

## Decision

Use Docker BuildKit OCI attestations as the baseline:

- `sbom: true` for an image-bound SBOM attestation;
- `provenance: mode=max` for detailed build provenance;
- attestations are produced in the same CI build that pushes the release image;
- immutable image digest remains the deployment identity;
- no production deployment authority is introduced.

## Reference comparison

Docker BuildKit / `docker/build-push-action` is the primary reference because it supports SBOM and provenance attestations attached to registry-pushed image indexes, including private repositories.

GitHub Artifact Attestations were reviewed as an additional signed-provenance option. GitHub currently documents private/internal repository support as requiring GitHub Enterprise Cloud, so NEXUS does not make that capability a mandatory dependency for this slice.

## Acceptance

The slice is verified only when:

1. the release workflow still builds/pushes only in CI;
2. SBOM generation is explicitly enabled;
3. max provenance is explicitly enabled;
4. no SSH/SCP/production deployment authority is added;
5. static policy check, focused tests and full regression pass;
6. the Phase 12 gate remains OPEN until deploy manifests, backup/rollback runbooks and real registry evidence are completed.
