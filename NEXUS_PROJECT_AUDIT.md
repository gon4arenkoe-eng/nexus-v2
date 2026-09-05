
## 2026-09-05 — Phase 2 ExecutionPlan / ExecutionLegPlan migration

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Scope:
- migrated immutable ExecutionLegPlan domain contract;
- migrated immutable ExecutionPlan domain contract;
- canonical OrderType comes from Core Domain;
- TradeSide and TradeIntentShape remain canonical intent/execution semantics;
- no PositionGroup, PositionLeg, ExecutionOrder or ExecutionFill added in this slice.

ExecutionLegPlan invariants:
- non-empty leg_id, order_id, client_order_id;
- AccountId and InstrumentId required;
- account and instrument venue must match within each leg;
- TradeSide required;
- quantity must be finite positive Decimal;
- OrderType required;
- MARKET forbids limit_price;
- LIMIT requires finite positive Decimal limit_price;
- reduce_only must be bool.

ExecutionPlan invariants:
- non-empty plan_id and intent_id;
- positive integer user_id;
- TradeIntentShape required;
- non-empty strategy and source;
- optional non-empty strategy_version;
- legs must be immutable tuple of ExecutionLegPlan;
- unique leg_id, order_id and client_order_id;
- SINGLE_LEG requires exactly one leg;
- PAIR requires exactly two legs;
- BASKET requires at least two legs;
- cross-venue pair is allowed with per-leg venue ownership;
- created_at must be timezone-aware and is normalized to UTC.

Architecture:
- Core Domain does not import apps.core.ports;
- no VenueAdapter dependency;
- no SQLAlchemy/FastAPI dependency;
- no Reconciliation logic;
- no ExecutionCoordinator logic;
- production authority unchanged.

Verification:
- focused ExecutionPlan tests: 31 passed;
- adjacent TradeIntent + Venue + ExecutionPlan tests: 60 passed;
- full suite: 204 passed;
- flake8: exit 0;
- mypy apps/core --explicit-package-bases --ignore-missing-imports: exit 0;
- compileall: exit 0;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_EXECUTION_PLAN_MIGRATION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
