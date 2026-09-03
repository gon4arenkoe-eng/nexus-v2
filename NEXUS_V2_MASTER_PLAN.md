# NEXUS V2 MASTER PLAN

**Version:** 1.1-draft  
**Date:** 2026-09-03  
**Status:** PROPOSED FOR APPROVAL — not yet canonical until committed to the project and registered in `NEXUS_PROJECT_AUDIT.md`  
**Companion:** `NEXUS_V2_FUNCTIONAL_INVENTORY.md`

---

## 0. Governance

### 0.1. Sources of truth

Two documents have different responsibilities:

- `NEXUS_V2_MASTER_PLAN.md` — forward-looking canonical roadmap and target architecture.
- `NEXUS_PROJECT_AUDIT.md` — sole source of truth for actual current state, evidence and DONE/VERIFIED status.

The Master Plan never makes an item DONE. Only Audit evidence can do that.

### 0.2. Working rule

Every implementation step follows:

`FACT → FULL AUDIT CROSS-CHECK → CODE CHECK → EVIDENCE → AUDIT → STATUS → ONE NEXT STEP`

Before every new design or implementation target, search the complete relevant Audit scope to avoid recreating already-approved work.

### 0.3. Production permissions

Unless explicitly changed by a separate approved security/architecture decision:

- Strategy Decision Engine AI promotion path: SHADOW-ONLY.
- Advisory: OBSERVE_ONLY.
- Restricted Live: DISABLED.
- Full Live: DISABLED.
- AI direct exchange access: BLOCKED.
- AIEA has no direct ExecutionCoordinator, VenueAdapter write, Risk bypass or exchange credential access.

---

## 1. Mission

Build NEXUS V2 as a powerful multi-user algorithmic trading platform with four product planes and three backend bounded contexts:

1. **NEXUS Core V2** — deterministic trading, risk, execution, ledger, reconciliation, venue integration.
2. **NEXUS Intelligence** — market data, regime, liquidity, volatility, funding/OI, news/events and canonical market context.
3. **NEXUS AIEA** — research, hypotheses, experiments, ML, validation, comparison, promotion/rollback and research memory.
4. **NEXUS Control Plane** — multi-user web shell, settings, administration, monitoring, analytics, AIEA laboratory and operational controls.

The Control Plane is a presentation/API shell, not a fourth trading brain.

### Core design objective

AIEA may improve what NEXUS decides to trade. Core V2 must guarantee how NEXUS executes, records, reconciles and controls risk.

No architecture can guarantee profitability. V2 is designed to maximize correctness, robustness, measurable execution quality and research discipline.

---

## 2. Architectural reference benchmark

NEXUS adopts proven patterns, not wholesale dependencies or copied architectures.

| Reference | Primary lesson for NEXUS | Adoption policy |
|---|---|---|
| NautilusTrader | deterministic event-driven execution, reconciliation, startup recovery, multi-venue semantics | P0 Core reference; patterns only unless separately approved |
| Hummingbot | connector separation, private user streams, in-flight order tracking, perpetual position modes | P0 VenueAdapter reference |
| QuantConnect LEAN | modular engine interfaces, transaction processing, live/backtest environment parity | P0 engine/parity reference |
| vn.py / VeighNa | simple EventEngine + Gateway + OMS separation | P0 event/OMS simplicity reference |
| CCXT | very broad exchange capability/mapping coverage | P0 exchange mapping/reference; not sole canonical domain |
| Microsoft Qlib | quant data/workflow/model lifecycle and online/simulation model management | P0 AIEA research reference |
| Microsoft RD-Agent | automated hypothesis→implementation→experiment→feedback research loop | P0 AIEA autonomous R&D reference, sandboxed only |
| Freqtrade/FreqAI | feature pipelines, adaptive retraining, lookahead analysis, operational strategy tooling | P1 AIEA validation/ML reference |
| VectorBT | high-throughput parameter/research exploration | P1 research acceleration; license review required before embedding |
| FinRL-X | AI-native modular production direction and RL research patterns | P2 experimental reference, not core dependency |

### License policy

- Track every reference/dependency license in a machine-readable third-party inventory.
- Do not copy source code from LGPL/GPL/Commons-Clause projects without explicit license review.
- Prefer reimplementation of architecture patterns behind NEXUS-owned contracts.
- CCXT/Qlib/vn.py permissive licenses do not remove the need for security and dependency review.

---

## 3. Target repository model

Use one private **monorepo** to prevent contract drift while keeping deployable components independent.

```text
nexus-v2/
├── apps/
│   ├── core/                  # production trading runtime
│   ├── intelligence/          # market/intelligence runtime
│   ├── aiea/                  # AIEA API/runtime coordinator
│   └── web/                   # Control Plane frontend
│
├── workers/
│   └── aiea_research/         # heavy off-production research workers
│
├── packages/
│   ├── contracts/             # versioned shared DTO/events/identities
│   ├── testkit/               # fixtures, fake venue, deterministic clock
│   └── observability/         # logging/metrics/tracing conventions
│
├── adapters/
│   ├── bingx/
│   ├── binance/
│   ├── bybit/
│   ├── okx/
│   └── ...
│
├── infra/
│   ├── compose/
│   ├── migrations/
│   ├── github/
│   └── deploy/
│
├── docs/
│   ├── architecture/
│   ├── runbooks/
│   └── adr/
│
├── NEXUS_V2_MASTER_PLAN.md
├── NEXUS_V2_FUNCTIONAL_INVENTORY.md
└── NEXUS_PROJECT_AUDIT.md
```

### Dependency direction

```text
contracts/domain
      ↑
application/core logic
      ↑
ports
      ↑
adapters/infrastructure
```

Forbidden dependencies include:

- Core domain → exchange client.
- Core domain → SQLAlchemy/FastAPI.
- AIEA → ExecutionCoordinator or VenueAdapter write methods.
- Strategies → raw exchange dictionaries.
- UI → direct database access.
- Intelligence → production order execution.

---

## 4. Runtime deployment model for the small server

### 4.1. Production server role

`nexus-bot` becomes a **runtime host only**.

Production must not be used for:

- source development;
- Docker image builds;
- heavy backtests;
- ML training;
- research datasets;
- parameter sweeps;
- large model artifact storage.

Invariant: **NO BUILD ON PRODUCTION**.

### 4.2. Off-server build/research

Primary flow:

```text
local workstation / Codespace / research host
        ↓
private GitHub monorepo
        ↓
GitHub Actions
        ↓
unit + contract + integration + security + migration + replay gates
        ↓
versioned Docker images
        ↓
GitHub Container Registry (GHCR)
        ↓
production: pull by immutable tag/digest
```

Heavy AIEA research runs in `workers/aiea_research` outside production. It publishes only versioned datasets/model/strategy artifacts and evidence manifests through approved storage/APIs.

### 4.3. Production footprint

Expected lightweight production services:

- `nexus-core`
- `nexus-intelligence-runtime`
- `nexus-aiea-runtime` (control/promotion metadata only; heavy research external)
- `nexus-web`
- PostgreSQL
- Redis
- Nginx/reverse proxy

Large history and models should live in external object storage or a dedicated research machine, not the production disk.

---

## 5. GitHub operating model

### 5.1. Repository

- Private monorepo.
- No `.env`, API keys, DB dumps, model secrets, exchange credentials or raw production data committed.
- `main` is release-quality only.
- Feature branches + pull requests for every material change.
- Enable protected branch/ruleset with required checks when supported by the GitHub account plan; otherwise follow the same PR-only discipline manually.

### 5.2. CI stages

Every PR should run, as applicable:

1. formatting/lint;
2. type checks;
3. unit tests;
4. shared-contract compatibility tests;
5. Postgres integration tests;
6. Redis/event transport tests;
7. Alembic single-head + upgrade/downgrade checks;
8. venue adapter contract tests using recorded/fake payloads;
9. deterministic replay tests;
10. lookahead/data-leakage checks for research changes;
11. security scan;
12. dependency vulnerability scan;
13. Docker build;
14. SBOM generation;
15. artifact/container provenance attestation.

### 5.3. Release

Release images are tagged with both semantic version and immutable commit identity, for example:

`ghcr.io/<owner>/nexus-core:2.1.0`  
`ghcr.io/<owner>/nexus-core:sha-<commit>`

Production deploys an immutable digest and records that digest in the Audit/deployment record.

### 5.4. Supply-chain controls

- Dependabot security updates.
- Pinned GitHub Actions versions/SHAs for sensitive workflows.
- Least-privilege workflow permissions.
- Artifact attestations for release images.
- SBOM per release.
- Secret scanning/pre-commit secret detection.

---

## 6. NEXUS Core V2

### 6.1. Domain kernel

Canonical immutable/value-oriented types:

- User/WorkspaceId
- VenueId
- AccountId
- InstrumentId / Instrument
- StrategyId / StrategyVersionId
- TradeIntent / PairTradeIntent / BasketTradeIntent
- PortfolioTarget
- ExecutionPlan / ExecutionLegPlan
- OrderId / ClientOrderId / VenueOrderId
- FillId / VenueFillId
- PositionGroup / PositionLeg
- ReconciliationRunId / DiscrepancyId

Execution-critical quantities/prices/fees use decimal-safe semantics; no silent binary-float ownership in canonical persistence.

### 6.2. Typed event model

Core state-changing evidence is represented by typed events, including:

- intent accepted/rejected;
- plan created;
- order submitted/accepted/partially-filled/filled/cancelled/rejected/unknown;
- fill observed;
- position opened/adjusted/closed;
- reconciliation started/completed/degraded;
- discrepancy found/resolved;
- recovery requested/completed/failed;
- risk decision;
- safety block;
- strategy version activation/deactivation.

The database may maintain projections, but immutable events/fills remain evidence.

### 6.3. VenueAdapter

Venue-specific transport and parsing stay behind adapters.

Canonical read surface must cover, capability-dependently:

- instruments/market metadata;
- account/balances;
- positions;
- order query;
- open orders;
- fills/trades;
- private event stream.

Canonical write surface must cover only supported operations:

- submit order;
- cancel order;
- modify/replace where supported;
- leverage/position-mode/protection operations only through explicit capabilities/policies.

Unsupported required capabilities fail closed.

### 6.4. Venue certification priority

**P0:** BingX, Binance USD-M, Bybit, OKX.  
**P1:** Bitget, Gate.io, KuCoin Futures, Hyperliquid.  
**P2:** BitMEX, Deribit, Kraken Futures, MEXC, HTX, Coinbase International, Backpack and others after capability review.

CCXT is the breadth reference; Hummingbot/Nautilus/official venue APIs validate execution semantics for critical venues.

### 6.5. Ledger

Preserve and extend the already-established Core V2 ownership chain:

`TradeIntent → ExecutionPlan → PositionGroup → PositionLeg → ExecutionOrder → ExecutionFill`

Requirements:

- idempotent writes;
- immutable fill evidence;
- local/venue state separation;
- deterministic replay;
- restart-safe state;
- pair/basket ownership;
- strategy/version/user/account lineage.

### 6.6. Reconciliation Engine

Reconciliation is a first-class production subsystem.

Startup sequence:

```text
load local ledger/cache
→ connect venue adapters
→ query/consume venue truth
→ reconcile orders
→ reconcile fills
→ reconcile positions
→ emit discrepancy/evidence
→ only then activate strategy execution
```

Continuous reconciliation runs while live.

Required discrepancy classes include:

- local order missing on venue;
- venue order unknown locally;
- local/venue order-state drift;
- missing local fill;
- duplicated/replayed fill;
- local position missing on venue;
- venue position missing locally;
- quantity/side/entry drift;
- account/balance stale/unavailable;
- reconciliation source unavailable/STALE/DEGRADED.

Phase 3 detects and records discrepancies. Destructive correction requires a separately approved policy.

### 6.7. Execution Coordinator

The coordinator owns the deterministic execution workflow, not strategies or AIEA.

Requirements:

- explicit states;
- idempotent command attempts;
- unknown-outcome recovery;
- partial fill handling;
- cancel/replace workflow;
- restart recovery;
- no naked pair exposure without recovery policy;
- per-leg ownership;
- safe closes independent of new-exposure permission.

### 6.8. Risk architecture

Layered risk:

1. strategy/signal eligibility;
2. single-leg sizing policy;
3. portfolio risk;
4. venue/account exposure limits;
5. liquidity/slippage guard;
6. execution safety;
7. global kill switch.

PortfolioRiskEngine must own:

- gross/net exposure;
- leverage/margin;
- per-user/per-account/per-venue limits;
- asset/currency concentration;
- correlation clusters;
- strategy concentration;
- pair/basket hedge integrity;
- daily/rolling drawdown;
- liquidity/capacity.

### 6.9. Strategy runtime

Strategies produce canonical intents, never direct orders.

Every strategy is versioned and has:

- manifest;
- parameter schema;
- supported instruments/venues;
- data requirements;
- risk requirements;
- code/artifact hash;
- validation evidence link;
- activation state.

The same strategy intent semantics should be used in research, backtest, paper, shadow and live wherever technically possible.

### 6.10. Strategy Portfolio Program

NEXUS V2 optimizes for a small portfolio of genuinely different, evidence-backed trading edges rather than a large catalog of superficially different indicator strategies.

Before any legacy strategy is promoted into V2, it must pass a strategy benchmark against mature open-source/reference implementations and published methodology where available. Benchmark references include NautilusTrader examples/tutorials, Hummingbot Strategy V2/controllers, Freqtrade/FreqAI strategy tooling, QuantConnect LEAN Algorithm Framework, Qlib research/portfolio workflows, and specialized projects for the relevant strategy family.

Canonical strategy families to research and certify include:

1. trend / momentum;
2. mean reversion / range;
3. breakout / volatility expansion;
4. liquidity / order-book / market-structure;
5. statistical arbitrage / relative value;
6. funding / basis / carry / cross-venue relative value;
7. market making where venue economics justify it.

The existing legacy strategy list is a candidate pool, not the target production catalog. Multiple legacy strategies may be consolidated into one stronger canonical strategy family if they express the same economic hypothesis.

Every strategy candidate must be evaluated on:

- explicit economic/market hypothesis;
- required market regime;
- signal stability;
- parameter stability;
- cross-symbol and cross-period robustness;
- turnover;
- fees/funding/slippage;
- capacity/liquidity sensitivity;
- latency sensitivity;
- tail risk and drawdown shape;
- correlation with other active strategies;
- execution complexity;
- data dependency/freshness;
- deterministic replay;
- lookahead/leakage tests;
- OOS and walk-forward performance;
- falsification tests;
- paper/shadow performance;
- live execution-quality dependency.

A strategy is not selected because it wins one backtest. AIEA must compare candidates using a multi-objective scorecard and reject strategies whose apparent edge depends on one period, one symbol, unstable parameters, unrealistic fills, or unmodeled costs.

### 6.11. Strategy allocation and diversification

Strategy selection is separate from capital allocation.

The target flow is:

`Strategy/Alpha → TradeIntent → PortfolioConstruction/Allocation → PortfolioRisk → ExecutionPlan`

Portfolio allocation must consider expected edge, confidence, capacity, drawdown, regime suitability and correlation between strategies. The system should prefer complementary strategy families rather than several variants of the same signal.

AIEA may recommend activation/deactivation or allocation changes, but production changes remain behind explicit promotion/risk/permission gates.

### 6.12. Grid Trading Desk — independent trading direction

Grid is NOT treated as an ordinary entry/exit StrategyPlugin in the target architecture. It is a dedicated trading program with its own long-lived state, capital allocation, order inventory, recovery rules, risk budget and performance attribution.

Target ownership:

`GridProgram → GridInstance → GridCycle → GridOrder/Fill → GridPnL`

The Grid Trading Desk shares canonical Core V2 infrastructure:

- Instrument/Venue/Account identities;
- VenueAdapter;
- ExecutionBoundary;
- canonical order/fill ledger;
- reconciliation;
- portfolio risk;
- event model;
- multi-user ownership.

But it owns grid-specific semantics:

- grid range/center/spacing;
- arithmetic/geometric/dynamic spacing;
- inventory skew;
- grid side/bias;
- level lifecycle;
- replenishment policy;
- regime-aware enable/disable/recenter;
- capital reservation;
- max inventory/exposure;
- stuck-position/unstucking policy if approved;
- grid-specific stop/rebuild policy;
- realized/unrealized grid performance attribution.

Grid PnL must be independently visible per user/account/venue/symbol/grid instance, while the canonical ExecutionFill/Ledger remains the accounting source of truth. GridPnL is an attribution/projection and must never double-count fills relative to portfolio PnL.

Grid must have a dedicated research/backtest simulator because fill probability, queue position, spread, adverse selection, maker/taker fees, latency and order-replenishment semantics materially affect results. Candle-only optimistic grid simulations are insufficient for production certification.

Reference-first research for Grid must explicitly compare at least Hummingbot GridExecutor/Grid Strike patterns, Passivbot grid/trailing/unstucking patterns, and NautilusTrader grid market-making/event-driven simulation patterns before NEXUS Grid V2 design is approved.

---

## 7. NEXUS Intelligence

### 7.1. Purpose

Produce trustworthy canonical market context for strategies, Risk and AIEA without owning execution.

### 7.2. Data domains

- trades;
- candles;
- top-of-book;
- order-book depth;
- spread/liquidity;
- funding;
- open interest;
- mark/index price;
- volatility;
- market regime;
- correlations;
- news/events;
- optional on-chain/whale data;
- future multi-asset corporate/session/reference data.

### 7.3. Data quality

Every feed tracks:

- source;
- timestamp/event time;
- ingestion time;
- freshness;
- gaps;
- duplicates;
- outliers;
- schema/version;
- provenance.

Stale market context must be explicit and may block trading where required.

### 7.4. Canonical MarketContext

Strategies and AIEA consume normalized context, not exchange-specific payloads.

MarketContext may include:

- regime probabilities/classification;
- volatility state;
- trend state;
- liquidity state;
- funding/OI state;
- cross-market context;
- news/event risk window;
- data quality/freshness score.

---

## 8. NEXUS AIEA

### 8.1. Role

AIEA is the research/evolution brain. It discovers and validates candidates; it never directly executes exchange orders.

### 8.2. Research loop

```text
Market/Trade Evidence
→ Knowledge Snapshot
→ Hypothesis
→ Candidate implementation/specification
→ Static/Data validation
→ Backtest
→ Cost/slippage/funding model
→ OOS
→ Walk-forward
→ Regime/event slices
→ Stability/falsification tests
→ Paper
→ Shadow
→ Comparison vs baseline
→ Promotion readiness
→ independent risk/permission approval
→ controlled strategy-version activation
→ ongoing drift/quality monitoring
→ rollback/retirement when degraded
```

### 8.3. Falsification-first policy

AIEA must not optimize for a beautiful backtest. Each hypothesis has predeclared pass/fail criteria before final evaluation.

Mandatory defenses include:

- lookahead leakage checks;
- train/validation/test isolation;
- purged/embargoed time splits where appropriate;
- OOS holdout isolation from iterative feedback;
- walk-forward validation;
- multiple-hypothesis/false-discovery control where applicable;
- realistic fees/funding/slippage;
- regime/symbol/time slices;
- minimum sample sizes;
- sensitivity/stability analysis;
- capacity/liquidity checks;
- survivorship/data-quality checks where applicable.

### 8.4. Experiment and model registry

Every experiment/model/strategy candidate records:

- user/workspace;
- parent version;
- dataset version/hash;
- feature definition/hash;
- model/code hash;
- hyperparameters;
- train/validation/test intervals;
- execution-cost model version;
- result/evidence hashes;
- environment/container digest;
- promotion status;
- reviewer/approval;
- rollback target.

### 8.5. Automated R&D

RD-Agent/Qlib-style automated loops are permitted only in an isolated research worker.

AI-generated code must pass:

- sandbox restrictions;
- static analysis;
- dependency allowlist;
- unit tests;
- deterministic research tests;
- no secrets/network-to-exchange permissions;
- human or policy approval before becoming a candidate version.

### 8.6. ML lifecycle

AIEA manages:

- training;
- inference artifact creation;
- model registry;
- model freshness;
- drift;
- recalibration;
- challenger vs champion comparison;
- rollback.

Model retraining never automatically grants live permissions.

### 8.7. Compute/storage placement

Heavy research is off-production.

Production receives only compact, versioned runtime artifacts necessary for approved inference/strategy behavior.

---

## 9. Multi-user architecture

### 9.1. Ownership hierarchy

```text
Workspace/Tenant
  └── User memberships + roles
      └── ExchangeAccount(s)
          └── StrategyInstance(s)
              └── TradeIntent
                  └── ExecutionPlan
                      └── PositionGroup
                          └── Orders/Fills
```

### 9.2. Roles

Initial target roles:

- `OWNER`
- `ADMIN`
- `TRADER`
- `VIEWER`

Optional later role:

- `RISK_APPROVER`

Permissions must be explicit per action, especially:

- credential management;
- strategy activation;
- risk-limit changes;
- exchange environment changes;
- live permission changes;
- AIEA promotion approval;
- manual close/cancel/recovery actions.

### 9.3. Tenant isolation

Every operational query/write is tenant-scoped.

High-value tables should be evaluated for PostgreSQL Row-Level Security in addition to application checks.

Cross-user cache keys, events, WebSocket subscriptions and background jobs must carry tenant ownership.

### 9.4. Secrets

- encryption at rest;
- never log decrypted credentials or prefixes;
- separate secret access layer;
- credentials unavailable to AIEA workers;
- key rotation support;
- account permission guidance: trading/read only, withdrawals disabled where venue supports it.

---

## 10. Settings architecture

Replace one monolithic `BotSettings` concept with hierarchical, typed, versioned settings.

Priority layers:

```text
system safe defaults
→ workspace settings
→ exchange-account settings
→ risk profile
→ strategy instance settings
→ optional session override
```

Settings domains:

- trading;
- portfolio risk;
- strategy parameters;
- venue/account mode;
- market data;
- AIEA research;
- promotion permissions;
- notifications;
- UI preferences;
- feature flags.

Every safety-critical setting change emits an audit event with old/new value, actor and timestamp.

Dangerous changes require confirmation and may require re-authentication/approval.

---

## 11. NEXUS Control Plane / UI

### 11.1. Product goal

The UI must make NEXUS understandable as a trading system, not merely show whether a bot process is running.

### 11.2. Primary navigation

- Command Center / Overview
- Portfolio
- Positions
- Orders & Fills
- Strategies
- Strategy Versions
- Risk
- Reconciliation
- Exchanges & Accounts
- Market Intelligence
- News / Events
- AIEA Research Center
- Experiments
- Candidates / Promotion
- Backtests / Walk-forward
- Model Health
- Execution Quality
- History / Attribution
- Events / Audit
- Notifications
- Settings
- Admin / Users / Roles

### 11.3. Dashboard

Top-level operational cards:

- NAV/equity;
- realized/unrealized PnL;
- drawdown;
- gross/net exposure;
- risk utilization;
- open positions;
- active strategies;
- venue health;
- reconciliation health;
- execution quality/slippage;
- data freshness;
- AIEA candidates/alerts;
- system health.

### 11.4. UX requirements

- modern responsive design;
- consistent design system;
- dark/light modes;
- accessible contrast/keyboard behavior;
- desktop/tablet/mobile layouts;
- real-time typed updates;
- clear loading/empty/error/stale states;
- dangerous-action confirmations;
- no ambiguous green status when data is stale;
- audit link from every consequential action.

### 11.5. Frontend technology

Preferred direction: TypeScript SPA (React/Vite or equivalent) with generated API types from OpenAPI. Final framework choice is an implementation decision after UI benchmark, not a Core dependency.

---

## 12. API and event contracts

- Versioned REST API (`/api/v2` or equivalent).
- OpenAPI is contract-tested.
- Typed error envelope.
- Idempotency keys for commands.
- Pagination/filter/sort conventions.
- Authenticated user-scoped WebSocket/SSE event gateway.
- Event schema versioning.
- Event sequence IDs and reconnect/resume semantics where needed.
- No frontend dependence on raw database models.

---

## 13. Data architecture

### Transactional

PostgreSQL owns:

- users/tenancy;
- accounts;
- configuration;
- strategy versions;
- execution ledger;
- reconciliation evidence;
- audit;
- promotion metadata.

### Runtime transport/cache

Redis may provide:

- distributed locks;
- cache;
- bounded runtime event transport/streams;
- job coordination.

Redis is not the sole durable source of trading truth.

### Research/time-series

Large datasets, features and models stay outside the production server. Preferred formats are columnar/versionable artifacts such as Parquet plus an object-store abstraction.

---

## 14. Observability and operations

Required signals:

- structured logs;
- metrics;
- traces/correlation IDs;
- order/venue latency;
- WebSocket reconnects/gaps;
- REST fallback rates;
- reconciliation discrepancies;
- stale data;
- rejected/unknown orders;
- fill latency/slippage;
- portfolio/risk utilization;
- AIEA job status;
- model drift/freshness;
- DB/Redis health.

Every operational alert links to a runbook.

---

## 15. Testing pyramid

### Level 1 — Pure domain tests

Fast deterministic tests for identities, intents, states, transitions, risk math and settings validation.

### Level 2 — Contract tests

- VenueAdapter certification suite;
- repository contracts;
- event schemas;
- API schemas;
- strategy contract.

### Level 3 — Integration

PostgreSQL + Redis + application services.

### Level 4 — Fault/recovery

Inject:

- REST timeout;
- response lost after venue acceptance;
- duplicate fill;
- out-of-order event;
- partial fill;
- WS disconnect;
- process restart;
- DB retry;
- stale venue/account snapshot.

### Level 5 — Historical deterministic replay

Rebuild local state from recorded events and compare hashes/projections.

### Level 6 — Research validation

Lookahead, OOS, walk-forward, cost, regime/stability and falsification gates.

### Level 7 — Venue DEMO certification

Per venue, verify order/fill/position/restart/reconciliation semantics.

### Level 8 — Shadow parallel run

New system observes the same market/runtime environment without new live authority and is compared with legacy behavior/evidence.

---

## 16. Functional parity program

`NEXUS_V2_FUNCTIONAL_INVENTORY.md` is mandatory for migration.

Every legacy user-facing or safety-critical capability gets:

- current source/evidence;
- V2 owner;
- migration action;
- parity test;
- evidence tag;
- retirement decision.

No legacy capability is silently dropped.

Legacy strategies are not automatically considered production-worthy merely because they existed. Functional parity preserves availability; AIEA/research gates determine whether a strategy is eligible for activation.

---

## 17. Phased implementation roadmap

### Phase 0 — Architecture baseline and repository bootstrap

Deliverables:

- approve this Master Plan;
- freeze functional inventory v1;
- create private GitHub monorepo;
- establish directories/contracts policy;
- CI skeleton;
- local/devcontainer environment;
- no production change.

Gate: `NEXUS_V2_FOUNDATION_PLAN_OK`

### Phase 1 — Shared contracts and testkit

Deliver:

- canonical identities;
- money/quantity/time conventions;
- typed event envelope;
- error/result contracts;
- deterministic clock/ID providers;
- fake venue/testkit;
- compatibility tests.

Gate: `NEXUS_V2_SHARED_CONTRACTS_OK`

### Phase 2 — Import and harden existing Core V2 foundation

Migrate verified work rather than recreate it:

- TradeIntent;
- identities;
- Venue order contracts;
- ExecutionPlan/Group/Leg/Order/Fill;
- ledger/replay/idempotency;
- local/venue order state.

No legacy runtime cutover.

Gate: `NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`

### Phase 3 — Reconciliation

Deliver:

- venue position/account/fill observation contracts;
- explicit reconciliation states;
- discrepancy model;
- startup reconciliation;
- deterministic repeated reconciliation;
- immutable discrepancy evidence;
- no destructive auto-correction.

Extract proven behavior from PositionAgent without copying legacy ownership.

Gate: `TRADING_CORE_V2_RECONCILIATION_OK`

### Phase 4 — Execution Coordinator

Deliver deterministic single-leg execution state machine, unknown outcomes, retry/idempotency, recovery, cancel/replace and restart behavior.

Gate: `TRADING_CORE_V2_EXECUTION_COORDINATOR_OK`

### Phase 5 — Pair/basket execution

Deliver pair-native ownership, partial-fill recovery, coordinated close and hedge integrity.

Gate: `TRADING_CORE_V2_PAIR_EXECUTION_OK`

### Phase 6 — Portfolio Risk V2

Deliver portfolio/account/venue/correlation/concentration/liquidity risk and integrate proven single-leg policy.

Gate: `TRADING_CORE_V2_PORTFOLIO_RISK_OK`

### Phase 7 — Strategy Portfolio Benchmark, runtime and backtest/live parity

Deliver:

- complete legacy strategy inventory and family clustering;
- GitHub/reference benchmark per strategy family;
- shortlist of canonical strategy families based on distinct economic hypotheses rather than count;
- versioned Strategy Catalog;
- multi-objective AIEA strategy scorecard;
- canonical strategy runtime;
- portfolio allocation interface;
- simulator/live semantic parity;
- per-strategy PnL/attribution and correlation analytics.

Gate: `NEXUS_V2_STRATEGY_PORTFOLIO_OK`

### Phase 7G — Grid Trading Desk

Design and certify Grid as a dedicated trading direction, not merely a normal StrategyPlugin.

Deliver:

- GridProgram/GridInstance/GridCycle lifecycle;
- independent capital/risk budget;
- canonical grid order/fill ownership;
- grid-specific reconciliation/restart recovery;
- regime-aware configuration/recentering;
- realistic grid simulation including maker/taker costs and execution assumptions;
- dedicated GridPnL attribution reconciled to the canonical ledger;
- multi-user Grid Control Plane;
- DEMO/shadow evidence before any live cutover.

Gate: `NEXUS_V2_GRID_TRADING_DESK_OK`

### Phase 8 — Intelligence V2

Deliver canonical market data, data-quality/freshness, regime, liquidity, funding/OI, news/events and MarketContext.

Gate: `NEXUS_V2_INTELLIGENCE_OK`

### Phase 9 — AIEA V2

Migrate and harden existing AIEA functions into a coherent research platform:

- dataset/feature lineage;
- hypotheses;
- experiments;
- backtest;
- falsification;
- OOS/WF;
- paper/shadow;
- comparison;
- model/strategy registry;
- promotion/rollback;
- drift/freshness;
- isolated automated R&D worker.

Gate: `NEXUS_V2_AIEA_OK`

### Phase 10 — Multi-user / Settings / Security V2

Deliver workspace/roles, tenant isolation, secrets layer, hierarchical settings, user-scoped background jobs/events and generic audit trail.

Gate: `NEXUS_V2_MULTI_USER_SECURITY_OK`

### Phase 11 — Control Plane V2

Deliver modern UI with operational trading, risk, reconciliation, venue, AIEA and admin surfaces.

Gate: `NEXUS_V2_CONTROL_PLANE_OK`

### Phase 12 — CI/CD and production packaging

Deliver immutable images, GHCR publishing, SBOM, attestations, deploy manifests, backup/rollback runbooks and no-build-on-production enforcement.

Gate: `NEXUS_V2_RELEASE_PIPELINE_OK`

### Phase 13 — Venue certification

Sequence:

1. BingX DEMO
2. Binance USD-M test environment
3. Bybit demo/test
4. OKX demo
5. P1 venues one by one

Each venue passes the common adapter/reconciliation/execution contract suite plus venue-specific edge cases.

Gate per venue: `NEXUS_V2_VENUE_<VENUE>_CERTIFIED_OK`

### Phase 14 — End-to-end simulation and shadow parallel run

New V2 runs alongside legacy without additional live permission.

Compare:

- signals/intents;
- risk decisions;
- order intent;
- positions;
- fills/reconciliation;
- PnL attribution;
- execution quality;
- failures/stale states.

Gate: `NEXUS_V2_SHADOW_PARITY_OK`

### Phase 15 — Cutover readiness review

Requires:

- functional inventory parity;
- all mandatory test gates;
- production backup/restore drill;
- rollback image/digest;
- secret migration plan;
- DB migration rehearsal;
- security review;
- explicit user authorization.

Gate: `NEXUS_V2_CUTOVER_READY`

### Phase 16 — Controlled production cutover

Separate explicit authorization required.

No AI live boundary is automatically expanded by Core cutover.

Gate: `NEXUS_V2_PRODUCTION_CUTOVER_OK`

### Phase 17 — Legacy retirement

Only after stable verified V2 production period:

- archive source outside production;
- preserve Git history/tag;
- preserve DB backup and migration record;
- preserve old image digest;
- remove legacy runtime artifacts from the small server only after rollback policy allows it.

Gate: `NEXUS_V10_LEGACY_RETIRED_OK`

---

## 18. Performance priorities

Optimize correctness before micro-latency, but design for scale:

- async I/O;
- bounded queues/backpressure;
- batched DB writes where safe;
- indexed canonical ledgers;
- no blocking research work in production event loop;
- incremental projections;
- private WS primary + REST reconciliation fallback;
- separate hot runtime state from large historical research data;
- profile before introducing Rust/native extensions.

Rust/Cython/native code is allowed later only for measured hotspots, not as an architectural shortcut.

---

## 19. Trading-quality scorecard

NEXUS must measure whether it trades well rather than infer quality from backtest PnL.

Core execution KPIs:

- submit→ack latency;
- fill latency;
- expected vs realized slippage;
- reject rate;
- unknown outcome rate;
- partial-fill recovery rate;
- reconciliation discrepancy rate/time-to-resolve;
- stale data incidence;
- venue availability;
- protection integrity;
- restart recovery success.

Strategy/AIEA KPIs:

- OOS expectancy;
- profit factor;
- drawdown;
- Sharpe/Sortino where meaningful;
- turnover/cost sensitivity;
- regime stability;
- parameter sensitivity;
- capacity/liquidity;
- calibration;
- degradation/drift;
- challenger vs champion lift.

Portfolio KPIs:

- NAV/drawdown;
- gross/net exposure;
- leverage/margin utilization;
- concentration;
- correlated exposure;
- strategy contribution;
- venue/account exposure.

---

## 20. Non-negotiable safety invariants

1. No AI direct exchange access.
2. No new exposure without Risk + execution safety gates.
3. Closing/reducing risk remains possible when new exposure is disabled.
4. Unknown execution outcomes are explicit, never silently treated as failures/successes.
5. Reconciliation must run after restart before live strategy execution.
6. No destructive reconciliation without approved policy.
7. No raw exchange payloads in canonical business logic.
8. No secret material in logs.
9. No production source builds.
10. No legacy deletion without verified rollback/archive.
11. No strategy promotion based only on in-sample/backtest performance.
12. No user/tenant cross-contamination in DB, cache, events or UI.

---

## 21. GitHub reference URLs

Core/execution:

- https://github.com/nautechsystems/nautilus_trader
- https://github.com/hummingbot/hummingbot
- https://github.com/QuantConnect/Lean
- https://github.com/vnpy/vnpy
- https://github.com/ccxt/ccxt

AIEA/research:

- https://github.com/microsoft/qlib
- https://github.com/microsoft/RD-Agent
- https://github.com/freqtrade/freqtrade
- https://github.com/polakowo/vectorbt
- https://github.com/AI4Finance-Foundation/FinRL

These repositories are references. Any runtime dependency or source reuse requires a separate technical/license/security decision.

---

## 22. Definition of success

NEXUS V2 is successful when:

- functional inventory parity is closed;
- deterministic Core V2 owns production trading lifecycle;
- multi-user isolation is proven;
- at least the P0 venue set follows one adapter contract, with venue certification evidence;
- startup and continuous reconciliation are reliable;
- pair-native execution is restart/recovery safe;
- AIEA can autonomously research and evaluate candidates without direct production authority;
- the Control Plane exposes complete trading, risk, reconciliation, intelligence and AIEA state;
- production is deployed from verified immutable images;
- legacy NEXUS can be removed from the small server without loss of function and with an external rollback archive.

---

## 23. Immediate next step after approval

Do **not** start coding Phase 3 or move files yet.

First commit this Master Plan and Functional Inventory into the new/private GitHub work area and register the architecture transition in `NEXUS_PROJECT_AUDIT.md` with status `ARCHITECTURE/ROADMAP APPROVED`, not `DONE` for implementation.

Then execute Phase 0 one step at a time, beginning with the repository/CI/contracts baseline.
