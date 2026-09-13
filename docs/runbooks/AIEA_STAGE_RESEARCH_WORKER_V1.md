# AIEA Stage-aware Deterministic Research Worker v1

Phase 9 research worker implementation for the existing `AIEAExperimentLifecycleOrchestrator`.

## Scope

- Implements `ExperimentStageWorkerPort.execute_stage()` for the eight canonical stages.
- Uses deterministic offline candle replay; no exchange credentials, VenueAdapter writes, ExecutionCoordinator, or production filesystem writes.
- Preserves candidate dataset/code/environment/cost-model lineage in every `ExperimentRecord`.
- Runs real calculations for all 13 mandatory falsification checks at `FALSIFICATION`.
- Keeps synthetic OHLCV as a test/replay fixture only, not production research data.

## Stage mapping

- BACKTEST: lookahead, holdout isolation, realistic costs.
- OOS: out-of-sample validation.
- WALK_FORWARD: chronological fold stability.
- REGIME_SLICES: regime and single-symbol stability proxy.
- FALSIFICATION: all 13 mandatory checks.
- PAPER: minimum-sample evidence.
- SHADOW: data-quality evidence.
- COMPARISON: false-discovery evidence.

## Safety

Successful research evidence grants no activation or exchange authority. Promotion remains SHADOW-only and requires the existing independent risk/permission approvals.
