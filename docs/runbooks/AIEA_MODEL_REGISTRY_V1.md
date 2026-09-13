# AIEA Model Registry v1

Status: candidate until canonical verification and Audit evidence are complete.

## Purpose

Bind a model/strategy candidate to its reproducible research identity without creating new execution authority.

The registry reuses the canonical append-only AIEA research journal and `ResearchArtifact` contract. No model binary is stored in the production database. `ResearchArtifact.content_hash` is the model content identity; compact registry metadata stores dataset/feature/code/environment/cost/evidence/result lineage.

## Durable path

```text
CandidateVersion + PromotionReadiness
        -> RegistryEntry
        -> ResearchArtifact(kind=MODEL)
        -> AIEAResearchRecordStore
        -> aiea_research_records
        -> fresh-session typed restore
```

## Safety invariants

- registry is workspace/user scoped;
- records are immutable and idempotent on identical retry;
- conflicting re-registration fails closed;
- registry does not activate a candidate;
- SHADOW_READY still requires independent Risk and permission approval;
- AIEA has no VenueAdapter, ExecutionCoordinator, credentials or exchange write access;
- heavyweight model artifacts remain off-production; the registry stores identity/metadata only.
