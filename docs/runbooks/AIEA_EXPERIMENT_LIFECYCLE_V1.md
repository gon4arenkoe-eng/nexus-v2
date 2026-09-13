# AIEA Experiment Lifecycle v1

## Purpose

Enforce one deterministic, fail-closed research path for each immutable candidate:

`BACKTEST -> OOS -> WALK_FORWARD -> REGIME_SLICES -> FALSIFICATION -> PAPER -> SHADOW -> COMPARISON -> PROMOTION_READINESS`

## Invariants

- A candidate cannot skip or reorder a lifecycle stage.
- A failed or below-threshold stage stops the lifecycle.
- A rejected candidate cannot acquire later-stage evidence.
- Every experiment must match candidate workspace/user, hypothesis, dataset hash, code hash, environment digest and cost-model version.
- Persisted experiments are reused on restart; compatible completed stages are not rerun.
- Duplicate immutable evidence for the same candidate/stage fails closed.
- Successful completion yields at most `SHADOW_READY` and still requires independent Risk and permission approvals.
- The orchestrator has no VenueAdapter, exchange credentials, ExecutionCoordinator or production-write authority.

## Persistence / restart

The existing append-only AIEA research journal remains the source of provenance. The store exposes tenant-scoped experiment reads by `candidate_id` so an interrupted lifecycle can resume from the first missing mandatory stage.

## Safety

This capability does not activate a strategy and does not relax production safety. AI promotion remains shadow-only until later approved gates explicitly change that state.
