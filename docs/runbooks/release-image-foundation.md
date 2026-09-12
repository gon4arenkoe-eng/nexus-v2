# NEXUS V2 Release Image Foundation

Status: Phase 12 foundation only. This document does not authorize production
deployment.

## Purpose

Establish the first verified supply-chain boundary:

`source commit -> CI verification -> CI-only container build -> GHCR -> digest`

The production host is not involved in building this image.

## Trigger

The release workflow is intentionally limited to a version tag (`v*`) or an
explicit `workflow_dispatch` invocation with a release label.

## Evidence

A successful workflow records:

- Git commit SHA;
- GHCR image name;
- immutable `sha-<full commit>` tag;
- registry `sha256:` digest.

The digest, not a mutable tag, is the canonical artifact identity for future
deployment work.

## Safety boundary

This foundation workflow MUST NOT:

- SSH/SCP to `nexus-bot`;
- execute `docker compose up` on production;
- build on production;
- receive exchange credentials;
- enable Restricted Live or Full Live;
- grant AIEA execution authority.

SBOM, provenance attestation, production deploy manifests and rollback-by-digest
are subsequent Phase 12 slices and remain required before
`NEXUS_V2_RELEASE_PIPELINE_OK` can close.
