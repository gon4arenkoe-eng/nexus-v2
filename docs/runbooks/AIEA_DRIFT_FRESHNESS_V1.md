# AIEA Drift / Freshness + Champion-Challenger v1

This slice turns model/strategy evidence degradation into deterministic research actions without granting activation authority.

## Invariants

- Freshness is derived from evidence timestamps, never supplied as a trusted ratio.
- Stale evidence becomes `UNKNOWN` and triggers research, never live mutation.
- Degraded champion evidence may request challenger research.
- Challenger lift may reach `PROMOTION_REVIEW`, never direct activation.
- Independent PromotionReadiness, risk approval and permission approval remain unchanged.
- Drift evidence is immutable, tenant-scoped and stored in the existing AIEA research journal as `ArtifactKind.EVIDENCE`.
- No new table or migration is required.
- `live_mutation_allowed` is always false in this slice.
