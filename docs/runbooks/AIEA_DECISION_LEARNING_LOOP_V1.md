# AIEA Decision Learning Loop v1

Status: candidate; must pass canonical verification before Audit/DONE.

## Scope

This slice closes the bounded feedback path:

`DecisionOutcome -> DecisionEvaluation -> Decision Memory -> AIEA ResearchEvidence -> Lesson -> falsification-first Hypothesis`

It also adds owner-scoped confidence-calibration projections and structured market-state tags (`regime`, `volatility`, `trend`, `liquidity`, `funding`, `event_risk`, `data_quality`) so historical decisions can be sliced by comparable context.

## Safety invariants

- AIEA remains research/evolution only.
- No VenueAdapter, ExecutionCoordinator, credential, direct order, Risk bypass, or live promotion authority is introduced.
- Missing independent evaluators produce `INSUFFICIENT_EVIDENCE`; PnL alone never fabricates regime/selection/timing/execution accuracy.
- Hypotheses are research-only and include every mandatory falsification check.
- Candidate creation, backtest/OOS/WF execution, shadow validation, promotion approval and activation remain behind the existing AIEA workflow and independent gates.
- Repeated publication of the same immutable evaluation is deterministic/idempotent in the append-only research store.

## Canonical verification

Run `VERIFY_AIEA_AUTONOMOUS_LOOP_COMPLETION.ps1` from the candidate archive against the canonical repository. Do not commit or push until focused, adjacent and full regression are green.
