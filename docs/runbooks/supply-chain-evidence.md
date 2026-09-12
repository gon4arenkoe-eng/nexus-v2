# Phase 12 — Supply-chain evidence

This slice extends the verified release-image foundation with image-bound SBOM and provenance attestations.

## Release invariant

`source commit -> CI verification -> BuildKit image build -> GHCR image -> immutable digest -> SBOM attestation + provenance attestation`

The attestations are emitted by BuildKit through `docker/build-push-action` and remain attached to the pushed image index. The release workflow requests `sbom: true` and `provenance: mode=max`.

## Verification

Static repository verification:

```text
py -3.13 infra/github/supply_chain_evidence_check.py
```

Registry/runtime verification is intentionally deferred until a real CI image exists. The later release-gate verification must inspect the pushed digest and prove that the image index exposes both SBOM and provenance attestations.

## Safety boundary

This slice does not add SSH, SCP, production credentials, production deployment jobs, or production build authority. `NO BUILD ON PRODUCTION` remains mandatory.

## Important GitHub-plan note

GitHub-native `actions/attest` is not made a hard dependency of this slice. GitHub documents that artifact attestations for private/internal repositories require GitHub Enterprise Cloud. BuildKit OCI attestations therefore remain the portable baseline for the private NEXUS repository. A later policy decision may add GitHub-native signed attestations if the repository plan supports them.
