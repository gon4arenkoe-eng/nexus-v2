# NEXUS V2 Dependency Boundaries

## Status

Phase 0 architecture policy.

This document defines allowed dependency direction and forbidden cross-boundary access before implementation code is introduced.

## 1. Canonical dependency direction

```text
packages/contracts
        ↑
domain/application logic
        ↑
ports
        ↑
adapters/infrastructure
```

Outer layers may depend on inner contracts and ports.

Inner domain/application layers must not depend on concrete infrastructure.

## 2. Repository ownership

### `packages/contracts`

Owns versioned shared contracts only:

- canonical identities;
- DTOs;
- event envelopes;
- observation contracts;
- command/result/error contracts;
- versioned compatibility surfaces.

Must not contain:

- exchange SDK clients;
- SQLAlchemy models;
- FastAPI routes;
- UI code;
- credential handling;
- production execution logic.

### `apps/core`

Owns deterministic trading runtime:

- TradeIntent;
- ExecutionPlan;
- PositionGroup;
- PositionLeg;
- ExecutionOrder;
- ExecutionFill;
- Ledger;
- Risk;
- Reconciliation;
- ExecutionCoordinator;
- restart/recovery orchestration.

Core does not search for alpha.

Core domain/application code must not import venue SDKs, SQLAlchemy, FastAPI, UI packages, or raw exchange payload models.

### `adapters/*`

Own venue-specific translation and I/O:

- REST/WebSocket clients;
- venue authentication;
- raw venue payload parsing;
- symbol/order/position normalization;
- VenueAdapter implementations.

Raw venue fields must terminate at the adapter boundary.

Adapters translate venue-specific state into canonical NEXUS contracts.

### `apps/intelligence`

Owns:

- market data;
- regime;
- volatility;
- liquidity;
- funding/open interest;
- news/events;
- correlations;
- freshness and quality.

Intelligence must not place, amend, cancel, or close production orders.

Intelligence publishes canonical analytical outputs only.

### `apps/aiea`

Owns research/evolution coordination:

- hypotheses;
- experiments;
- falsification;
- backtest/OOS/walk-forward evidence;
- model/strategy registry;
- promotion readiness;
- drift/rollback evidence.

AIEA must not access exchange credentials.

AIEA must not invoke VenueAdapter write methods.

AIEA must not invoke ExecutionCoordinator directly.

AI-generated code executes only in sandboxed research workers.

### `workers/aiea_research`

Owns heavy off-production research execution.

Must not run on the production runtime host.

Must not hold live exchange credentials.

### `apps/web`

Owns the Control Plane UI.

UI must communicate through typed/versioned APIs and event channels.

UI must not access databases directly.

### `packages/testkit`

Owns reusable test infrastructure:

- deterministic clock;
- deterministic ID providers;
- fake venue;
- canonical fixtures;
- replay fixtures;
- tenant-isolation fixtures.

### `packages/observability`

Owns shared logging, metrics, tracing, correlation-ID and redaction conventions.

Must not become a business-domain owner.

### `infra/*`

Owns infrastructure composition and deployment concerns.

Infrastructure may compose applications and adapters.

Infrastructure must not redefine canonical trading semantics.

## 3. Forbidden dependencies

The following are explicitly prohibited:

1. Core domain → exchange SDK/client.
2. Core domain → SQLAlchemy.
3. Core domain → FastAPI.
4. Core domain → UI framework.
5. Strategy → raw venue payload.
6. Strategy → direct venue order placement.
7. AIEA → VenueAdapter write methods.
8. AIEA → ExecutionCoordinator direct execution authority.
9. AIEA → exchange credentials.
10. Intelligence → production execution.
11. UI → direct database access.
12. Raw venue fields → canonical Core domain.
13. Adapter-specific enum/value leakage into shared canonical contracts.
14. Cross-user or cross-workspace ownership bypass.
15. Research worker → production runtime mutation.

## 4. Canonical execution ownership

```text
Strategy
    ↓
TradeIntent
    ↓
Allocation
    ↓
PortfolioRisk
    ↓
ExecutionPlan
    ↓
PositionGroup
    ↓
PositionLeg
    ↓
ExecutionOrder
    ↓
ExecutionFill
```

No strategy or research component may bypass this ownership chain.

## 5. Venue boundary

Canonical direction:

```text
venue raw payload
    ↓
adapter parser/normalizer
    ↓
canonical observation / command result
    ↓
Core application
```

Reverse execution direction:

```text
Core execution command
    ↓
VenueAdapter port
    ↓
venue-specific adapter
    ↓
exchange API
```

No venue-specific field is canonical merely because an exchange exposes it.

## 6. Multi-user ownership boundary

Canonical ownership:

```text
Workspace/Tenant
    ↓
User/Role
    ↓
ExchangeAccount
    ↓
Strategy/GridInstance
    ↓
Execution ownership
```

Cross-user and cross-workspace contamination is prohibited.

All future persistence, API and event contracts must preserve this ownership.

## 7. Grid boundary

Grid is not a normal StrategyPlugin.

Grid owns:

```text
GridProgram
    ↓
GridInstance
    ↓
GridCycle
    ↓
GridOrder/GridFill
    ↓
GridPnL
```

Grid reuses canonical Ledger, Risk, Reconciliation and VenueAdapter boundaries.

Grid must not create a parallel execution or accounting source of truth.

## 8. Reconciliation boundary

Reconciliation consumes canonical local state and canonical venue observations.

It records discrepancy/evidence.

Destructive correction is not implicit and requires an approved policy.

`STALE`, `DEGRADED`, and `UNKNOWN` states must remain explicit.

## 9. Contract-change rule

Shared contract changes must be:

- versioned;
- backward-compatibility reviewed;
- covered by contract tests;
- reflected in affected adapters/apps;
- recorded in Audit when they change verified behavior.

No application may silently redefine a shared canonical contract locally.

## 10. Enforcement plan

Phase 0 establishes this policy.

Phase 1 must make the policy mechanically enforceable through:

- package layout;
- import rules;
- architecture tests;
- contract tests;
- CI dependency checks.

Policy approval is not implementation DONE.
