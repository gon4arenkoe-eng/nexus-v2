# NEXUS V2 Grid Trading Desk — Phase 7G benchmark

## Scope

Phase 7G treats Grid as a dedicated trading program, not as a normal
`StrategyPlugin`.

Canonical ownership:

`GridProgram -> GridInstance -> GridCycle -> GridLevel/Order/Fill -> GridPnL`

The canonical execution ledger remains the accounting source of truth.
`GridPnL` is an attribution/projection and must never duplicate fill accounting.

## Legacy behavior extracted

The legacy snapshot contains both `strategies/grid_combo.py` and a separate
`agents/grid_agent.py`. The useful behavior retained as requirements is:

- regime-aware grid setup;
- range/center/levels;
- long, short and neutral grid direction;
- stateful order management;
- rebuild/recenter behavior;
- order/fill synchronization;
- realized/unrealized Grid PnL visibility.

The following legacy implementation patterns are intentionally not copied:

- direct exchange-client calls from Grid ownership;
- direct SQLAlchemy mutation/commit from Grid business logic;
- parallel accounting outside the canonical Ledger;
- automatic destructive recovery without an approved policy.

## Reference comparison

### Hummingbot GridExecutor / Grid Strike

Useful reference ideas:

- explicit grid levels;
- level-specific lifecycle;
- activation bounds;
- separate controller vs executor responsibilities;
- risk controls around each managed level;
- batch/controlled order management rather than uncontrolled order bursts.

NEXUS adoption:

- deterministic Grid level lifecycle;
- execution goes only through `GridExecutionBoundary`;
- Grid owns long-lived program/cycle state, while the execution layer owns
  actual canonical order execution.

License observed during reference research: Apache-2.0. No Hummingbot source is
copied and no runtime dependency is added.

### Passivbot

Useful reference ideas:

- grid entries and closes as long-lived inventory management;
- optional trailing behavior;
- explicit wallet/exposure limits;
- dedicated "unstucking" behavior for stuck positions.

NEXUS adoption:

- explicit inventory/risk budget;
- stuck-position policy is a first-class policy;
- destructive/realizing-loss unstucking is not automatic. The safe default is
  `HALT`; flattening requires an explicit `REDUCE_ONLY` policy.

License observed during reference research: Unlicense/public-domain dedication.
No Passivbot source is copied and no runtime dependency is added.

### NautilusTrader

Useful reference ideas:

- deterministic event-driven state machines;
- realistic event-driven simulation rather than candle-only optimistic fills;
- separation between strategy logic, order execution and recovery;
- grid/market-making examples built on canonical order/event infrastructure.

NEXUS adoption:

- deterministic Grid domain/application boundary;
- queue/liquidity constrained event simulation;
- maker fees, slippage/adverse-selection and latency assumptions are explicit;
- restart state is durable and reconciliation failure is fail-closed.

License observed during reference research: LGPL-3.0-only. No NautilusTrader
source is copied and no runtime dependency is added.

## Phase 7G design decisions

1. Grid is not registered as a normal `StrategyPlugin`.
2. Grid Core has no `VenueAdapter`, SQLAlchemy, FastAPI or direct submit/cancel
   dependency.
3. Capital reservation is mandatory before a Grid instance is checkpointed.
4. Unknown order outcome or reconciliation discrepancy moves Grid to
   `RECOVERY`.
5. Recenter cancels the old cycle through the execution boundary before a new
   cycle is created.
6. `STALE`, `UNKNOWN` and discrepancies are never hidden as healthy Grid state.
7. Grid PnL is reconstructed from canonical fill attribution and rejects
   duplicate fills.
8. Multi-user controls are user-scoped.
9. Regime allow-list can stop Grid fail-closed; range deviation can trigger a
   deterministic recenter.
10. Simulation models book liquidity, queue fill fraction, maker fee,
    slippage, adverse selection and latency. Candle-only certification remains
    insufficient for production.

## Production safety

Phase 7G does not enable Restricted Live or Full Live. No AI component gains
exchange authority. Concrete venue DEMO/shadow certification remains required
before any Grid live cutover.
