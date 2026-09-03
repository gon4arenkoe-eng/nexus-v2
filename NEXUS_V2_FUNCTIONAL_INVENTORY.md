# NEXUS V2 — Functional Capability Inventory

**Version:** 1.0-draft  
**Date:** 2026-09-03  
**Purpose:** Prevent functional loss during the migration from legacy NEXUS V10 to NEXUS V2.

## 0. Evidence basis and status semantics

This inventory is based on three evidence classes:

1. **Legacy source snapshot** `nexus_snapshot2.tar.gz` — source-level evidence of the existing V10 platform. The snapshot is a baseline and may be older than the live server.
2. **Current server read-backs supplied on 2026-09-03** — evidence for the latest `trading_core/` and current Audit sections discussed during the Phase 2/3 work.
3. **Current Audit decisions supplied in the session** — especially the Trading Core V2 roadmap, VenueAdapter design, Ledger completion, multi-venue gap audit, and Phase 3 reconciliation requirements.

Status labels:

- `OBSERVED` — present in the legacy snapshot.
- `AUDIT VERIFIED` — explicitly evidenced by current Audit/read-back.
- `PARTIAL` — capability exists but architecture/coverage is incomplete.
- `PLANNED` — canonical direction exists but runtime implementation is not complete.
- `MISSING` — required for V2, not established as implemented.

Migration actions:

- `KEEP` — preserve the implementation or behavior with minimal change.
- `WRAP` — retain implementation behind a new canonical boundary.
- `EXTEND` — preserve and expand.
- `REBUILD` — keep the functional requirement, replace implementation.
- `REPLACE` — retire old ownership after verified canonical replacement.
- `NEW` — new V2 capability.
- `DEPRECATE` — retain only for historical/rollback value until retirement.

---

## 1. Product / multi-user shell

| Capability | Current evidence | Current status | V2 action | Canonical V2 owner | Parity / acceptance gate |
|---|---|---:|---|---|---|
| User registration | `/api/auth/register`, `User` model | OBSERVED | REBUILD/EXTEND | Control Plane + Identity | registration tests, validation, rate limits |
| Login / JWT | `/api/auth/login`, refresh/logout/me | OBSERVED | REBUILD/EXTEND | Identity/API | auth integration + expiry/refresh tests |
| Admin role | `User.is_admin`, admin routes | OBSERVED | EXTEND | Identity/RBAC | role matrix tests |
| Multi-user DB ownership | `user_id` across Exchange, Position, TradeHistory, AIEA models | OBSERVED/PARTIAL | EXTEND | Shared tenancy contract | tenant-isolation test suite |
| Multiple exchanges per user | `User.exchanges`, Exchange table | OBSERVED | KEEP/EXTEND | Core Account/Venue | per-user account isolation tests |
| Workspace/tenant abstraction | not established | MISSING | NEW | Identity | explicit tenant/workspace ownership |
| RBAC beyond admin/user | not established | MISSING | NEW | Identity | Owner/Admin/Trader/Viewer policy tests |
| User preferences | basic settings exist | PARTIAL | REBUILD | Settings service/domain | versioned per-user settings |
| User-scoped realtime events | current WS not proven user-scoped | PARTIAL | REBUILD | Control Plane Event Gateway | auth + tenant isolation WS tests |
| Audit trail for user actions | AI audit exists; generic product audit incomplete | PARTIAL | EXTEND | Audit/Event layer | actor/action/resource immutable audit |

## 2. Exchange / venue capabilities

| Capability | Current evidence | Current status | V2 action | Canonical V2 owner | Gate |
|---|---|---:|---|---|---|
| BingX client | `clients/bingx.py` | OBSERVED | WRAP | `BingXVenueAdapter` | contract + DEMO certification |
| Binance client | `clients/binance.py` | OBSERVED | WRAP/EXTEND | `BinanceVenueAdapter` | sandbox/read/write certification |
| Bybit client | `clients/bybit.py` | OBSERVED | WRAP/EXTEND | `BybitVenueAdapter` | demo/read/write certification |
| OKX client | `clients/okx.py` | OBSERVED | WRAP/EXTEND | `OKXVenueAdapter` | demo/read/write certification |
| Bitget | absent in snapshot | MISSING | NEW | Venue adapter | capability certification |
| Gate.io | absent in snapshot | MISSING | NEW | Venue adapter | capability certification |
| KuCoin Futures | absent in snapshot | MISSING | NEW | Venue adapter | capability certification |
| Hyperliquid | absent in snapshot | MISSING | NEW | Venue adapter | capability certification |
| Venue capability discovery | `VenueCapabilities` in current V2 | AUDIT VERIFIED | KEEP/EXTEND | Core Venue port | capability contract tests |
| Order request/result normalization | current V2 `VenueOrderRequest/Result/State` | AUDIT VERIFIED | KEEP | Core Venue port | existing focused tests + adapter tests |
| Position observation | planned `VenuePosition`, not implemented | PLANNED | NEW | Core Venue port | canonical position contract tests |
| Account observation | planned `VenueAccountState`, not implemented | PLANNED | NEW | Core Venue port | account/balance contract tests |
| Fill/trade observation | persistence exists but venue observation contract not confirmed | MISSING | NEW | Core Venue port | fill identity/dedup tests |
| REST order query | strongest in BingX | PARTIAL | EXTEND | Venue adapter | per-venue capability tests |
| Open-order query | strongest in BingX | PARTIAL | EXTEND | Venue adapter | per-venue capability tests |
| Private WebSocket/user stream | not canonical | PARTIAL | NEW/EXTEND | Venue adapter runtime | reconnect/gap/replay tests |
| Hedge/one-way mode | legacy exchange-specific | PARTIAL | REBUILD | Venue adapter + canonical mode | mode identity tests |
| Sandbox/demo mode | legacy exchange model `is_demo` | OBSERVED | EXTEND | Venue account config | explicit environment contract |
| Exchange credential encryption | encrypted fields exist | OBSERVED | KEEP/REBUILD | Secret management | no-plaintext/no-log security tests |
| Credential log safety | snapshot prints decrypted key prefixes | SECURITY GAP | REPLACE | Secret management | zero secret material in logs |

## 3. Trading Core / execution lifecycle

| Capability | Current evidence | Current status | V2 action | Canonical V2 owner | Gate |
|---|---|---:|---|---|---|
| `TradeIntent` | current V2 | AUDIT VERIFIED | KEEP | Core domain | contract tests |
| Venue/Account/Instrument identity | current V2 identities | AUDIT VERIFIED | KEEP/EXTEND | Core domain | identity invariants |
| ExecutionPlan | current V2 persistence/domain work | AUDIT VERIFIED | KEEP | Core execution | persistence/replay tests |
| PositionGroup | current V2 | AUDIT VERIFIED | KEEP | Core ledger | group lifecycle tests |
| PositionLeg | current V2 | AUDIT VERIFIED | KEEP | Core ledger | leg lifecycle tests |
| ExecutionOrder | current V2 | AUDIT VERIFIED | KEEP | Core ledger | local/venue state tests |
| ExecutionFill | current V2 persistence | AUDIT VERIFIED | KEEP/EXTEND | Core ledger | fill dedup/replay tests |
| Immutable ledger events | current Phase 2 evidence | AUDIT VERIFIED | KEEP/EXTEND | Core event ledger | deterministic replay |
| Local vs venue order state | current Phase 2 evidence | AUDIT VERIFIED | KEEP | Core ledger/reconciliation | state separation tests |
| Idempotency | legacy SentOrder + V2 canonical ownership | PARTIAL→V2 VERIFIED | KEEP V2 | Execution Coordinator | replay/race/idempotency tests |
| Global new-order kill switch | `ExecutionBoundary` | OBSERVED | KEEP/REBUILD | Core execution safety | fail-closed tests |
| Risk-reducing close while kill switch active | `ExecutionBoundary.close_position` | OBSERVED | KEEP invariant | Core execution safety | safety regression test |
| ExecutionCoordinator | roadmap requirement | MISSING | NEW | Core application | state-machine + restart E2E |
| PairExecutionCoordinator | roadmap requirement | MISSING | NEW | Core application | partial-fill/recovery E2E |
| Basket execution | planned by ownership shape | MISSING | NEW later | Core application | basket lifecycle tests |
| Unknown command outcome handling | not canonical | MISSING | NEW | Core execution/reconciliation | timeout-after-submit fault tests |
| Startup recovery before strategy activation | not canonical | MISSING | NEW | Core lifecycle | restart/reconciliation gate |
| Continuous reconciliation | not implemented in Core V2 | MISSING | NEW | Reconciliation Engine | repeated deterministic reconcile |
| External/unknown venue order detection | Phase 3 requirement | PLANNED | NEW | Reconciliation Engine | discrepancy tests |
| Missing local fill detection | Phase 3 requirement | PLANNED | NEW | Reconciliation Engine | fill recovery tests |
| Stale local position detection | Phase 3 requirement | PLANNED | NEW | Reconciliation Engine | position discrepancy tests |

## 4. Legacy reconciliation / protection behavior that must not be lost

| Behavior | Current evidence | Migration action | V2 destination |
|---|---|---|---|
| Exchange→DB position synchronization | `PositionAgent` | EXTRACT behavior | Reconciliation Engine |
| Hedge identity `(symbol, side)` | `PositionAgent` | CANONICALIZE | `VenuePosition` / Position identity |
| Orphaned local position detection | `PositionAgent` | EXTRACT detection only | Reconciliation Engine |
| SL/TP close-reason inference | `PositionAgent` order lookups | REBUILD over canonical observations | Reconciliation/attribution |
| Restart SL/TP intent recovery | `PositionAgent` | KEEP invariant | Recovery policy |
| Protection drift detection | `_reconcile_protection_orders` | EXTRACT observation | Reconciliation Engine |
| Create-new-before-remove-old protection | `_reconcile_protection_orders` | KEEP safety invariant | Execution/Recovery Coordinator |
| Duplicate protection cleanup | `_reconcile_protection_orders` | MOVE | Execution/Recovery Coordinator |
| Direct `Position` mutation/commit | `PositionAgent` | DO NOT COPY | Core application/ledger owns writes |
| Direct TradeHistory creation | `PositionAgent` | DO NOT COPY | Attribution/reporting pipeline |

## 5. Risk management

| Capability | Current evidence | Status | V2 action | V2 owner | Gate |
|---|---|---:|---|---|---|
| Max concurrent positions | BotSettings + AIRiskAgent | OBSERVED | KEEP policy / REBUILD owner | Portfolio Risk | portfolio tests |
| Daily loss limit | AIRiskAgent | OBSERVED | KEEP/EXTEND | Portfolio Risk | loss limit tests |
| Position sizing | AIRiskAgent | OBSERVED | KEEP proven logic initially | SingleLegRiskPolicy | parity tests |
| Dynamic leverage | AIRiskAgent | OBSERVED | KEEP/EXTEND | Risk policy | cap/volatility tests |
| ATR volatility guards | AIRiskAgent | OBSERVED | KEEP | Risk policy | deterministic tests |
| Regime/trend guard | AIRiskAgent | OBSERVED | KEEP/EXTEND | Risk policy | regime tests |
| Volume/liquidity guard | AIRiskAgent | OBSERVED | EXTEND | Risk + Intelligence | liquidity tests |
| OOS production guard | AIRiskAgent | OBSERVED | KEEP concept / REBUILD | Promotion/Risk gate | dataset lineage tests |
| Portfolio gross/net exposure | not canonical | MISSING | NEW | PortfolioRiskEngine | exposure limits |
| Venue/account exposure | planned | MISSING | NEW | PortfolioRiskEngine | per-venue/account tests |
| Correlation/concentration risk | not canonical | MISSING | NEW | PortfolioRiskEngine | scenario tests |
| Pair/basket hedge integrity | roadmap | MISSING | NEW | PortfolioRisk + coordinator | hedge ratio tests |
| Drawdown/circuit breaker | partial legacy | PARTIAL | EXTEND | Core safety | portfolio DD gate |

## 6. Strategy functionality

### Legacy registry observed

`trend_pullback`, `smc`, `ema_cross`, `scalping`, `bollinger_squeeze`, `mean_reversion`, `trend_following_chop`, `statistical_arbitrage`, `breakout`, `range_trading`, `liquidity_sweep`, `order_block`, `fair_value_gap`, `volume_profile`, `funding_oi`, `volatility_expansion`, `grid_combo`.

| Capability | Status | V2 action | Gate |
|---|---:|---|---|
| Strategy registry | OBSERVED | REBUILD as versioned Strategy Catalog | catalog/version tests |
| Strategy result normalization | OBSERVED | REPLACE with canonical intent contract | intent contract tests |
| DecisionEngine | OBSERVED | REBUILD/EXTEND | deterministic decision tests |
| Regime-aware strategy selection | OBSERVED/PARTIAL | EXTEND | regime slice validation |
| Grid strategy | OBSERVED | KEEP functional parity, redesign ownership | Grid DEMO E2E |
| StatArb legacy | OBSERVED but legacy | DEPRECATE after V2 cutover | StatArb V2 pair-native gate |
| StatArb V2 research stack | AUDIT VERIFIED | KEEP/INTEGRATE | canonical pair integration |
| Funding/OI strategy | OBSERVED | REVALIDATE | cost/OOS/WF evidence |
| Every other legacy strategy | OBSERVED | REVALIDATE before V2 activation | no strategy auto-promoted by parity alone |
| Strategy versioning | AIEA model exists | PARTIAL | EXTEND | immutable version + artifact hash |
| Same strategy contract in backtest/shadow/live | roadmap | MISSING | NEW | parity test suite |

## 7. Market Intelligence

| Capability | Current evidence | Status | V2 action | Owner |
|---|---|---:|---|---|
| Market scanning | `market/scanner.py`, agents | OBSERVED | REBUILD/EXTEND | Intelligence |
| Dynamic symbol universe | legacy runtime work | PARTIAL | EXTEND | Intelligence |
| OHLCV normalization | clients/services | PARTIAL | REBUILD | Intelligence data contracts |
| Regime detection | `market_regime_agent`, strategy detector | OBSERVED | REBUILD/EXTEND | Intelligence |
| Volatility/ATR context | agents/risk | OBSERVED | EXTEND | Intelligence |
| Volume context | agents/risk | OBSERVED | EXTEND | Intelligence |
| Sentiment | `sentiment_agent` | OBSERVED/PARTIAL | REVALIDATE | Intelligence |
| Funding/open interest | strategy/client pieces | PARTIAL | EXTEND | Intelligence |
| Order book/liquidity | partial/not canonical | MISSING/PARTIAL | NEW | Intelligence |
| News/Event ingestion | AIEA B5 | AUDIT VERIFIED | KEEP/EXTEND | Intelligence + AIEA |
| Historical event registry | infrastructure exists | PARTIAL | EXTEND later | Intelligence/AIEA |
| On-chain/whale | approved/backlog, not verified | PLANNED | NEW later | Intelligence |
| Data quality | `AIDataQualityEngine` | OBSERVED | KEEP/EXTEND | Intelligence/AIEA |
| Canonical MarketContext | partial `MarketStateBuilder` | PARTIAL | REBUILD | Intelligence contract |
| Time sync/gap detection | not established | MISSING | NEW | Intelligence ingestion |

## 8. AIEA — AI Evolution & Experimentation Architecture

| Capability | Current evidence | Status | V2 action | Gate |
|---|---|---:|---|---|
| AI agent registry | `AIAgent` | OBSERVED | EXTEND | version/config ownership |
| Knowledge snapshots | model/service | OBSERVED | KEEP/EXTEND | reproducible snapshot hash |
| AI memory / lessons | `AIMemoryService`, `AILesson` | OBSERVED | KEEP/EXTEND | provenance tests |
| Hypothesis generation | `AIHypothesisEngine` | OBSERVED | KEEP/REBUILD interface | hypothesis schema tests |
| Experiment engine | `AIExperimentEngine` | OBSERVED | KEEP/EXTEND | isolated execution |
| Historical dataset builder | services | OBSERVED | KEEP/EXTEND | dataset lineage |
| Candle backtesting | services | OBSERVED | KEEP/EXTEND | deterministic engine/parity |
| Cost/execution simulation | `ai_backtest_execution` | OBSERVED | EXTEND | fees/slippage/funding model |
| Metrics | `ai_backtest_metrics` | OBSERVED | EXTEND | standardized scorecard |
| Static validation | service | OBSERVED | KEEP | syntax/import/safety tests |
| OOS validation | `AIOOSValidator` | OBSERVED | KEEP/EXTEND | contamination-free split |
| Walk-forward validation | `AIWalkForwardValidator` | OBSERVED | KEEP/EXTEND | rolling windows |
| Shadow walk-forward | service | OBSERVED | KEEP/EXTEND | shadow evidence |
| Paper trading | model/service | OBSERVED | KEEP/EXTEND | realistic execution model |
| Strategy signal replay | service | OBSERVED | KEEP/EXTEND | deterministic replay |
| Comparison alignment | services | OBSERVED | KEEP/EXTEND | aligned cohorts |
| Comparison metrics/slices | services | OBSERVED | KEEP/EXTEND | regime/symbol/side slices |
| Stability scoring | services/models | OBSERVED | KEEP/EXTEND | minimum window/sample policy |
| Shadow quality | services/models | OBSERVED | KEEP/EXTEND | quality thresholds |
| Shadow advisory calibration | services/models | OBSERVED | KEEP/EXTEND | calibration gate |
| Predictive advisory analysis | services/models | OBSERVED | KEEP/EXTEND | lift vs baseline |
| News context comparison | service | OBSERVED | KEEP/EXTEND | event-conditioned scorecard |
| Validation evidence ledger | model/service | OBSERVED | KEEP/EXTEND | content hashes/provenance |
| Promotion readiness/gates | services | OBSERVED | KEEP/EXTEND | explicit state machine |
| Risk approval | service/model fields | OBSERVED | KEEP | independent risk gate |
| Permission gate | service | OBSERVED | KEEP | user/admin policy |
| Promotion audit | service | OBSERVED | KEEP | immutable audit |
| Rollback | service | OBSERVED | KEEP/EXTEND | deterministic rollback |
| Production safety | service | AUDIT-IMPORTANT | KEEP invariant | AI direct exchange blocked |
| Automated R&D loop | partial | PARTIAL | EXTEND using RD-Agent/Qlib patterns | sandbox + bounded loop |
| Model registry/artifact store | partial strategy versions only | MISSING/PARTIAL | NEW | model hash + dataset lineage |
| Model drift/freshness | partial shadow stability | PARTIAL | EXTEND | drift policy |
| False discovery / multiple hypothesis control | StatArb research only | PARTIAL | EXTEND platform-wide | research gate |
| Research compute isolation | conceptually required | PARTIAL | NEW | off-production workers |

## 9. Dashboard / Control Plane / UX

| Capability | Current evidence | Status | V2 action | Gate |
|---|---|---:|---|---|
| Dashboard overview | HTML/JS + `/api/dashboard` | OBSERVED | REBUILD/EXTEND | responsive E2E |
| Dark visual theme | current dashboard CSS | OBSERVED | KEEP design intent / redesign | design system |
| Responsive layout | CSS media queries | OBSERVED | EXTEND | mobile/tablet/desktop QA |
| Positions table | UI/API | OBSERVED | EXTEND | real-time position events |
| PnL/equity chart | UI/API | OBSERVED | EXTEND | authoritative ledger data |
| Strategy controls | UI/API | OBSERVED | REBUILD | versioned strategy instances |
| Exchange management | UI/API | OBSERVED | REBUILD/EXTEND | account-scoped controls |
| DEMO/REAL mode UI | observed | OBSERVED | REBUILD with stronger safety | explicit permission gates |
| Grid UI | observed | OBSERVED | KEEP/REBUILD | parity before retirement |
| Agents status | UI/API | OBSERVED | REPLACE with service/component health | health model |
| Signals feed | UI/API | OBSERVED | EXTEND | typed events |
| Logs view | UI/API | OBSERVED | EXTEND | user-safe structured logs |
| History/stats | UI/API | OBSERVED | EXTEND | canonical ledger analytics |
| Stash | UI/API/model | OBSERVED | DECIDE/KEEP if product requirement remains | explicit business decision |
| Settings screen | UI markup exists; persistence incomplete | PARTIAL | REBUILD | versioned settings API |
| Notifications settings | UI hints, backend unclear | PARTIAL | REBUILD | actual persisted channels |
| Risk settings | UI + BotSettings partial | PARTIAL | REBUILD | hierarchical risk config |
| Reconciliation console | roadmap requirement | MISSING | NEW | discrepancies + last run + actions |
| AIEA Research Center | not present in legacy UI | MISSING | NEW | experiments/candidates/evidence |
| Model/strategy promotion UI | not present | MISSING | NEW | permissioned approval workflow |
| Multi-user admin console | limited admin endpoints | PARTIAL | EXTEND | tenants/users/roles/audit |
| Accessibility | not established | MISSING | NEW | keyboard/contrast/ARIA QA |

## 10. API / realtime / integration

| Capability | Current evidence | Status | V2 action | Gate |
|---|---|---:|---|---|
| FastAPI runtime | `app_fastapi.py` | OBSERVED | KEEP/REBUILD composition | single canonical app factory |
| Duplicate legacy app entrypoint | `main.py` exists | OBSERVED | DEPRECATE | one runtime entrypoint |
| REST API | 16 router modules | OBSERVED | EXTEND/version | OpenAPI contract tests |
| `/ws/metrics` | current WebSocket | OBSERVED/PARTIAL | REPLACE | authenticated typed event stream |
| API versioning | not established | MISSING | NEW | `/api/v2` contract policy |
| Idempotent command API | partial | MISSING/PARTIAL | NEW | idempotency key contract |
| Pagination/filtering | inconsistent | PARTIAL | REBUILD conventions | API contract tests |
| Structured errors | inconsistent dicts | PARTIAL | REBUILD | canonical error schema |

## 11. Persistence / data / infrastructure

| Capability | Current evidence | Status | V2 action | Gate |
|---|---|---:|---|---|
| PostgreSQL | current runtime | OBSERVED | KEEP | migrations/backups |
| SQLAlchemy async | current stack | OBSERVED | KEEP | transaction discipline |
| Alembic | current | OBSERVED/AUDIT VERIFIED | KEEP | single-head migration gate |
| Redis | current runtime | OBSERVED | KEEP/EXTEND | cache/event transport tests |
| Nginx | current | OBSERVED | KEEP/RECONFIGURE | TLS/proxy tests |
| Docker Compose | current | OBSERVED | REBUILD production compose | immutable image deploy |
| GitHub Actions | legacy `.github/workflows/ci.yml` | OBSERVED | REBUILD/EXTEND | required CI matrix |
| No-build-on-production | not current | MISSING | NEW invariant | prod uses registry images only |
| GHCR images | not established | MISSING | NEW | tagged + digest deployment |
| Build provenance/attestation | not established | MISSING | NEW | GitHub artifact attestation |
| Dependency update automation | not established | MISSING | NEW | Dependabot/security policy |
| SBOM | not established | MISSING | NEW | generated per release |
| Research dataset storage | likely local/DB | PARTIAL | REBUILD | object storage/off-prod |
| Model artifact storage | not canonical | MISSING | NEW | model registry/object store |
| Transactional backup/restore | backups exist | PARTIAL | EXTEND | restore drill |
| Observability | logs/health partial | PARTIAL | REBUILD | metrics/traces/alerts |

## 12. Functional parity rule for legacy retirement

A legacy capability may be retired only when all applicable gates are true:

1. V2 target owner is implemented.
2. Unit/contract tests pass.
3. Persistence/restart behavior is verified where relevant.
4. Multi-user isolation is verified.
5. Security checks pass.
6. DEMO/shadow evidence exists for exchange-touching behavior.
7. UI/API parity exists if the legacy capability was user-facing.
8. Rollback is documented and tested.
9. The result is written to `NEXUS_PROJECT_AUDIT.md` with an evidence tag.

No historical code/data is automatically deleted.

---

## 13. Highest-priority gaps revealed by the inventory

1. Canonical Reconciliation Engine and venue observation contracts.
2. ExecutionCoordinator / PairExecutionCoordinator.
3. Portfolio-level risk ownership.
4. Canonical typed event model and authenticated event delivery.
5. Startup recovery before strategy activation.
6. Full multi-user tenancy/RBAC/settings architecture.
7. V2 Control Plane including reconciliation and AIEA views.
8. Off-production research/model/data infrastructure for AIEA.
9. Production-grade multi-venue adapter certification.
10. CI/CD supply-chain hardening and immutable image deployment.

---

## 14. Inventory maintenance rule

This file is a capability map, not the source of current-state truth.

- `NEXUS_V2_MASTER_PLAN.md` defines the forward roadmap.
- `NEXUS_PROJECT_AUDIT.md` remains the authoritative record of what is actually VERIFIED/DONE.
- Before retiring any legacy module, this inventory must be updated with the V2 replacement and evidence tag.

## 15. Strategy Portfolio and Grid Trading inventory

### 15.1. Current legacy strategy candidate pool

Snapshot inspection shows the registry currently exposes 17 strategy entries, spanning trend, momentum, mean-reversion/range, breakout/volatility, liquidity/SMC-style signals, funding/OI, statistical arbitrage and `grid_combo`. V2 will not assume all 17 deserve independent production status. They are research candidates to be clustered by economic hypothesis and benchmarked before certification.

Required migration classification for every legacy strategy:

- KEEP AS FAMILY CANDIDATE;
- MERGE/CONSOLIDATE;
- REBUILD;
- RESEARCH ONLY;
- DEPRECATE.

Each classification requires evidence from code review, costs-aware backtests, OOS/walk-forward, parameter stability, cross-market robustness and comparison with mature reference implementations.

### 15.2. Grid current-state interpretation

The legacy snapshot contains both a `grid_combo` strategy-level signal generator and a separate `GridAgent` that owns grid state/order synchronization/management. This is evidence that Grid already behaves as more than a conventional one-shot entry/exit strategy. V2 therefore treats Grid as a dedicated trading program candidate.

V2 Grid capability inventory:

| Capability | V2 action | Required evidence |
|---|---|---|
| Grid setup/range/levels | REBUILD | deterministic configuration tests |
| Regime-aware grid mode | KEEP/RESEARCH | OOS regime attribution |
| Grid state lifecycle | REBUILD | restart/replay tests |
| Grid order inventory | REBUILD on canonical ledger | order/fill reconciliation |
| Replenishment/recenter | RESEARCH/REBUILD | realistic execution simulation |
| Grid capital allocation | NEW | portfolio-risk integration |
| Grid risk budget | NEW | exposure/drawdown tests |
| Grid PnL | NEW canonical attribution | fill-to-grid reconciliation, no double count |
| Multi-user grid ownership | NEW | tenant isolation tests |
| Grid UI | REBUILD | user-scoped E2E |
| Grid research/backtest | REBUILD | fees/slippage/latency/adverse-selection assumptions |
| DEMO/shadow certification | NEW gate | venue evidence |

### 15.3. Strategy quality principle

Target production strategy count is not a KPI. The target is a diversified set of distinct, robust edges with measurable incremental contribution after costs. AIEA owns research comparison and candidate evidence; Core V2 owns deterministic runtime/risk/execution.
