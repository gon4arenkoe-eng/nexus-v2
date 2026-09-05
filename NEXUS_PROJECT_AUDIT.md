# NEXUS PROJECT AUDIT

> **CANONICAL LIVE PROJECT STATE**
>
> Единственный рабочий документ фактического состояния,
> архитектурной карты, evidence и следующего шага NEXUS.

Audit rebuild date: 2026-08-27 17:27:49

## 0. CANONICAL WORK PROTOCOL

### 0.1. Главный принцип

**ONE PROJECT → ONE LIVE AUDIT → ONE CURRENT STATE → ONE NEXT STEP**

`NEXUS_PROJECT_AUDIT.md` является единственной рабочей точкой синхронизации фактического состояния проекта.

### 0.2. Обязательная цепочка

**FACT → CHECK → EVIDENCE → AUDIT → STATUS → NEXT STEP**

### 0.3. Статусы

- `NOT STARTED`
- `IN PROGRESS`
- `PARTIALLY VERIFIED`
- `VERIFIED`
- `TEST VERIFIED`
- `DONE`
- `BLOCKED`
- `NOT DOCUMENTED`

### 0.4. Правила

- Не считать код доказательством без проверки.
- Не считать старую запись доказательством без соответствующего evidence.
- Не повторять уже подтверждённые проверки без новой технической причины.
- Новые требования добавлять в соответствующий раздел.
- Архитектурные изменения сначала согласовывать с пользователем.
- Не удалять исторические документы автоматически.

## 1. CURRENT VERIFIED STATE

### 1.1. Уже подтверждённые крупные результаты

- `BLOCK A / A8` — TEST VERIFIED / DONE
- `BLOCK D / D.1–D.6.8` — DONE
- `BLOCK E / E.1–E.12` — DONE
- `BLOCK F / F.1–F.9` — DONE + REVIEWED

### 1.2. Current active work

- `A9` — TEST VERIFIED / DONE
- `B.5 News / Event Correlation` — TEST VERIFIED / DONE
- No new implementation item is active until the next uncompleted Audit item is factually mapped.

### 1.3. A8 evidence

- `A8_TWO_IDENTITY_CHAINS_CREATED_OK`
- `A8_SAME_USER_CHAINS_OK`
- `A8_CROSS_USER_SNAPSHOT_BLOCKED_OK`
- `A8_CROSS_USER_EXPERIMENT_TAMPER_BLOCKED_OK`
- `A8_CROSS_USER_EVIDENCE_BLOCKED_OK`
- `A8_SAME_USER_EVIDENCE_OK`
- `A8_IDENTITY_CHAINS_REMAIN_ISOLATED_OK`
- `A8_PRODUCTION_ISOLATION_OK`

### 1.4. BLOCK D evidence

- `D.1–D.6.8 completed`
- `D6_8_BLOCK_D_FULL_COMPILE_OK`

### 1.5. Production execution boundary

```text
SignalAgent
    ↓
StrategyDecisionEngine
    ↓
AIRiskAgent
    ↓
ExecutionAgent
    ↓
ExecutionBoundary
    ↓
BaseExchangeClient
```

Status: `VERIFIED`

### 1.6. Production protection fail-safe

После открытия позиции защита проверяется фактически через `get_open_orders()`. При невозможности подтвердить SL/TP используется `close_reason="PROTECTION_FAILSAFE"`.

Status: `VERIFIED`

## 2. PROJECT ARCHITECTURE MAP

Карта ниже построена непосредственно по текущей структуре `NEXUS_MASTER_PLAN.md`. Она является плановой картой до фактического сопоставления каждого пункта с implementation/evidence.

# 1. Назначение модуля

**Status:** `PARTIALLY VERIFIED`

## Canonical requirement

AIEA — отдельный исследовательско-развивающий контур NEXUS.

Он предназначен для:

- анализа исторических данных;
- формирования торговых гипотез;
- создания новых и модификации существующих стратегий;
- проведения экспериментов;
- validation;
- paper / shadow research;
- comparison;
- controlled promotion.

AIEA не должен заменять Strategy Decision Engine и Grid Engine.

## Фактически обнаруженная реализация

В проекте присутствуют отдельные AIEA-компоненты:

- `agents/ai_orchestrator.py`
- `agents/ai_risk_agent.py`
- `services/ai_knowledge_engine.py`
- `services/ai_knowledge_snapshot_service.py`
- `services/ai_hypothesis_engine.py`
- `services/ai_experiment_engine.py`
- `services/ai_memory.py`
- `services/ai_backtest_engine.py`
- `services/ai_oos_validator.py`
- `services/ai_walk_forward_validator.py`
- `services/ai_paper_trading_service.py`
- `services/ai_shadow_*`
- `services/ai_comparison_*`
- `services/ai_promotion_*`
- `services/ai_validation_evidence.py`
- `services/ai_production_safety.py`
- соответствующие `models/ai_*`.

## Что уже фактически подтверждено

- Foundation identity / isolation — A8 `TEST VERIFIED`.
- AI Memory — B4 `TEST VERIFIED`.
- Validation Engine — BLOCK D `DONE`.
- Promotion Pipeline — E.1–E.12 `DONE`.
- Comparison Engine — F.1–F.9 `DONE + REVIEWED`.
- Production execution isolation — `VERIFIED` для проверенных boundary paths.

## Что ещё не доказано полностью

Наличие компонентов само по себе не доказывает завершённость полного AIEA lifecycle.

Требуют отдельного factual audit:

- полный autonomous Evolution Loop;
- полный Strategy Generator lifecycle;
- полный Strategy Modifier lifecycle;
- полный Strategy Genome lifecycle;
- полный AI trust lifecycle;
- Restricted Live;
- Full Live;
- полный News/Event Intelligence lifecycle;
- полный Dashboard;
- полный Application / Production Security.

## Evidence

Code inventory:

- `agents/ai_orchestrator.py`
- `services/ai_knowledge_engine.py`
- `services/ai_hypothesis_engine.py`
- `services/ai_experiment_engine.py`
- `services/ai_memory.py`
- `services/ai_backtest_engine.py`
- `services/ai_comparison_*`
- `services/ai_promotion_*`
- `services/ai_production_safety.py`

Test evidence:

- A8 Foundation Isolation
- B4 AI Memory
- BLOCK D final validation
- E1–E12 Promotion
- F1–F9 Comparison

## Remaining

Полное сопоставление назначения AIEA с фактическим implementation lifecycle.

# 2. Основные цели

**Status:** `PARTIALLY VERIFIED`

## 2.1. Historical Research

- [x] Анализ исторических сделок NEXUS.
- [x] Анализ strategy × market_regime.
- [x] Анализ strategy × symbol.
- [x] Анализ strategy × side.
- [x] Анализ strategy × volatility.
- [x] Анализ strategy × confidence.
- [x] Анализ temporal dimensions.
- [x] Анализ strategy × leverage.

**Evidence:**

- `B1_REQUIRED_SLICES_OK`
- `B1_OPTIONAL_SLICES_OK`
- `B1_AGGREGATION_OK`
- `B1_HISTORICAL_ANALYSIS_OK`

## 2.2. Research / Discovery

- [x] Формирование исследовательских observations.
- [x] Выявление regime-dependent behaviour.
- [x] Выявление contrast между положительными и отрицательными режимами.
- [x] Передача observations в Hypothesis Engine.
- [ ] Полный autonomous discovery cycle — не доказан.
- [ ] Полное отделение correlation от causation — требует дальнейшего аудита.

**Evidence:**

`B2_REGIME_CONTRAST_OK`

## 2.3. Hypothesis Generation

- [x] Генерация hypothesis из knowledge snapshot.
- [x] Привязка hypothesis к user.
- [x] Привязка hypothesis к snapshot.
- [x] Сохранение expected effect.
- [x] Сохранение conditions.
- [x] Сохранение parameters.
- [x] Сохранение reasoning.
- [x] Запрет непосредственной strategy mutation в research stage.

**Evidence:**

- `B2_HYPOTHESIS_STRUCTURE_OK`
- `B2_VALIDATION_REQUIRED_OK`
- `B2_NO_STRATEGY_MUTATION_OK`
- `B2_HYPOTHESIS_RESEARCH_OK`

## 2.4. Strategy Evolution

- [ ] Полная автоматическая генерация новой strategy не доказана.
- [ ] Полная автоматическая модификация существующей strategy не доказана.
- [ ] Полный Strategy Genome lifecycle требует отдельного audit.
- [x] Strategy version infrastructure существует.
- [x] Strategy genealogy infrastructure существует.

## 2.5. Validation

- [x] Static Validation.
- [x] Backtest.
- [x] Out-of-Sample.
- [x] Walk-Forward.
- [x] Paper infrastructure.
- [x] Validation metrics.
- [x] Validation result integrity.
- [x] Production isolation.

**Evidence:**

`D6_8_BLOCK_D_FULL_COMPILE_OK`

## 2.6. Comparison

- [x] AI Strategy comparison.
- [x] Strategy Engine comparison.
- [x] Grid comparison participant.
- [x] Baseline participant.
- [x] Symbol × regime × side alignment.
- [x] PnL / win rate / profit factor / expectancy.
- [x] Drawdown / stability.
- [x] trade_source separation.
- [x] News/Event context layer.
- [x] Persistence.
- [x] Read-only production boundary.

**Evidence:**

BLOCK F `F.1–F.9` — `DONE + REVIEWED`.

## 2.7. Promotion / Trust

- [x] Promotion Manager.
- [x] Promotion State Machine.
- [x] Formal Promotion Gates.
- [x] Evidence Binding.
- [x] Risk Approval.
- [x] Permission policy.
- [x] Promotion audit.
- [x] Rollback.
- [x] Rollback integrity.
- [x] Production Safety boundary.
- [ ] Полный AI trust-level lifecycle не доказан.
- [ ] Restricted Live не активирован.
- [ ] Full Live не активирован.

**Evidence:**

E.1–E.12 test evidence.

## 2.8. AI Memory

- [x] AI lesson recording.
- [x] User-memory isolation.
- [x] Experiment ownership.
- [x] Append-only memory.
- [x] Research-memory-only boundary.

**Evidence:**

B4 evidence.

## 2.9. News & Event Intelligence

- [ ] Полный external ingestion.
- [ ] Historical event backfill.
- [ ] Event deduplication.
- [ ] Event → market linkage.
- [ ] Event → regime linkage.
- [ ] Event → strategy linkage.
- [ ] Event → outcome linkage.
- [ ] News-aware research.
- [ ] News-aware validation.
- [ ] News/Event risk enforcement lifecycle.

Статус:

`PARTIALLY VERIFIED`

## 2.10. Versioned AI History

- [x] Strategy version records.
- [x] Experiment records.
- [x] Validation evidence.
- [x] Promotion audit trail.
- [x] Rollback audit trail.
- [ ] Полная end-to-end история каждого AI observation/decision требует отдельного audit.

## 2.11. Главный результат цели

AIEA уже имеет существенную исследовательскую, validation, comparison и promotion infrastructure.

Однако полный заявленный lifecycle:

`research → hypothesis → generation → validation → paper → shadow → advisory → restricted live → live`

ещё не доказан целиком.

**Evidence:** B1/B2/B3/B4, BLOCK D, BLOCK E, BLOCK F, текущий code inventory.

**Remaining:** закрыть неподтверждённые lifecycle-компоненты отдельными factual audits.

# 3. Что AIEA НЕ должен делать

**Status:** `PARTIALLY VERIFIED`

## 3.1. Direct Exchange Execution

AIEA не должен напрямую отправлять production orders на BingX или другой exchange.

**Status:** `VERIFIED`

**Evidence:**
- `services/execution_boundary.py`
- `agents/execution_agent.py`
- E10/E12 production isolation evidence.

## 3.2. RiskAgent Bypass

AIEA не должен обходить RiskAgent.

Канонический production path:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary → Exchange`

**Status:** `VERIFIED`

**Evidence:**
- `agents/orchestrator.py`
- `agents/ai_risk_agent.py`
- `agents/execution_agent.py`
- `services/execution_boundary.py`
- E10/E12 risk-boundary evidence.

## 3.3. ExecutionAgent Bypass

AIEA auxiliary services не должны самостоятельно выполнять production execution.

**Status:** `VERIFIED` для проверенных AI paths.

**Evidence:**
- promotion services;
- validation services;
- comparison services;
- shadow/advisory services;
- E10/E12 production isolation.

## 3.4. Production Strategy Mutation

AIEA не должен переписывать существующую production strategy version.

Evolution выполняется через новую strategy version и genealogy.

**Status:** `VERIFIED` для version/promotion boundary.

**Evidence:**
- `models/ai_strategy_version.py`
- `services/ai_promotion_manager.py`
- `services/ai_promotion_rollback.py`
- E8/E9 evidence.

## 3.5. Risk Configuration Mutation

AIEA не должен самостоятельно менять:

- risk limits;
- max leverage;
- account settings;
- AI risk budget.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** полный audit configuration write-paths.

## 3.6. Self-Promotion

AIEA не может самостоятельно повышать trust/promotion level.

Promotion требует readiness, formal gates, risk approval и permission validation.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 permission tests;
- E10 permission escalation test;
- E12 promotion chain.

**Remaining:** отдельный audit `ai_agents.trust_level` lifecycle.

## 3.7. Experiment / Audit History Destruction

AIEA не должен удалять или переписывать:

- experiments;
- validation evidence;
- promotion audits;
- genealogy history.

**Status:** `TEST VERIFIED`

**Evidence:**
- E7 historical snapshot stability;
- E8 history preservation;
- E9 parent preservation.

## 3.8. Unvalidated Hypothesis / Strategy

AIEA не может считать гипотезу или strategy доказанной без обязательной validation pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_VALIDATION_REQUIRED_OK`
- `B2_NO_STRATEGY_MUTATION_OK`
- `B2_HYPOTHESIS_RESEARCH_OK`

## 3.9. Shadow / Advisory Override

Shadow/Advisory не должны:

- изменять production signal;
- менять strategy;
- менять confidence;
- блокировать execution;
- инициировать execution.

**Status:** `VERIFIED`

**Evidence:**
- `agents/signal_agent.py`
- `services/ai_shadow_advisory_influence_policy.py`

## 3.10. News/Event Risk Bypass

AIEA не должен отключать или обходить News/Event Risk controls.

**Status:** `NOT VERIFIED`

**Remaining:** полный audit `event → risk restriction → production safety`.

## 3.11. AI-Generated Code Boundary

AI-generated code не должен получать прямой production access.

Обязательны:

- sandbox isolation;
- network isolation;
- filesystem isolation;
- credentials isolation;
- production DB isolation;
- Docker/socket isolation.

**Status:** `NOT VERIFIED`

## 3.12. Итог

Основные production-boundary ограничения уже имеют фактическое или тестовое подтверждение.

Остаются:

- trust lifecycle audit;
- risk configuration write-path audit;
- News/Event Risk enforcement audit;
- AI-generated code sandbox audit;
- exhaustive AI → production negative-path audit.

**Evidence:** A8, B2, E6–E12, code audit.

# 4. Архитектурная модель

**Status:** `PARTIALLY VERIFIED`

## 4.1. Архитектурное разделение

NEXUS разделяет Strategy Decision Engine, Grid Engine, AI Evolution Agent и production Risk / Execution / Position / TradeHistory контуры.

AIEA не заменяет Strategy Decision Engine или Grid Engine.

## 4.2. Production decision path

`Market → MarketAgent → SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary → BaseExchangeClient → Exchange`

**Status:** `VERIFIED`

**Evidence:**
- `agents/orchestrator.py`
- `agents/signal_agent.py`
- `strategies/decision_engine.py`
- `agents/ai_risk_agent.py`
- `agents/execution_agent.py`
- `services/execution_boundary.py`

## 4.3. AIEA research boundary

Обнаружены отдельные контуры Knowledge, Hypothesis, Experiment, Validation, Memory, Comparison, Promotion и News/Event.

**Status:** `PARTIALLY VERIFIED`

## 4.4. Validation boundary

Validation / Backtest / OOS / Walk-Forward / Paper контуры отделены от production execution.

**Status:** `VERIFIED`

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 4.5. Comparison boundary

Comparison Engine является аналитическим контуром.

`Comparison Observation != Trade`

**Status:** `TEST VERIFIED`

**Evidence:** BLOCK F `F.1–F.9` + review.

## 4.6. Promotion boundary

`Experiment → Readiness → Formal Gate → Risk Approval → Permission Policy → Promotion Manager → Strategy Version`

**Status:** `TEST VERIFIED`

**Evidence:** E.1–E.12.

## 4.7. Production safety boundary

`ExecutionBoundary` является технической границей перед exchange execution и выполняет safety / permission / trading-control checks до `place_order()`.

**Status:** `VERIFIED`

**Evidence:**
- `services/execution_boundary.py`
- `services/ai_production_safety.py`
- E10/E12 evidence.

## 4.8. Не полностью подтверждено

- полный autonomous AIEA evolution loop;
- полный News/Event Intelligence;
- Dynamic Market Universe;
- Restricted Live;
- Full Live;
- trust-level lifecycle;
- AI-generated code sandbox lifecycle;
- полный Dashboard.

**Status:** `NOT VERIFIED`

**Remaining:** отдельный factual audit каждого контура.

# 5. Основные подсистемы AIEA

**Status:** `PARTIALLY VERIFIED`

## 5.1. Evolution Orchestrator

Каноническое назначение: запуск research cycles, экспериментов, validation и передачи результатов в controlled promotion.

Фактически обнаружен `agents/ai_orchestrator.py`.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** `agents/ai_orchestrator.py`

**Remaining:** полный audit фактического orchestration lifecycle.

## 5.2. Knowledge Engine

Фактически существует:

- `services/ai_knowledge_engine.py`
- `services/ai_knowledge_snapshot_service.py`

Knowledge snapshot используется как вход для последующего hypothesis generation.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** B1/B2 research evidence и найденные AI knowledge services.

## 5.3. Hypothesis Engine

Фактически существует `services/ai_hypothesis_engine.py`.

Подтверждено:

- hypothesis generation из snapshot;
- user binding;
- snapshot binding;
- conditions / parameters / reasoning;
- отсутствие автоматической production mutation.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_REGIME_CONTRAST_OK`
- `B2_HYPOTHESIS_STRUCTURE_OK`
- `B2_VALIDATION_REQUIRED_OK`
- `B2_NO_STRATEGY_MUTATION_OK`
- `B2_HYPOTHESIS_RESEARCH_OK`

## 5.4. Strategy Generator

Отдельный production-ready AI Strategy Generator как полный autonomous lifecycle пока не доказан.

Обнаружена strategy-version infrastructure, но этого недостаточно для утверждения полной автоматической генерации.

**Status:** `NOT VERIFIED`

**Remaining:** generator implementation, schema, sandbox execution, validation linkage.

## 5.5. Strategy Modifier

Versioned strategy infrastructure существует.

Новая версия связывается с hypothesis / experiment и promotion genealogy.

Полный autonomous modifier lifecycle не доказан.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- `models/ai_strategy_version.py`
- `services/ai_experiment_engine.py`
- `services/ai_promotion_rollback.py`

## 5.6. Strategy Genome

Требуется machine-readable strategy definition.

Static validation содержит проверку Strategy Definition / Genome schema.

Фактический полный genome lifecycle от generation до comparison ещё не подтверждён.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** `services/ai_static_strategy_validator.py`

**Remaining:** exhaustive genome lifecycle audit.

## 5.7. Experiment Engine

Фактически существует:

`services/ai_experiment_engine.py`

Подтверждены:

- experiment creation;
- hypothesis linkage;
- strategy version linkage;
- ownership;
- validation linkage.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 experiment chain;
- B2 validation-required boundary;
- E1/E12 promotion integration.

## 5.8. Validation Engine

Фактически реализован отдельный validation contour:

- Static Validation;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- validation metrics / scoring.

**Status:** `DONE`

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 5.9. Comparison Engine

Фактически реализованы:

- comparison contract;
- identity/alignment;
- participant-specific analytics;
- PnL / win rate / PF / expectancy;
- drawdown / stability;
- trade_source separation;
- News/Event context;
- persistence;
- read-only analysis.

**Status:** `DONE + REVIEWED`

**Evidence:** BLOCK F `F.1–F.9`.

## 5.10. Promotion subsystem

Фактически существуют:

- Promotion Manager;
- Promotion Gates;
- Risk Approval;
- Permission Policy;
- Promotion Audit;
- Rollback;
- Rollback Integrity;
- Production Safety;
- Multi-user Isolation.

**Status:** `DONE`

**Evidence:** E.1–E.12.

## 5.11. AI Memory

Фактически реализована research-only append-only memory.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_AGENT_OK`
- `B4_LESSON_RECORD_OK`
- `B4_USER_MEMORY_ISOLATION_OK`
- `B4_EXPERIMENT_OWNERSHIP_OK`
- `B4_APPEND_ONLY_MEMORY_OK`
- `B4_RESEARCH_MEMORY_ONLY_OK`
- `B4_CLEANUP_OK`

## 5.12. News / Event subsystem

Обнаружены:

- `services/ai_news_event_service.py`
- `services/ai_news_ingestion.py`
- `models/ai_news_event.py`
- News/Event comparison context layer.

Полная production/research News & Event Intelligence ещё не завершена.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** ingestion, event storage, deduplication, historical backfill, correlation and validation integration.

## 5.13. Production Safety

AIEA-related production boundary уже имеет отдельный safety layer.

**Status:** `VERIFIED`

**Evidence:**
- `services/ai_production_safety.py`
- `services/execution_boundary.py`
- E10/E12 evidence.

## 5.14. Итог раздела

Основные базовые AIEA subsystems уже существуют.

Полностью доказаны отдельными тестами/аудитами:

- Hypothesis;
- Experiment;
- Validation;
- Comparison;
- Promotion;
- Memory.

Частично доказаны:

- Evolution Orchestrator;
- Knowledge Engine;
- Strategy Modifier;
- Strategy Genome;
- News/Event.

Не доказан полностью:

- autonomous Strategy Generator lifecycle.

**Remaining:** закрывать подсистемы по отдельному factual audit, не повторяя уже закрытые тесты.
# 6. Knowledge Engine

**Status:** `PARTIALLY VERIFIED`

## 6.1. Назначение

Knowledge Engine должен собирать и анализировать:

- TradeHistory;
- Positions;
- strategy;
- market_regime;
- symbol;
- side;
- confidence;
- volatility;
- entry / exit;
- SL / TP;
- PnL;
- fees / funding;
- holding time;
- close reason;
- signal metadata;
- historical market data;
- News & Event context.

## 6.2. Фактическая реализация

Обнаружены:

- `services/ai_knowledge_engine.py`
- `services/ai_knowledge_snapshot_service.py`
- `models/ai_knowledge_snapshot.py`

Knowledge snapshots используются как структурированный вход для research / hypothesis generation.

**Status:** `VERIFIED` для существования и snapshot pipeline.

**Evidence:**
- B1 historical analysis;
- B2 hypothesis research;
- `AIKnowledgeEngine`;
- `AIKnowledgeSnapshotService`.

## 6.3. Аналитические разрезы

Подтверждены в B1:

- strategy × regime;
- strategy × symbol;
- strategy × side;
- strategy × regime × side;
- strategy × regime × side × symbol;
- strategy × volatility;
- strategy × confidence;
- symbol × regime;
- strategy × hour;
- strategy × day_of_week;
- strategy × holding_time;
- strategy × leverage.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B1_REQUIRED_SLICES_OK`
- `B1_OPTIONAL_SLICES_OK`
- `B1_AGGREGATION_OK`
- `B1_HISTORICAL_ANALYSIS_OK`

## 6.4. Data quality

AIEA research layer должен отделять или исключать:

- legacy;
- GRID;
- test/manual-test;
- missing strategy;
- missing regime;
- invalid trade context;
- неподтверждённые источники.

B1 проверяет:

- `trade_source`;
- strategy quality;
- GRID exclusion;
- отсутствие synthetic dimensions.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B1_REAL_SOURCE_ISOLATION_OK`
- `B1_STRATEGY_QUALITY_FILTER_OK`
- `B1_NO_SYNTHETIC_DIMENSIONS_OK`
- `B1_DATA_QUALITY_OK`

## 6.5. Research snapshot integrity

Snapshot должен быть связан с конкретным user и dataset version.

Использование snapshot в hypothesis chain уже подтверждено:

`Knowledge Snapshot → Hypothesis`

**Status:** `TEST VERIFIED`

**Evidence:**
- B2 user binding;
- B2 snapshot binding;
- A8 identity isolation.

## 6.6. AI Memory integration

Knowledge results могут использоваться как вход для следующего research cycle.

AI Memory остаётся отдельным append-only контуром и не заменяет исторические данные.

**Status:** `TEST VERIFIED` частично в рамках B4.

**Evidence:** B4 research-memory-only boundary.

## 6.7. News & Event Intelligence

Архитектура требует:

`News/Event → Knowledge → Research → Hypothesis → Validation`

Обнаружены:

- `models/ai_news_event.py`
- `services/ai_news_event_service.py`
- `services/ai_news_ingestion.py`
- `services/ai_comparison_news_context.py`

Но полный historical event ingestion, backfill и корреляционный Knowledge pipeline ещё не закрыты.

**Status:** `PARTIALLY VERIFIED`

**Remaining:**
- external ingestion;
- source adapters;
- persistent event store;
- historical backfill;
- deduplication;
- event → market linkage;
- event → regime linkage;
- event → strategy linkage;
- event → outcome linkage.

## 6.8. Источники торговых данных

Knowledge Engine не должен смешивать:

`REAL / GRID / TEST / AI_PAPER / AI_SHADOW / AI_LIVE / LEGACY`

Production performance должна анализироваться отдельно от experimental sources.

**Status:** `TEST VERIFIED` для подтверждённых B1 source guards; полный cross-source audit ещё требуется.

## 6.9. Итог

Основной historical research / aggregation контур существует и имеет тестовое подтверждение.

Закрыто:

- аналитические slices;
- source/data quality filtering;
- snapshot generation/binding;
- research input для hypothesis generation.

Не закрыто полностью:

- полноценный event-aware Knowledge layer;
- полный historical News/Event dataset lifecycle;
- exhaustive source-isolation audit всех research queries.

**Remaining:** factual audit News/Event + complete Knowledge source coverage.
# 7. Hypothesis Engine

**Status:** `TEST VERIFIED`

## 7.1. Назначение

Hypothesis Engine должен преобразовывать наблюдения Knowledge Engine в формализованные, проверяемые и воспроизводимые гипотезы.

Базовая цепочка:

`Knowledge Snapshot → Observation → Hypothesis → Experiment`

## 7.2. Фактическая реализация

Обнаружен:

`services/ai_hypothesis_engine.py`

Фактически подтверждено:

- генерация hypothesis из Knowledge Snapshot;
- привязка hypothesis к user;
- привязка к snapshot;
- target strategy;
- hypothesis type;
- conditions;
- parameters;
- reasoning;
- status.

## 7.3. Структура hypothesis

Поддерживаются данные:

- `title`;
- `description`;
- `hypothesis_type`;
- `target_strategy`;
- `parent_version`;
- `expected_effect`;
- `conditions`;
- `parameters`;
- `reasoning`;
- `status`.

Hypothesis должна оставаться исследовательским объектом до validation.

## 7.4. Связь с исходными наблюдениями

Hypothesis связывается с конкретным Knowledge Snapshot.

Это обеспечивает трассируемость:

`research data → snapshot → hypothesis`

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_REGIME_CONTRAST_OK`
- `B2_HYPOTHESIS_STRUCTURE_OK`

## 7.5. User / identity isolation

Hypothesis должна принадлежать тому же user, которому принадлежит исходный snapshot.

Это дополнительно защищено A8 identity isolation.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_HYPOTHESIS_STRUCTURE_OK`
- A8 cross-user isolation evidence.

## 7.6. Validation boundary

Hypothesis не считается доказанной автоматически.

Для перехода к strategy validation требуется Experiment Engine и дальнейшая validation pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_VALIDATION_REQUIRED_OK`

## 7.7. Запрет самостоятельной mutation production strategy

Генерация hypothesis сама по себе не должна изменять production strategy.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_NO_STRATEGY_MUTATION_OK`

## 7.8. Experiment linkage

Hypothesis должна быть связана с создаваемым экспериментом, а эксперимент — с конкретной Strategy Version.

Фактическая цепочка подтверждена в A9:

`Snapshot → Hypothesis → Experiment → StrategyVersion`

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_SNAPSHOT_OK`
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`

## 7.9. Research-only boundary

Hypothesis Engine не получает production execution authority.

Он не должен:

- отправлять exchange orders;
- менять RiskAgent;
- менять ExecutionAgent;
- менять production strategy;
- менять risk limits;
- самостоятельно выполнять promotion.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** полный negative-path audit непосредственно для Hypothesis Engine.

## 7.10. Итог

Hypothesis Engine фактически существует и его основной research lifecycle подтверждён тестами.

Закрыто:

- hypothesis generation;
- snapshot binding;
- user binding;
- hypothesis structure;
- validation-required boundary;
- no-strategy-mutation boundary;
- experiment linkage.

Остаётся:

- exhaustive negative-path audit;
- проверка поведения при malformed / inconsistent snapshot data;
- расширенная дедупликация похожих гипотез.

# 8. Strategy Generator

**Status:** `NOT VERIFIED`

## 8.1. Каноническое требование

AIEA должен уметь создавать новые стратегии.

Каждая generated strategy должна получать:

- unique strategy ID;
- version;
- hypothesis ID;
- Strategy Genome;
- experiment ID;
- validation state.

Generated strategy по умолчанию является экспериментальной и не получает production permissions автоматически.

## 8.2. Требования к implementation boundary

Generation должна происходить в research / sandbox environment.

Production не должен исполнять необработанный AI-generated Python.

Generated strategy должна проходить:

`generation → static validation → sandbox execution → backtest → OOS → walk-forward → paper → shadow → evaluation → promotion`

## 8.3. Фактически обнаруженная инфраструктура

Обнаружены:

- `models/ai_strategy_version.py`;
- `services/ai_static_strategy_validator.py`;
- `services/ai_experiment_engine.py`;
- `services/ai_backtest_engine.py`;
- `services/ai_oos_validator.py`;
- `services/ai_walk_forward_validator.py`;
- `services/ai_paper_trading_service.py`.

Эта инфраструктура подтверждает наличие необходимых downstream компонентов, но не доказывает наличие полного автономного Strategy Generator.

## 8.4. Strategy Version boundary

Strategy Version уже используется в experiment / promotion identity chains.

A9 подтвердил:

`Experiment → StrategyVersion`

но это не является доказательством autonomous generation.

**Status:** `TEST VERIFIED` для version linkage.

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`

## 8.5. Static validation boundary

Static validator содержит проверки стратегии и запрещённых operations, включая ограничения на RiskAgent / ExecutionAgent / exchange access.

**Status:** `VERIFIED` как существующий validation component.

**Evidence:**
- `services/ai_static_strategy_validator.py`
- BLOCK D static validation evidence.

## 8.6. Production permission boundary

Новая strategy version не должна автоматически получать production permission.

Promotion E.1–E.12 обеспечивает отдельную контролируемую permission / promotion boundary.

**Status:** `TEST VERIFIED`

**Evidence:**
- E.6 permission tests;
- E.10 production safety;
- E.12 promotion integration.

## 8.7. Что ещё не доказано

Не подтверждены полностью:

- autonomous generation logic;
- generation input/context assembly;
- automatic genome generation;
- generated implementation persistence;
- sandbox execution lifecycle;
- generator → experiment automatic linkage;
- generator → validation automatic pipeline;
- duplicate strategy detection;
- generator failure handling.

## 8.8. Итог

Инфраструктура для Strategy Version, Static Validation, Experiment и Validation уже существует.

Полный автономный Strategy Generator пока **не считается реализованным без отдельного factual/test evidence**.

**Remaining:** отдельный audit generator implementation и его end-to-end lifecycle.

# 9. Strategy Modifier

**Status:** `PARTIALLY VERIFIED`

## 9.1. Каноническое требование

AIEA должен изменять существующие стратегии только через создание новой версии.

Запрещено изменять существующую production version непосредственно.

Поддерживаемые типы изменений:

- parameter change;
- rule addition;
- rule removal;
- entry modification;
- exit modification;
- filter modification;
- regime restriction;
- volatility restriction;
- volume filter;
- confidence threshold;
- risk/reward model;
- SL / TP model;
- News/Event filter;
- News/Event risk restriction.

## 9.2. Versioned strategy infrastructure

Фактически существует:

`models/ai_strategy_version.py`

Strategy Version используется в identity chain, experiments и promotion.

**Status:** `VERIFIED` для version infrastructure.

**Evidence:**
- `models/ai_strategy_version.py`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E.1–E.12 promotion evidence.

## 9.3. Parent / Genealogy binding

Promotion rollback и integrity layer требуют контролируемой связи с parent version.

Проверяются:

- parent existence;
- same strategy;
- same hypothesis;
- promotion stage / level consistency;
- parent approval;
- parent status.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_VALID_GENEALOGY_FIXTURE_OK`
- `E9_PARENT_REQUIRED_BLOCKED_OK`
- `E9_HYPOTHESIS_MISMATCH_BLOCKED_OK`
- `E9_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E9_PARENT_APPROVAL_REQUIRED_OK`
- `E9_PARENT_STATUS_MISMATCH_BLOCKED_OK`
- `E9_PARENT_PRESERVED_OK`

## 9.4. Production version immutability

Существующая доказанная version не должна переписываться новой версией.

Rollback сохраняет parent version и не удаляет историю.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_PARENT_VERSION_PRESERVED_OK`
- `E8_HISTORY_PRESERVED_OK`
- `E9_PARENT_PRESERVED_OK`

## 9.5. Hypothesis / Experiment linkage

Изменение strategy version должно быть связано с hypothesis и experiment.

A9 подтверждает:

`Hypothesis → Experiment → StrategyVersion`

Promotion layer дополнительно проверяет identity consistency.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E11 identity isolation evidence.

## 9.6. Autonomous modifier lifecycle

Наличие version infrastructure не доказывает наличие полного autonomous Strategy Modifier.

Не доказаны:

- получение исходной strategy context;
- формирование modification proposal;
- автоматическое изменение genome;
- автоматическая генерация новой definition;
- сохранение before/after genome;
- автоматический experiment creation;
- автоматический validation запуск;
- automatic comparison старой и новой version.

**Status:** `NOT VERIFIED`

## 9.7. Production safety

Даже созданная новая version не должна автоматически становиться production version.

Promotion должен проходить через controlled pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 permission controls;
- E10 production safety;
- E12 end-to-end promotion integration.

## 9.8. Итог

Versioning, genealogy и promotion boundaries фактически реализованы и протестированы.

Полный autonomous Strategy Modifier ещё не доказан.

**Remaining:**

отдельный audit modifier implementation → genome diff → experiment → validation → promotion lifecycle.
# 10. Strategy Genome

**Status:** `PARTIALLY VERIFIED`

## 10.1. Каноническое требование

Каждая AI strategy должна иметь машинно-читаемое описание — Strategy Genome.

Genome должен описывать как минимум:

- strategy;
- version;
- parent;
- regimes;
- entry rules;
- exit rules;
- filters;
- confidence rules;
- risk rules.

Genome должен использоваться как структурированное определение стратегии, а не только как текстовое описание.

## 10.2. Genome schema / static validation

Фактически существует:

`services/ai_static_strategy_validator.py`

Static validation содержит отдельные проверки Strategy Definition / Genome schema и запрещённых операций.

**Status:** `VERIFIED` для schema/static validation layer.

**Evidence:**
- BLOCK D / D.1 static validation;
- `services/ai_static_strategy_validator.py`.

## 10.3. Strategy Version integration

Strategy Version хранится отдельно и используется в:

`Hypothesis → Experiment → StrategyVersion → Validation/Promotion`

**Status:** `TEST VERIFIED` для linkage.

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`;
- E.1–E.12 identity/promotion evidence.

## 10.4. Version immutability

Изменение genome не должно переписывать существующую version.

Новая definition должна быть отдельной version с parent linkage.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_PARENT_VERSION_PRESERVED_OK`;
- `E9_PARENT_PRESERVED_OK`;
- `E9_ROLLBACK_AUDIT_INTEGRITY_OK`.

## 10.5. Genome → Validation

Genome/strategy definition должна проходить static validation до дальнейшего validation pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK D static validation;
- malformed definition / forbidden operations tests;
- validation gate integration.

## 10.6. Genome → Backtest / OOS / Walk-Forward / Paper / Shadow

Validation infrastructure содержит downstream stages:

- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow.

Однако полный доказанный автоматический lifecycle именно:

`Genome → Stage 1 → Stage 2 → ... → Stage 6`

для AI-generated genome отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- BLOCK D completed;
- validation services present;
- promotion evidence chain.

## 10.7. Before / After Genome evolution

Для изменения существующей стратегии требуется сохранять:

- parent genome;
- new genome;
- hypothesis;
- experiment;
- expected effect;
- actual effect;
- validation history.

Наличие полной автоматической before/after genome persistence пока не доказано.

**Status:** `NOT VERIFIED`

## 10.8. Genome comparison

Genome должен позволять сравнивать версии и определять, какие изменения привели к изменению результата.

Отдельный полноценный Genome Diff / comparison lifecycle пока не подтверждён.

**Status:** `NOT VERIFIED`

## 10.9. Autonomous genome generation

Не подтверждены полностью:

- автоматическое построение genome AI;
- автоматическая mutation genome;
- genome deduplication;
- genome complexity limits;
- automatic genome → strategy implementation;
- sandbox execution именно genome-generated strategy.

**Status:** `NOT VERIFIED`

## 10.10. Production boundary

Genome не получает production permission автоматически.

Любая version должна пройти controlled Promotion Pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 permission policy;
- E10 production safety;
- E12 promotion integration.

## 10.11. Итог

Подтверждены:

- Strategy Definition / Genome schema validation;
- Strategy Version integration;
- immutable version boundary;
- связь с validation infrastructure;
- production permission boundary.

Не подтверждены полностью:

- autonomous genome generation;
- genome mutation lifecycle;
- before/after genome persistence;
- genome diff;
- complete genome-driven strategy execution lifecycle.

**Remaining:** отдельный factual audit полного Strategy Genome lifecycle.
# 11. Validation Engine

**Status:** `DONE`

## 11.1. Общий validation pipeline

Каноническая последовательность:

`Static Validation → Backtest → OOS → Walk-Forward → Paper → Shadow`

Каждая стадия должна иметь собственные данные, результаты и критерии прохождения.

BLOCK D фактически завершён.

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 11.2. Stage 1 — Static Validation

Проверяются:

- структура strategy definition;
- обязательные поля;
- допустимые параметры;
- forbidden operations;
- production/exchange isolation;
- RiskAgent / ExecutionAgent restrictions;
- Strategy Genome schema.

Фактически существует:

`services/ai_static_strategy_validator.py`

**Status:** `TEST VERIFIED`

**Evidence:**
- D.1 static validation evidence;
- malformed definition blocked;
- forbidden operations blocked;
- validation gate integration.

## 11.3. Stage 2 — Backtest

Фактически реализованы отдельные компоненты:

- `services/ai_backtest_dataset.py`
- `services/ai_historical_market_data_loader.py`
- `services/ai_strategy_signal_replay.py`
- `services/ai_backtest_execution.py`
- `services/ai_backtest_metrics.py`
- `services/ai_backtest_engine.py`
- `services/ai_candle_backtest_service.py`

Подтверждены:

- historical data loading;
- pagination;
- timestamp normalization;
- duplicate elimination;
- continuity/gap checks;
- no-lookahead replay;
- entry/exit;
- SL/TP;
- fees;
- funding;
- slippage;
- LONG/SHORT;
- multi-symbol;
- multi-regime;
- canonical PnL;
- profit factor;
- expectancy;
- drawdown;
- Sharpe / Sortino;
- production isolation.

**Status:** `TEST VERIFIED`

**Evidence:** D.2.1–D.2.8 + `D6_8_BLOCK_D_FULL_COMPILE_OK`.

## 11.4. Stage 3 — Out-of-Sample

Фактически существует:

`services/ai_oos_validator.py`

OOS связан с конкретным:

- experiment;
- strategy version;
- hypothesis;
- target strategy.

Также существуют source/data validity guards.

**Status:** `TEST VERIFIED`

**Evidence:** completed BLOCK D OOS validation and promotion evidence.

## 11.5. Stage 4 — Walk-Forward

Фактически существует:

- `services/ai_walk_forward_validator.py`
- `services/ai_shadow_walk_forward_validator.py`

Назначение — последовательная оценка на независимых временных окнах.

**Status:** `TEST VERIFIED`

**Evidence:** BLOCK D completion + validation evidence.

## 11.6. Stage 5 — Paper

Фактически существует:

`services/ai_paper_trading_service.py`

и:

`services/ai_paper_result_aggregation.py`

Paper должен моделировать:

- entry;
- exit;
- SL;
- TP;
- fees;
- funding;
- holding time;
- PnL.

Результаты отделены от production trading.

**Status:** `TEST VERIFIED`

**Evidence:** BLOCK D paper validation completion.

## 11.7. Stage 6 — Shadow

Фактически существует shadow infrastructure:

- `models/ai_shadow_decision.py`;
- shadow quality services;
- shadow stability;
- advisory;
- outcome resolution.

Current production safety:

- Strategy Decision Engine = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- shadow/advisory не управляют production execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK E/F integration evidence;
- shadow/advisory production-boundary checks;
- `services/ai_shadow_advisory_influence_policy.py`.

## 11.8. Validation result persistence

Validation results должны сохранять:

- strategy version;
- experiment;
- dataset;
- validation stage;
- result;
- evidence;
- критерии прохождения.

Validation Evidence infrastructure существует:

`services/ai_validation_evidence.py`

Promotion E.4 дополнительно проверяет identity/evidence binding.

**Status:** `TEST VERIFIED`

**Evidence:** E4 exact evidence binding + E10/E12 integration.

## 11.9. Validation → Promotion boundary

Высокий PnL сам по себе не разрешает переход.

Promotion требует:

- readiness;
- formal gate;
- evidence;
- risk approval;
- permission;
- stage consistency.

**Status:** `TEST VERIFIED`

**Evidence:**
- E1;
- E3;
- E4;
- E5;
- E6;
- E10;
- E12.

## 11.10. Production isolation

Validation services не должны вызывать:

- RiskAgent;
- ExecutionAgent;
- direct exchange execution.

Backtest / OOS / validation остаются research-only.

**Status:** `VERIFIED`

**Evidence:**
- `services/ai_backtest_*`
- `services/ai_oos_validator.py`
- `services/ai_walk_forward_validator.py`
- D BLOCK production isolation;
- E10/E12 production isolation.

## 11.11. Оставшиеся validation extensions

Не считаются полностью закрытыми отдельными контурами:

- полный News/Event-aware validation;
- exhaustive robustness framework beyond completed BLOCK D;
- автоматизированная статистическая sufficiency policy на всех stages;
- единый end-to-end generated-strategy validation runner.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** отдельный audit этих расширений.

## 11.12. Итог

BLOCK D фактически завершён.

Подтверждены:

- Static Validation;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow;
- validation evidence;
- production isolation;
- promotion boundary.

**Final evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

# 12. Experiment Engine

**Status:** `TEST VERIFIED`

## 12.1. Каноническое требование

Каждый эксперимент должен иметь уникальный identity и быть воспроизводимым.

Минимальная цепочка:

`Hypothesis → Experiment → Strategy Version → Dataset → Parameters → Result`

## 12.2. Фактическая реализация

Обнаружен:

`services/ai_experiment_engine.py`

Также существует модель:

`models/ai_experiment.py`

Эксперимент связывается с:

- hypothesis;
- strategy version;
- user;
- dataset;
- parameters;
- experiment type;
- lifecycle status.

**Status:** `VERIFIED`

## 12.3. Experiment identity

Для эксперимента должны сохраняться:

- `experiment_id`;
- `hypothesis_id`;
- `strategy_version_id`;
- dataset;
- parameters;
- start/end range;
- timestamps;
- result.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- A8 identity isolation;
- E1/E12 promotion identity chain.

## 12.4. Experiment lifecycle

Канонические состояния:

`CREATED → RUNNING → PASSED / FAILED / REJECTED`

Дополнительно возможны:

`PROMOTED`
`ROLLED_BACK`

Experiment history не должна переписываться при последующих promotion / rollback действиях.

**Status:** `TEST VERIFIED`

**Evidence:**
- E8 history preservation;
- E12 promotion integration.

## 12.5. Hypothesis binding

Эксперимент должен принадлежать той же hypothesis, из которой он был создан.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 hypothesis/experiment chain;
- E11 cross-user identity isolation;
- E12 identity validation.

## 12.6. Strategy Version binding

Каждый experiment, связанный со strategy validation или promotion, должен ссылаться на конкретную Strategy Version.

Нельзя использовать только имя стратегии без version identity.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E4 exact evidence binding;
- E12 promotion chain.

## 12.7. User ownership

Experiment должен принадлежать тому же user, что и его hypothesis / strategy identity chain.

Cross-user tampering должно блокироваться.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A8_CROSS_USER_EXPERIMENT_TAMPER_BLOCKED_OK`
- `A8_IDENTITY_CHAINS_REMAIN_ISOLATED_OK`
- E11 cross-user identity evidence.

## 12.8. Reproducibility

Для воспроизводимости должны быть доступны:

- exact strategy version;
- hypothesis;
- dataset;
- parameters;
- time range;
- experiment type.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** model / service infrastructure.

**Remaining:** отдельный deterministic rerun audit.

## 12.9. Production isolation

Experiment Engine не должен:

- отправлять exchange orders;
- вызывать production ExecutionAgent;
- менять production strategy;
- менять risk limits.

**Status:** `VERIFIED`

**Evidence:**
- `services/ai_experiment_engine.py`
- E10/E12 production isolation.

## 12.10. Result linkage

Эксперимент должен иметь связанный result/evidence для последующей validation и promotion.

Обнаружены:

- `models/ai_experiment_result.py`;
- `services/ai_validation_evidence.py`.

**Status:** `TEST VERIFIED`

**Evidence:** E3/E4/E12 validation/promotion evidence.

## 12.11. Cleanup / test isolation

Integration tests создают временные experiment fixtures и очищают их после завершения.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8 cleanup;
- A9 cleanup;
- E12 cleanup.

## 12.12. Не закрыто полностью

Остаётся проверить отдельно:

- deterministic experiment rerun;
- complete dataset fingerprint/version binding;
- automatic end-to-end Experiment → all validation stages orchestration;
- failed experiment recovery;
- concurrent experiment isolation.

**Status:** `PARTIALLY VERIFIED`

## 12.13. Итог

Experiment Engine и его identity chain фактически существуют и подтверждены тестами.

Закрыто:

- experiment model;
- hypothesis binding;
- strategy version binding;
- user ownership;
- validation/evidence linkage;
- production isolation;
- cleanup.

Remaining: расширенный reproducibility / concurrency audit.
# 13. Метрики стратегии

**Status:** `TEST VERIFIED`

## 13.1. Канонический набор метрик

Для каждой Strategy Version должны рассчитываться:

- total trades;
- wins;
- losses;
- win rate;
- gross PnL;
- net PnL;
- average PnL;
- median PnL;
- profit factor;
- expectancy;
- max drawdown;
- Sharpe;
- Sortino;
- average holding time;
- fees;
- funding;
- worst trade;
- best trade.

## 13.2. Фактическая реализация

Обнаружены:

- `services/ai_backtest_metrics.py`
- `services/ai_research_evaluation.py`
- `models/ai_experiment_result.py`

B3 подтверждает canonical metrics на тестовых данных.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B3_CANONICAL_METRICS_OK`
- `B3_VERSION_SOURCE_BINDING_OK`
- `B3_REQUIRED_SLICES_OK`
- `B3_RESEARCH_ONLY_OK`
- `B3_STRATEGY_EVALUATION_OK`

## 13.3. PnL integrity

Метрики должны различать:

- gross PnL;
- fees;
- funding;
- net PnL.

B3 подтверждает:

`gross_pnl = 120.0`
`fees = 10.0`
`funding = 3.0`
`net_pnl = 107.0`

**Status:** `TEST VERIFIED`

## 13.4. Strategy slices

Обязательные аналитические разрезы:

- strategy × regime;
- strategy × symbol;
- strategy × side.

Дополнительные research dimensions:

- volatility;
- confidence;
- hour;
- day_of_week;
- holding_time;
- leverage.

**Status:** `TEST VERIFIED`

**Evidence:** B1 historical analysis + B3 required slices.

## 13.5. Trade source separation

Metrics должны рассчитываться отдельно по `trade_source`.

Нельзя смешивать production и experimental sources.

**Status:** `TEST VERIFIED`

**Evidence:**
- B1 real-source isolation;
- BLOCK F trade_source separation;
- `services/ai_comparison_trade_source.py`.

## 13.6. Strategy Version binding

Evaluation должен относиться к конкретной Strategy Version, а не только к имени strategy.

B3 подтверждает:

- конкретную strategy version;
- `trade_source=REAL`;
- research-only result;
- `validated=False`;
- `promotion_ready=False`.

**Status:** `TEST VERIFIED`

**Evidence:** B3 canonical metrics/version binding.

## 13.7. Stability metrics

Канонические требования включают:

- stability;
- variance;
- win/loss sequences;
- degradation train → OOS;
- degradation backtest → paper → shadow;
- statistical significance;
- minimum sample size.

В проекте обнаружены дополнительные stability services:

- `services/ai_shadow_stability_service.py`
- `services/ai_shadow_quality_service.py`
- `services/ai_shadow_quality_window_service.py`

Однако полный единый statistical stability policy для всего lifecycle отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 13.8. Best / Worst trade and holding time

B3 подтверждает:

- best trade;
- worst trade;
- average holding time;
- average PnL;
- median PnL;
- expectancy.

**Status:** `TEST VERIFIED`

## 13.9. Statistical sufficiency

Недостаточный sample size не должен считаться доказательством edge.

Promotion gates уже используют sufficiency guards для отдельных validation stages.

**Status:** `TEST VERIFIED` для promotion gates; `PARTIALLY VERIFIED` для единой metrics policy.

**Evidence:**
- E3 insufficient-data guard;
- promotion gate tests.

## 13.10. Research-only semantics

Исследовательская оценка не должна автоматически делать strategy validated или promotion-ready.

B3 явно проверяет:

- `research_only=True`;
- `validated=False`;
- `promotion_ready=False`.

**Status:** `TEST VERIFIED`

**Evidence:** `B3_RESEARCH_ONLY_OK`

## 13.11. Итог

Подтверждены:

- canonical performance metrics;
- PnL / fee / funding accounting;
- required strategy slices;
- strategy version binding;
- trade_source isolation;
- research-only evaluation;
- best/worst trade;
- holding time;
- basic sufficiency guards.

Не закрыто полностью:

- единая statistical significance policy;
- единая stability/degradation policy между всеми validation stages;
- полная statistical robustness framework.

**Remaining:** отдельный factual audit stability / significance / degradation policy.
# 14. Overfitting Protection

**Status:** `PARTIALLY VERIFIED`

## 14.1. Каноническое назначение

AIEA не должен считать strategy доказанной только потому, что она показала высокий historical/backtest PnL.

Обязательны:

- train/test separation;
- OOS validation;
- walk-forward validation;
- minimum trade count;
- parameter complexity limits;
- stability checks;
- degradation checks;
- robustness checks;
- multi-symbol validation;
- multi-regime validation;
- отдельная LONG/SHORT проверка;
- News/Event behaviour analysis при наличии данных.

## 14.2. Train / Test Separation

Validation architecture содержит отдельный OOS stage и запрет использования OOS/test данных для optimization.

**Status:** `VERIFIED`

**Evidence:**
- `services/ai_oos_validator.py`
- BLOCK D OOS implementation;
- validation evidence chain.

## 14.3. Out-of-Sample Protection

OOS использует отдельный период, не участвующий в создании/оптимизации strategy.

**Status:** `TEST VERIFIED`

**Evidence:** completed D.3 OOS validation and promotion gates.

## 14.4. Walk-Forward Protection

Walk-Forward использует последовательные независимые временные окна:

`train → validate → test → next window`

**Status:** `TEST VERIFIED`

**Evidence:**
- `services/ai_walk_forward_validator.py`
- BLOCK D completion.

## 14.5. Minimum Sample / Sufficiency

Недостаточный sample size не должен считаться доказательством.

Promotion Gate уже блокирует `INSUFFICIENT_DATA`.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E3_OOS_INSUFFICIENT_DATA_BLOCKED_OK`
- `E3_MISSING_RESULT_BLOCKED_OK`

## 14.6. Performance Degradation

Требуется анализ degradation между:

- backtest → OOS;
- OOS → walk-forward;
- backtest → paper;
- paper → shadow;
- shadow → дальнейшие стадии.

Инфраструктура evaluation/stability существует, но единая policy для всех переходов отдельно не доказана.

**Status:** `PARTIALLY VERIFIED`

## 14.7. Multi-symbol / Multi-regime Robustness

Backtest architecture поддерживает:

- multi-symbol;
- multi-regime;
- LONG;
- SHORT.

**Status:** `TEST VERIFIED`

**Evidence:**
- D.2.6;
- `D6_8_BLOCK_D_FULL_COMPILE_OK`.

## 14.8. Parameter Complexity

Канонический план требует ограничения сложности параметров, чтобы уменьшать риск overfitting.

Отдельный полный complexity budget / parameter-count policy фактически не подтверждён.

**Status:** `NOT VERIFIED`

**Remaining:** определить и проверить измеряемую complexity policy.

## 14.9. Stability / Variance

В проекте существуют:

- `ai_shadow_stability_service.py`;
- `ai_shadow_quality_service.py`;
- `ai_shadow_quality_window_service.py`.

Они обеспечивают отдельные stability/quality analyses.

Единая overfitting stability policy для всех validation stages ещё не доказана.

**Status:** `PARTIALLY VERIFIED`

## 14.10. Statistical Significance

Результат должен оцениваться с учётом statistical significance и sample sufficiency.

Sufficiency guards есть в promotion layer, но полноценная unified statistical significance framework ещё не подтверждена.

**Status:** `PARTIALLY VERIFIED`

## 14.11. News/Event Overfitting Protection

При наличии исторических News/Event данных необходимо проверять:

- pre-event behaviour;
- during-event behaviour;
- post-event behaviour;
- degradation при сильном event/news background.

Полный historical event-aware validation ещё не закрыт.

**Status:** `NOT VERIFIED`

## 14.12. No Optimization on OOS/Test

OOS/test данные не должны использоваться для настройки strategy.

Это архитектурное требование validation pipeline.

**Status:** `VERIFIED` на уровне OOS design; exhaustive runtime proof ещё не проведён.

## 14.13. Итог

Подтверждены:

- OOS separation;
- Walk-Forward;
- minimum-data guards;
- multi-symbol;
- multi-regime;
- LONG/SHORT robustness;
- базовые stability components.

Частично подтверждены:

- degradation policy;
- unified stability policy;
- statistical significance.

Не подтверждены:

- parameter complexity policy;
- полный News/Event-aware anti-overfitting pipeline;
- exhaustive automated overfitting detector.

**Remaining:** отдельный audit anti-overfitting policy и её автоматического enforcement.
# 15. Strategy Promotion Pipeline

**Status:** `TEST VERIFIED / DONE`

Promotion является контролируемым переходом между validation stages и production permissions.

Каноническая цепочка:

`DRAFT → VALIDATED → BACKTEST_PASSED → OOS_PASSED → PAPER → SHADOW → ADVISORY → RESTRICTED_LIVE → LIVE`

Пропуск стадий запрещён.

## 15.1. E.1 — Promotion Manager

Фактически существует:

`services/ai_promotion_manager.py`

Promotion Manager является controlled mutation boundary.

Проверяет:

- user;
- hypothesis;
- strategy version;
- experiment;
- promotion stage;
- readiness;
- risk approval;
- permissions.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E1_READY_PROMOTION_OK`
- `E1_PROMOTION_STATE_PERSISTED_OK`
- `E1_AUDIT_CREATED_OK`
- `E1_NOT_READY_BLOCKED_OK`
- `E1_IDENTITY_ISOLATION_OK`
- `E1_PRODUCTION_ISOLATION_OK`

## 15.2. E.2 — Promotion State Machine

Фактически подтверждены:

- только следующий stage;
- запрет пропуска;
- запрет обратного перехода;
- stage ↔ level consistency.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E2_VALID_FORWARD_TRANSITION_OK`
- `E2_SKIP_STAGE_BLOCKED_OK`
- `E2_BACKWARD_TRANSITION_BLOCKED_OK`
- `E2_LEVEL_STAGE_INTEGRITY_OK`
- `E2_PRODUCTION_ISOLATION_OK`

## 15.3. E.3 — Formal Promotion Gates

Фактически существует:

`services/ai_promotion_gates.py`

Проверяются stage-specific validation results и evidence.

Недостаточные данные блокируют promotion.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E3_BACKTEST_PASS_OK`
- `E3_OOS_PASS_OK`
- `E3_OOS_INSUFFICIENT_DATA_BLOCKED_OK`
- `E3_MISSING_RESULT_BLOCKED_OK`
- `E3_SHADOW_MISSING_BLOCKED_OK`
- `E3_SHADOW_PASS_OK`
- `E3_ADVISORY_NOT_YET_IMPLEMENTED_BLOCKED_OK`
- `E3_PRODUCTION_ISOLATION_OK`
- `E3_CLEANUP_OK`

## 15.4. E.4 — Promotion Evidence Binding

Validation evidence должна быть привязана к exact:

- user;
- experiment;
- strategy version;
- hypothesis;
- strategy definition hash.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E4_EXACT_EVIDENCE_SET_BOUND_OK`
- `E4_CROSS_VERSION_EVIDENCE_BLOCKED_OK`
- `E4_CROSS_HYPOTHESIS_EVIDENCE_BLOCKED_OK`
- `E4_CROSS_USER_EVIDENCE_BLOCKED_OK`
- `E4_PRODUCTION_ISOLATION_OK`
- `E4_CLEANUP_OK`

## 15.5. E.5 — Risk Approval Gate

Фактически существует отдельный promotion-risk контур:

`services/ai_promotion_risk_approval.py`

Он отделён от торгового AIRiskAgent.

Поддерживаются:

- `APPROVED`;
- `REJECTED`;
- `NOT_EVALUATED`;
- approval timestamp;
- approver;
- immutable approval snapshot;
- identity binding.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E5_NOT_EVALUATED_BLOCKED_OK`
- `E5_SHADOW_APPROVAL_PASS_OK`
- `E5_LIVE_SCOPE_BLOCKED_OK`
- `E5_LIVE_APPROVAL_PASS_OK`
- `E5_CROSS_EXPERIMENT_BLOCKED_OK`
- `E5_REJECT_BLOCKED_OK`
- `E5_PRODUCTION_ISOLATION_OK`
- `E5_MANAGER_RISK_BLOCK_OK`
- `E5_MANAGER_RISK_APPROVAL_PASS_OK`

## 15.6. E.6 — Promotion Level / Permissions

Фактически существует:

`services/ai_promotion_permissions.py`

Установлена единая policy:

`promotion_stage → promotion_level → permissions`

Проверяются stage/level consistency и permission escalation.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E6_ALL_STAGE_LEVELS_VALID_OK`
- `E6_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E6_UNKNOWN_STAGE_BLOCKED_OK`
- `E6_PERMISSION_ESCALATION_BLOCKED_OK`
- `E6_INVALID_STATE_NO_PERMISSION_OK`
- `E6_PRODUCTION_ISOLATION_OK`

## 15.7. E.7 — Approval / Promotion Audit Trail

Promotion сохраняет исторический snapshot, включая:

- user;
- experiment;
- hypothesis;
- strategy version;
- previous/target stage;
- previous/target level;
- approver;
- timestamp;
- strategy definition hash;
- evidence IDs/hashes;
- risk approval snapshot;
- permission state.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E7_PROMOTION_AUDIT_SNAPSHOT_OK`
- `E7_AUDIT_TRIPLE_SNAPSHOT_OK`
- `E7_HISTORICAL_SNAPSHOT_STABLE_OK`
- `E7_PRODUCTION_ISOLATION_OK`
- `E7_CLEANUP_OK`

## 15.8. E.8 — Rollback Mechanism

Фактически существует:

`services/ai_promotion_rollback.py`

Rollback:

- использует parent version;
- не удаляет current version;
- сохраняет history;
- создаёт rollback audit;
- отзывает permissions rolled-back version.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLBACK_EXECUTED_OK`
- `E8_PARENT_VERSION_PRESERVED_OK`
- `E8_ROLLED_BACK_PERMISSION_REVOKED_OK`
- `E8_ROLLBACK_AUDIT_OK`
- `E8_HISTORY_PRESERVED_OK`
- `E8_PRODUCTION_ISOLATION_OK`
- `E8_CLEANUP_OK`

## 15.9. E.9 — Rollback Integrity

Rollback genealogy integrity требует:

- valid parent;
- same strategy;
- same hypothesis;
- correct stage/level;
- parent approval;
- valid parent status;
- prohibition of repeated rollback.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_VALID_GENEALOGY_FIXTURE_OK`
- `E9_PARENT_REQUIRED_BLOCKED_OK`
- `E9_HYPOTHESIS_MISMATCH_BLOCKED_OK`
- `E9_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E9_PARENT_APPROVAL_REQUIRED_OK`
- `E9_PARENT_STATUS_MISMATCH_BLOCKED_OK`
- `E9_VALID_ROLLBACK_OK`
- `E9_SECOND_ROLLBACK_BLOCKED_OK`
- `E9_PARENT_PRESERVED_OK`
- `E9_ROLLBACK_AUDIT_INTEGRITY_OK`
- `E9_PRODUCTION_ISOLATION_OK`
- `E9_CLEANUP_OK`

## 15.10. E.10 — Production Safety

Фактически существует:

`services/ai_production_safety.py`

и production boundary:

`services/execution_boundary.py`

AI production execution требует контролируемых условий.

Проверяются:

- live stage;
- permission;
- risk approval;
- rolled-back state;
- production safety.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E10_AI_NO_RISK_APPROVAL_BLOCKED_OK`
- `E10_AI_NON_LIVE_BLOCKED_OK`
- `E10_AI_ROLLED_BACK_BLOCKED_OK`
- `E10_AI_PERMISSION_ESCALATION_BLOCKED_OK`
- `E10_AI_VALID_SAFETY_PASS_OK`
- `E10_STRATEGY_ENGINE_COMPATIBILITY_OK`
- `E10_SAFETY_POLICY_OK`
- `E10_PRODUCTION_ISOLATION_OK`

## 15.11. E.11 — Multi-user / Strategy Isolation

Promotion identity chain требует совпадения:

`user → hypothesis → strategy version → experiment → evidence`

Cross-user substitution/tampering блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E11_TWO_IDENTITY_CHAINS_CREATED_OK`
- `E11_CROSS_USER_VERSION_BLOCKED_OK`
- `E11_CROSS_USER_HYPOTHESIS_BLOCKED_OK`
- `E11_CROSS_USER_EVIDENCE_BLOCKED_OK`
- `E11_SAME_USER_IDENTITY_RESTORED_OK`
- `E11_SAME_IDENTITY_ROLLBACK_OK`
- `E11_PRODUCTION_ISOLATION_OK`
- `E11_CLEANUP_OK`

## 15.12. E.12 — End-to-End Promotion Integration

E12 объединяет полный controlled chain:

`Hypothesis → StrategyVersion → Experiment → Validation → Readiness → Formal Gate → Risk Approval → Promotion → Permission → Audit → Rollback`

**Status:** `TEST VERIFIED / DONE`

**Evidence:**
- `E12_FIXTURE_CREATED_OK`
- `E12_READINESS_AND_FORMAL_GATE_OK`
- `E12_RISK_GATE_CANNOT_BE_BYPASSED_OK`
- `E12_RISK_APPROVAL_OK`
- `E12_PROMOTION_OK`
- `E12_PERMISSION_AND_AUDIT_CHAIN_OK`
- `E12_PRODUCTION_SAFETY_CHAIN_OK`
- `E12_ROLLBACK_OK`
- `E12_ROLLBACK_INTEGRITY_OK`
- `E12_PRODUCTION_ISOLATION_OK`
- `E12_CLEANUP_OK`

## 15.13. Production state protection

Последние подтверждённые integration checks показывали отсутствие test promotion artifacts после cleanup.

Production strategy version `12` остаётся:

`CANDIDATE / DRAFT / promotion_level=0 / NOT_EVALUATED`

**Status:** `TEST VERIFIED`

## 15.14. Promotion limitations

Наличие Promotion Pipeline не означает разрешение AIEA торговать в production.

На текущем состоянии:

- Restricted Live отключён;
- Full Live отключён;
- AI не имеет прямого exchange authority;
- Promotion остаётся fail-closed.

**Status:** `VERIFIED`

## 15.15. Итог

E.1–E.12 фактически реализованы, протестированы и интеграционно проверены.

**Final status:** `DONE + TEST VERIFIED`

**Remaining:** дальнейшее расширение permission levels возможно только через новый согласованный архитектурный пункт и отдельное evidence.
# 16. AI Confidence Levels

**Status:** `PARTIALLY VERIFIED`

## 16.1. Канонические уровни

AIEA должен иметь отдельный trust level:

- `0` — Research only;
- `1` — Paper;
- `2` — Shadow;
- `3` — Advisory;
- `4` — Restricted Live;
- `5` — Live.

AI не должен самостоятельно изменять собственный trust level.

## 16.2. Разделение confidence и trust

Необходимо различать:

`strategy confidence` — уверенность конкретного торгового сигнала;

`AI trust level` — разрешённый системе уровень участия AIEA в торговом контуре.

Это разные сущности и не должны смешиваться.

## 16.3. Фактическое хранение trust level

В модели AI Agent обнаружено:

`models/ai_agent.py`

Поле:

`trust_level = Column(Integer, nullable=False, default=0)`

Таким образом, отдельное persistent поле для AI trust level существует.

**Status:** `VERIFIED`

**Evidence:** `models/ai_agent.py`

## 16.4. Promotion level / permission separation

Promotion infrastructure содержит отдельные:

- promotion stage;
- promotion level;
- permission policy.

Permission layer не должен автоматически повышать AI trust level.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 promotion permission tests;
- E10 production safety;
- E12 integration.

## 16.5. Запрет self-escalation

AI не должен самостоятельно получить более высокий access level.

Promotion layer блокирует невалидное повышение permissions и stage/level mismatch.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E6_PERMISSION_ESCALATION_BLOCKED_OK`
- `E6_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E6_INVALID_STATE_NO_PERMISSION_OK`
- `E10_AI_PERMISSION_ESCALATION_BLOCKED_OK`

## 16.6. Trust lifecycle

Не подтверждён полностью автоматический lifecycle:

`Research → Paper → Shadow → Advisory → Restricted Live → Live`

как изменение именно `ai_agent.trust_level`.

Promotion stages и permissions существуют, но unified trust lifecycle отдельно не доказан.

**Status:** `NOT VERIFIED`

## 16.7. Immutable / controlled trust policy

Требование:

AI не может сам менять:

- trust level;
- promotion criteria;
- risk limits;
- permissions.

Production safety и promotion permission infrastructure реализуют значительную часть этой границы.

Однако отдельный полный audit механизма изменения самого `trust_level` ещё не проведён.

**Status:** `PARTIALLY VERIFIED`

## 16.8. Текущий фактический вывод

Подтверждено:

- отдельное поле `trust_level`;
- разделение promotion permissions;
- блокировка permission escalation;
- отсутствие разрешения AI самостоятельно расширять production authority.

Не подтверждено полностью:

- автоматическая state machine для `ai_agent.trust_level`;
- переходы trust level через все уровни;
- отдельный immutable audit trail изменения trust level.

**Remaining:** отдельный factual audit AI trust-level lifecycle и mutation boundary.

# 17. Restricted Live

**Status:** `NOT VERIFIED / DISABLED`

## 17.1. Каноническое назначение

Restricted Live — первый ограниченный live-уровень участия AIEA в реальной торговле.

Он должен использовать строго ограниченные:

- AI risk budget;
- maximum position size;
- daily loss limit;
- maximum simultaneous positions;
- symbol whitelist;
- leverage;
- mandatory SL;
- mandatory TP;
- RiskAgent;
- protection validation;
- AI kill switch.

## 17.2. Текущий production state

На текущем состоянии Restricted Live не разрешён.

Подтверждённые ограничения:

- `Restricted Live = DISABLED`;
- AIEA не имеет прямого BingX execution authority;
- AI не должен обходить RiskAgent;
- AI не должен обходить ExecutionAgent.

**Status:** `VERIFIED` для текущего disabled safety state.

**Evidence:**
- `NEXUS_CURRENT_STATE.md`;
- production safety state;
- E10/E12 production isolation.

## 17.3. Isolated AI risk budget

Канонический план требует отдельный AI risk budget.

Пример базового ограничения:

- risk budget = 0.25% account;
- max positions = 1;
- max leverage = 3;
- daily loss limit = 0.5%.

Конкретные параметры не должны изменяться AIEA.

Отдельная фактическая Restricted Live risk-budget policy не подтверждена.

**Status:** `NOT VERIFIED`

## 17.4. Position / exposure limits

Обязательны:

- max position size;
- max simultaneous AI positions;
- symbol whitelist;
- leverage ceiling.

Production Risk / Execution infrastructure уже существует, однако отдельный Restricted Live AI limit layer не доказан.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** отдельный audit Restricted Live limit enforcement.

## 17.5. Mandatory protection

Restricted Live должен требовать:

- SL;
- TP;
- protection validation.

Production protection fail-safe уже подтверждён отдельно.

**Status:** `VERIFIED` для общего production protection boundary; `NOT VERIFIED` для полного Restricted Live-specific gate.

**Evidence:**
- protection fail-safe;
- `services/execution_boundary.py`;
- `PROTECTION_FAILSAFE`.

## 17.6. RiskAgent requirement

Restricted Live не должен обходить RiskAgent.

Production execution chain уже содержит:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary`

**Status:** `VERIFIED` для production boundary; Restricted Live-specific activation path не используется.

## 17.7. AI Kill Switch

Restricted Live должен иметь отдельный AI kill switch, который имеет priority выше AI decisions.

Наличие общего production safety / trading kill-switch подтверждено, но отдельный полный `AI_LIVE_KILL_SWITCH` lifecycle не доказан.

**Status:** `PARTIALLY VERIFIED`

## 17.8. Promotion dependency

Restricted Live возможен только после:

- validation;
- shadow evidence;
- formal promotion gate;
- risk approval;
- permission evaluation.

Эта инфраструктура E.1–E.12 уже реализована.

Это не означает, что Restricted Live включён.

**Status:** `TEST VERIFIED` для prerequisite promotion controls.

## 17.9. Restricted Live activation

Не подтверждены:

- отдельная activation state machine;
- AI-specific risk budget enforcement;
- AI-specific position/exposure limits;
- whitelist enforcement;
- Restricted Live execution end-to-end;
- production soak / degradation controls;
- live rollback triggers;
- dedicated AI live kill switch integration.

**Status:** `NOT VERIFIED`

## 17.10. Итог

Restricted Live на текущем этапе:

`DISABLED`

Safety infrastructure, необходимая для будущего этапа, частично существует.

Полноценный Restricted Live operational contour не реализован и не должен считаться активным.

**Remaining:** отдельный Restricted Live factual audit и только после него — controlled implementation.
# 18. AI не должен обходить RiskAgent

**Status:** `TEST VERIFIED`

## 18.1. Канонический production контур

Все AI live decisions должны проходить:

`AI → Strategy Decision → RiskAgent → Protection Validation → ExecutionAgent → Exchange`

AIEA не получает прямого exchange execution authority.

## 18.2. Фактический production path

Подтверждён:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary → BaseExchangeClient.place_order()`

**Status:** `VERIFIED`

**Evidence:**
- `agents/signal_agent.py`
- `strategies/decision_engine.py`
- `agents/ai_risk_agent.py`
- `agents/execution_agent.py`
- `services/execution_boundary.py`

## 18.3. Execution Boundary

`ExecutionBoundary` является технической границей перед exchange execution.

Перед `BaseExchangeClient.place_order()` выполняются safety checks.

**Status:** `VERIFIED`

**Evidence:**
- `services/execution_boundary.py`
- `AIProductionSafetyService`
- global trading kill-switch integration.

## 18.4. AIProductionSafetyService

Фактически существует:

`services/ai_production_safety.py`

Safety layer не должен самостоятельно выполнять exchange execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10 production safety;
- E12 production isolation.

## 18.5. Promotion / permission boundary

AI promotion execution должен требовать:

- соответствующий live promotion stage;
- соответствующее permission;
- approved risk state;
- valid strategy version;
- отсутствие rolled-back state.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5 risk approval;
- E6 permission policy;
- E10 production safety;
- E12 integration.

## 18.6. Запрет прямого вызова ExecutionAgent

Promotion / research services не должны самостоятельно вызывать:

- RiskAgent;
- ExecutionAgent;
- exchange client.

Проверенные сервисы используют аналитический / promotion layer вместо прямого execution.

**Status:** `VERIFIED` в рамках проведённого service boundary audit.

## 18.7. Запрет direct BingX access

AIEA не должен отправлять production orders напрямую в BingX.

Production exchange execution остаётся за `BaseExchangeClient`, доступным через контролируемую execution chain.

**Status:** `VERIFIED` для текущего production architecture.

## 18.8. Protection validation

После открытия production position защита должна быть фактически подтверждена.

Failure path использует:

`close_reason="PROTECTION_FAILSAFE"`

**Status:** `VERIFIED`

**Evidence:** production protection fail-safe audit.

## 18.9. Advisory / Shadow isolation

Advisory / Shadow не должны:

- менять strategy;
- менять signal;
- менять confidence;
- блокировать execution;
- инициировать execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- shadow advisory influence policy;
- E10/E12 production isolation;
- current production safety state.

## 18.10. Production isolation

AIEA-related research, comparison, validation and promotion components не должны превращаться в самостоятельный execution path.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8 production isolation;
- E10 production isolation;
- E12 production isolation.

## 18.11. Итог

Подтверждено:

- единый RiskAgent-controlled production path;
- ExecutionBoundary перед exchange;
- AI Production Safety;
- permission / risk approval gates;
- protection fail-safe;
- advisory/shadow isolation;
- отсутствие самостоятельного execution authority у research/promotion слоя.

**Remaining:** отдельный periodic negative-path audit direct exchange access при появлении новых AIEA компонентов.
# 19. Strategy Registry

**Status:** `PARTIALLY VERIFIED`

## 19.1. Каноническое назначение

Registry должен быть единственным контролируемым источником информации о разрешённых Strategy Versions.

Для каждой версии должны сохраняться:

- strategy;
- version;
- status;
- promotion_level;
- approved_at;
- approved_by;
- parent_version;
- hypothesis_id;
- experiment_id;
- created_by;
- created_at.

## 19.2. Фактически обнаруженная registry infrastructure

Обнаружен:

`strategies/registry.py`

Также существует:

`models/ai_strategy_version.py`

и promotion-specific version state.

**Status:** `VERIFIED` для существования registry/version infrastructure.

**Evidence:**
- `strategies/registry.py`
- `models/ai_strategy_version.py`

## 19.3. AI Strategy Version

AI Strategy Version является отдельной persistent сущностью и используется в experiment / validation / promotion identity chains.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E4 exact evidence binding;
- E12 promotion chain.

## 19.4. Strategy status lifecycle

Канонически должны различаться:

- `DRAFT`;
- `VALIDATED`;
- `ACTIVE`;
- `DEPRECATED`;
- `ROLLED_BACK`;
- `REJECTED`.

Production Registry не должен позволять заменить ACTIVE version без Promotion Pipeline.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- `models/ai_strategy_version.py`;
- E6 promotion permission policy;
- E8/E9 rollback state.

**Remaining:** отдельная exhaustive audit status transition matrix.

## 19.5. Promotion level

Strategy Version содержит promotion state, используемый вместе с controlled promotion policy.

Stage/level mismatch блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 stage/level tests;
- E10 production safety.

## 19.6. Approved metadata

Promotion audit сохраняет approval metadata:

- approver;
- timestamp;
- target stage;
- target level;
- evidence;
- risk approval;
- strategy definition hash.

**Status:** `TEST VERIFIED`

**Evidence:** E7 promotion audit snapshot.

## 19.7. ACTIVE version protection

Новая version не должна автоматически заменить ACTIVE version.

Promotion manager и permission layer создают controlled boundary.

Rollback также сохраняет предыдущую доказанную version.

**Status:** `TEST VERIFIED`

**Evidence:**
- E1 promotion manager;
- E6 permission policy;
- E8 parent preservation;
- E9 genealogy integrity.

## 19.8. Registry ↔ Genealogy

Каждая новая version должна иметь parent relationship, когда она является эволюцией существующей strategy.

**Status:** `TEST VERIFIED`

**Evidence:**
- E9 genealogy tests;
- `models/ai_strategy_version.py`.

## 19.9. Registry ↔ Hypothesis / Experiment

AI-generated or modified version должна быть связана с:

`hypothesis_id`
`experiment_id`

Эта identity chain уже используется promotion subsystem.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 hypothesis/experiment/version chain;
- E11/E12 identity checks.

## 19.10. Production registry authority

Registry должен предотвращать несанкционированную активацию Strategy Version.

Promotion permission и production safety layers обеспечивают значительную часть этой границы.

Полный direct-mutation audit registry отдельно не выполнен.

**Status:** `PARTIALLY VERIFIED`

## 19.11. Итог

Подтверждены:

- Strategy Registry infrastructure;
- AI Strategy Version;
- promotion level;
- genealogy linkage;
- hypothesis/experiment linkage;
- approval metadata;
- ACTIVE version protection через promotion boundary.

Не закрыты полностью:

- exhaustive registry status machine;
- полный direct-mutation negative-path audit;
- единый runtime источник разрешённой production version для всех consumers.

**Remaining:** отдельный factual audit полного Strategy Registry lifecycle.
# 20. Genealogy

**Status:** `TEST VERIFIED`

## 20.1. Каноническое требование

Для каждой эволюции стратегии должна сохраняться полная lineage:

- strategy_id;
- version;
- parent_strategy_id;
- parent_version;
- created_by;
- created_at;
- hypothesis_id;
- experiment_id.

Новая версия не должна уничтожать или изменять parent version.

## 20.2. Фактическая genealogy infrastructure

Genealogy реализована через versioned Strategy Version и `parent_version_id`.

Используются:

- `models/ai_strategy_version.py`;
- `services/ai_promotion_rollback.py`;
- promotion integrity checks.

**Status:** `VERIFIED`

## 20.3. Parent strategy validation

Rollback / promotion integrity проверяет:

- наличие parent;
- same strategy;
- same hypothesis;
- корректный promotion stage;
- корректный promotion level;
- approval metadata;
- допустимый parent status.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_VALID_GENEALOGY_FIXTURE_OK`
- `E9_PARENT_REQUIRED_BLOCKED_OK`
- `E9_HYPOTHESIS_MISMATCH_BLOCKED_OK`
- `E9_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E9_PARENT_APPROVAL_REQUIRED_OK`
- `E9_PARENT_STATUS_MISMATCH_BLOCKED_OK`

## 20.4. Parent preservation

Rollback не должен изменять или удалять предыдущую доказанную version.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_PARENT_VERSION_PRESERVED_OK`
- `E9_PARENT_PRESERVED_OK`

## 20.5. History preservation

Экспериментальная и validation history не должна удаляться при rollback.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_HISTORY_PRESERVED_OK`
- `E9_ROLLBACK_AUDIT_INTEGRITY_OK`

## 20.6. Rollback genealogy

Rollback происходит только к доказанному parent через контролируемую genealogy.

Повторный rollback уже rolled-back версии блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLBACK_EXECUTED_OK`
- `E8_ROLLED_BACK_PERMISSION_REVOKED_OK`
- `E9_VALID_ROLLBACK_OK`
- `E9_SECOND_ROLLBACK_BLOCKED_OK`

## 20.7. Hypothesis / Experiment genealogy

Strategy Version genealogy должна сохранять связь:

`Parent Version → Hypothesis → Experiment → New Version`

Эта identity chain интегрирована в promotion layer.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E11/E12 identity checks.

## 20.8. Immutable lineage

История эволюции должна быть восстанавливаема без переписывания parent records.

Тесты подтверждают сохранение parent и rollback history.

**Status:** `TEST VERIFIED`

## 20.9. Не полностью закрыто

Не доказаны отдельно:

- визуализация полного genealogy tree;
- query/API для полного lineage traversal;
- массовая проверка genealogy всех существующих Strategy Versions;
- защита от циклических lineage records на уровне всей БД.

**Status:** `PARTIALLY VERIFIED`

## 20.10. Итог

Genealogy foundation фактически реализован и защищён тестами.

Закрыто:

- parent linkage;
- strategy/hypothesis consistency;
- stage/level consistency;
- parent approval;
- parent preservation;
- rollback integrity;
- history preservation.

Остаётся:

- полный lineage traversal audit;
- cycle detection;
- API/reporting полного дерева genealogy.

**Remaining:** расширенный factual audit genealogy graph/runtime consumers.
# 21. AI Memory

**Status:** `TEST VERIFIED`

## 21.1. Каноническое назначение

AI Memory должна хранить долговременные research lessons и observations:

- market observations;
- successful hypotheses;
- failed hypotheses;
- strategy versions;
- experiments;
- performance patterns;
- regime behaviour;
- symbol behaviour;
- risk lessons;
- News/Event lessons;
- validation failures;
- promotion / rollback history.

Memory используется для следующих research cycles и hypothesis generation.

## 21.2. Фактическая реализация

Обнаружены:

- `services/ai_memory.py`;
- `models/ai_lesson.py`;
- `models/ai_agent.py`.

Основная сущность памяти — `AILesson`.

## 21.3. Lesson recording

Тест B4 подтверждает создание lesson и его привязку к AI agent.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_AGENT_OK`
- `B4_LESSON_RECORD_OK`

## 21.4. User isolation

Memory должна быть изолирована по user.

B4 проверяет отсутствие утечки lessons между пользователями.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_USER_MEMORY_ISOLATION_OK`

## 21.5. Experiment ownership

Memory item может быть связан с experiment только в пределах допустимой identity chain.

Cross-user experiment ownership должен блокироваться.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_EXPERIMENT_OWNERSHIP_OK`

## 21.6. Append-only semantics

AI Memory не должна позволять изменять исторические lessons задним числом.

B4 проверяет отсутствие mutation API:

- `update_lesson`;
- `delete_lesson`.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_APPEND_ONLY_MEMORY_OK`

## 21.7. Research-only boundary

Memory не должна становиться механизмом promotion или production control.

B4 проверяет:

- отсутствие `promotion_level` в lesson;
- lesson type не может использоваться как validation evidence.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_RESEARCH_MEMORY_ONLY_OK`

## 21.8. Experiment-linked memory

Memory должна сохранять `source_experiment_id`, когда lesson получен из конкретного experiment.

Это обеспечивает:

`Experiment → Lesson → Future Research`

**Status:** `TEST VERIFIED` в рамках B4 ownership test.

## 21.9. Контекст lesson

Каноническая структура предусматривает:

- lesson_id;
- context;
- observation;
- hypothesis;
- result;
- confidence;
- source_experiment_id;
- created_at.

Фактическая модель `AILesson` существует.

**Status:** `PARTIALLY VERIFIED`

**Remaining:** полный schema audit всех memory fields.

## 21.10. Memory integration с Knowledge / Hypothesis

Memory должна использоваться следующим research cycle.

Фактическая интеграция memory → Knowledge / Hypothesis generation отдельно не доказана.

**Status:** `PARTIALLY VERIFIED`

## 21.11. Historical integrity

Memory не должна позволять AI переписывать historical knowledge.

Append-only test подтверждает основную boundary.

**Status:** `TEST VERIFIED`

## 21.12. Cleanup / test isolation

B4 fixture cleanup подтверждён.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_CLEANUP_OK`

## 21.13. Итог

Подтверждены:

- AI agent memory;
- lesson recording;
- user isolation;
- experiment ownership;
- append-only semantics;
- research-only boundary;
- cleanup.

Частично требуют проверки:

- полная schema coverage;
- фактическое использование memory в следующем research cycle;
- интеграция Memory → Knowledge → Hypothesis.

**Remaining:** audit downstream memory consumers и полного lesson schema.
# 22. Learning Loop

**Status:** `PARTIALLY VERIFIED`

## 22.1. Канонический цикл

AIEA должен поддерживать повторяемый цикл:

`OBSERVE → ANALYZE → HYPOTHESIZE → GENERATE → BACKTEST → VALIDATE → PAPER → SHADOW → COMPARE → LEARN → MODIFY → RETEST`

Каждый цикл должен сохранять входные данные, hypotheses, strategy versions, experiment results и lessons.

## 22.2. Фактически существующие элементы цикла

Обнаружены:

- Knowledge Engine;
- Knowledge Snapshot;
- Hypothesis Engine;
- Experiment Engine;
- Validation Engine;
- Paper infrastructure;
- Shadow infrastructure;
- Comparison Engine;
- AI Memory.

Фактические компоненты:

- `services/ai_knowledge_engine.py`
- `services/ai_knowledge_snapshot_service.py`
- `services/ai_hypothesis_engine.py`
- `services/ai_experiment_engine.py`
- `services/ai_backtest_engine.py`
- `services/ai_oos_validator.py`
- `services/ai_walk_forward_validator.py`
- `services/ai_paper_trading_service.py`
- `services/ai_memory.py`
- comparison services

**Status:** `VERIFIED` для наличия основных компонентов.

## 22.3. Observe / Analyze

Knowledge layer анализирует historical trading data, market context и формирует snapshots.

**Status:** `TEST VERIFIED`

**Evidence:**
- B1 historical analysis;
- B1 data quality;
- Knowledge Snapshot infrastructure.

## 22.4. Hypothesize

Наблюдения передаются в Hypothesis Engine.

`Knowledge Snapshot → Hypothesis`

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_REGIME_CONTRAST_OK`
- `B2_HYPOTHESIS_STRUCTURE_OK`
- `B2_VALIDATION_REQUIRED_OK`

## 22.5. Generate / Modify

Strategy Version infrastructure существует, но полный autonomous generation / modification lifecycle ещё не доказан.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- A9 experiment/version chain;
- Strategy Version model;
- Strategy Genome/static validation infrastructure.

## 22.6. Backtest / Validate

Validation stages фактически реализованы:

`Static → Backtest → OOS → Walk-Forward → Paper → Shadow`

BLOCK D завершён.

**Status:** `TEST VERIFIED`

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 22.7. Compare

Comparison Engine позволяет сопоставлять AI / production / Grid / Baseline участников на сопоставимых market contexts.

**Status:** `DONE + REVIEWED`

**Evidence:** BLOCK F `F.1–F.9`.

## 22.8. Learn / Memory

AI Memory хранит lessons и сохраняет research knowledge для будущего использования.

**Status:** `TEST VERIFIED`

**Evidence:** B4 memory tests.

## 22.9. Modify / Retest

Канонический план требует:

`LEARN → MODIFY → RETEST`

Однако полный автоматический замкнутый цикл:

`lesson → automatic modification → new experiment → retest`

отдельно не подтверждён.

**Status:** `NOT VERIFIED`

## 22.10. Repeatability

Learning Loop должен быть повторяемым и сохранять identity каждого цикла.

Части repeatable pipeline существуют, но отдельной сущности `learning_cycle` и полного cycle-level audit пока не обнаружено в проведённой проверке.

**Status:** `PARTIALLY VERIFIED`

## 22.11. Promotion safety

Learning Loop не должен самостоятельно повышать promotion level.

Promotion остаётся отдельным контролируемым контуром E.1–E.12.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 permission policy;
- E10 production safety;
- E12 integration.

## 22.12. News/Event integration

News & Event Intelligence должна участвовать в:

`OBSERVE → ANALYZE → LEARN`

если исторические/realtime данные доступны.

Полный event-aware learning cycle пока не подтверждён.

**Status:** `NOT VERIFIED`

## 22.13. Итог

Подтверждены отдельные основные компоненты Learning Loop:

- observation;
- analysis;
- hypothesis;
- validation;
- paper;
- shadow;
- comparison;
- memory;
- promotion safety.

Не подтверждены полностью:

- autonomous generate/modify/retest loop;
- отдельная cycle identity;
- automatic lesson → modification feedback;
- полный News/Event-aware learning loop.

**Remaining:** factual audit полного замкнутого Learning Loop.
# 23. Comparison Engine

**Status:** `DONE + TEST VERIFIED`

## 23.1. Назначение

Comparison Engine должен сравнивать:

- AI Strategy;
- Strategy Engine;
- Grid;
- Baseline.

Сравнение должно выполняться на сопоставимых временных точках и market context.

## 23.2. Фактическая реализация

Обнаружены:

- `services/ai_comparison_contract.py`
- `services/ai_comparison_alignment.py`
- `services/ai_comparison_analysis.py`
- `services/ai_comparison_metrics.py`
- `services/ai_comparison_slices.py`
- `services/ai_comparison_stability.py`
- `services/ai_comparison_trade_source.py`
- `services/ai_comparison_news_context.py`
- `services/ai_comparison_persistence.py`

Модели:

- `models/ai_comparison_observation.py`
- `models/ai_comparison_result.py`

## 23.3. Comparison Data Contract

Comparison Observation и Comparison Result являются отдельными аналитическими сущностями.

Ключевой принцип:

`Comparison Observation != Trade`

**Status:** `TEST VERIFIED`

**Evidence:** BLOCK F / F.1.

## 23.4. Identity / Alignment

Сравнение использует сопоставимые:

- symbol;
- market_regime;
- side;
- temporal context.

Alignment является отдельным сервисом.

**Status:** `TEST VERIFIED`

**Evidence:** F.2 + F-REVIEW-1.

## 23.5. Participant separation

Участники comparison разделяются:

- `STRATEGY_ENGINE`;
- `GRID`;
- `AI_SANDBOX`;
- `AI_PAPER`;
- `AI_SHADOW`;
- `AI_LIVE`;
- `MANUAL`;
- `BASELINE`.

`BASELINE` является comparison participant, а не trade_source.

**Status:** `TEST VERIFIED`

**Evidence:** F.6 + F-REVIEW-5.

## 23.6. Required identity dimensions

Comparison поддерживает:

- symbol;
- market_regime;
- side;
- strategy;
- strategy version;
- production strategy;
- production side;
- AI confidence;
- production confidence;
- result.

**Status:** `TEST VERIFIED`

**Evidence:** F.3 + F-REVIEW-1/F-REVIEW-2.

## 23.7. Performance metrics

Comparison должен учитывать:

- PnL;
- win rate;
- profit factor;
- expectancy;
- drawdown;
- stability;
- risk-adjusted characteristics;
- fees;
- funding.

Фактически присутствует metrics layer.

**Status:** `TEST VERIFIED`

**Evidence:** F.4/F.5.

## 23.8. Trade source isolation

Comparison не должен смешивать production и experimental sources.

Есть отдельный:

`services/ai_comparison_trade_source.py`

Source isolation была отдельно reviewed.

**Status:** `TEST VERIFIED`

**Evidence:**
- F.6;
- F-REVIEW-5.

## 23.9. News/Event context

Comparison имеет отдельный News/Event context layer.

Обнаружен:

`services/ai_comparison_news_context.py`

Контекст может включаться в comparison observation.

**Status:** `TEST VERIFIED`

**Evidence:** F.7.

Это не означает завершённый общий News/Event Intelligence pipeline.

## 23.10. Persistence

Фактически существуют:

- `ai_comparison_observations`;
- `ai_comparison_results`.

Persistence сохраняет comparison identity.

**Status:** `TEST VERIFIED`

**Evidence:** F.8 + F-REVIEW-4.

## 23.11. Read-only production boundary

Comparison Engine не должен:

- менять production strategy;
- изменять signal;
- изменять confidence;
- блокировать execution;
- запускать execution.

**Status:** `TEST VERIFIED`

**Evidence:** F.9 + production isolation evidence.

## 23.12. Stability

Comparison имеет отдельный stability analysis layer.

Стабильность является аналитическим/research indicator и не должна автоматически становиться Promotion criterion без соответствующего formal gate.

**Status:** `VERIFIED`

## 23.13. Post-block review

Проведен review:

- Comparison Identity;
- Participant-specific Analytics;
- Alignment Semantics;
- Persistence Identity;
- Source Isolation Guards.

**Status:** `TEST VERIFIED`

**Evidence:**
- `F-REVIEW-1`
- `F-REVIEW-2`
- `F-REVIEW-3`
- `F-REVIEW-4`
- `F-REVIEW-5`

## 23.14. Production independence

Comparison Engine остаётся read-only относительно production.

Production trading не контролируется Comparison Engine.

**Status:** `VERIFIED`

## 23.15. Ограничения

Не следует считать Comparison Engine реализацией полного:

- autonomous Learning Loop;
- Promotion decision;
- News/Event Intelligence;
- live trading control.

Это отдельные архитектурные контуры.

## 23.16. Итог

F.1–F.9 полностью отражены в Audit.

Подтверждены:

- contract;
- identity/alignment;
- symbol × regime × side;
- metrics;
- stability;
- trade_source separation;
- News/Event context;
- persistence;
- read-only analysis;
- post-block review.

**Final status:** `DONE + TEST VERIFIED`

**Evidence:** BLOCK F / F.1–F.9 + F-REVIEW-1…5.
# 24. AI Discovery

**Status:** `PARTIALLY VERIFIED`

## 24.1. Каноническое назначение

AIEA Discovery должен искать:

- новые market patterns;
- комбинации существующих индикаторов;
- regime-specific behaviour;
- failure patterns;
- успешные комбинации стратегий;
- различия LONG/SHORT;
- различия symbol;
- volatility-dependent behaviour;
- time-dependent behaviour;
- news-dependent behaviour;
- event-dependent behaviour;
- повторяющиеся причины убытков;
- повторяющиеся причины успешных сделок.

Обнаруженная закономерность должна превращаться в формализованную hypothesis и проверяться через Experiment Engine.

## 24.2. Existing discovery inputs

Knowledge Engine уже формирует аналитические разрезы, которые могут служить входом Discovery:

- strategy × regime;
- strategy × symbol;
- strategy × side;
- strategy × regime × side;
- strategy × volatility;
- strategy × confidence;
- symbol × regime;
- temporal slices;
- holding time;
- leverage.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B1_REQUIRED_SLICES_OK`
- `B1_OPTIONAL_SLICES_OK`
- `B1_AGGREGATION_OK`

## 24.3. Discovery → Hypothesis

Hypothesis Engine существует и способен преобразовать исследовательское наблюдение в формализованную hypothesis.

Цепочка:

`Observation → Knowledge Snapshot → Hypothesis`

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_REGIME_CONTRAST_OK`
- `B2_HYPOTHESIS_STRUCTURE_OK`
- `B2_VALIDATION_REQUIRED_OK`

## 24.4. Correlation versus proof

Discovery не должна считать correlation доказанной causal relationship.

Hypothesis должна проходить Experiment / Validation pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_VALIDATION_REQUIRED_OK`;
- validation pipeline;
- Experiment Engine.

## 24.5. Hypothesis deduplication

План требует избегать большого количества практически одинаковых hypotheses.

Похожие hypotheses должны группироваться и сравниваться.

Отдельный полноценный similarity / clustering / deduplication service в текущем factual audit не подтверждён.

**Status:** `NOT VERIFIED`

## 24.6. Failure pattern discovery

Knowledge / research infrastructure позволяет анализировать отрицательные результаты и performance slices.

Однако самостоятельный автоматический failure-pattern discovery engine отдельно не доказан.

**Status:** `PARTIALLY VERIFIED`

## 24.7. Success pattern discovery

Аналогично, performance analytics могут предоставлять данные для поиска успешных patterns.

Отдельный автоматический discovery lifecycle:

`detect → rank → hypothesize`

ещё не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 24.8. Regime / symbol / side discovery

Required dimensions поддерживаются Knowledge Engine.

**Status:** `TEST VERIFIED`

**Evidence:** B1 required/optional slices.

## 24.9. News/Event discovery

Канонический план требует event/news-dependent discovery.

B.5 является активным research-only track, однако полный автоматический discovery по событиям ещё не закрыт.

**Status:** `PARTIALLY VERIFIED`

**Remaining:**
- event history;
- event grouping;
- event → market pattern discovery;
- event → strategy pattern discovery;
- event → outcome analysis;
- statistical confirmation.

## 24.10. Discovery → Experiment

Любая обнаруженная закономерность должна становиться проверяемой hypothesis и далее experiment.

Hypothesis/Experiment linkage существует.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 hypothesis/experiment/version chain;
- B2 validation-required boundary.

## 24.11. Discovery safety

Discovery должен оставаться research-only.

Он не должен:

- менять production strategy;
- отправлять orders;
- bypass RiskAgent;
- bypass ExecutionAgent;
- самостоятельно promote strategy.

**Status:** `VERIFIED`

**Evidence:**
- B2 no strategy mutation;
- A8/E10 production isolation.

## 24.12. Итог

Подтверждены:

- аналитические входы для discovery;
- Knowledge slices;
- Observation → Hypothesis;
- correlation → validation boundary;
- regime/symbol/side discovery inputs;
- Hypothesis → Experiment linkage;
- research-only boundary.

Не подтверждены полностью:

- самостоятельный Discovery Engine;
- hypothesis deduplication/clustering;
- automatic failure/success pattern ranking;
- complete News/Event discovery;
- автоматический discovery → experiment orchestration.

**Remaining:** отдельный factual audit полного AI Discovery lifecycle.
# 25. Новые стратегии от AI

**Status:** `PARTIALLY VERIFIED`

## 25.1. Каноническая цепочка

Для новой AI-generated strategy требуется:

`AI-generated strategy → unique ID → version → hypothesis → implementation → tests → backtest → OOS → walk-forward → paper → shadow → evaluation → promotion`

Без прохождения обязательных стадий strategy не должна попадать в Production.

## 25.2. Strategy Version infrastructure

Фактически существует:

- `models/ai_strategy_version.py`;
- `services/ai_experiment_engine.py`;
- validation services;
- promotion services.

A9 подтверждает связывание experiment с конкретной Strategy Version.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- E12 promotion integration.

## 25.3. Unique strategy identity

AI strategy должна иметь уникальную identity и отдельную version.

Strategy Version является persistent объектом и не должна заменять существующую version.

**Status:** `VERIFIED`

**Evidence:**
- `models/ai_strategy_version.py`;
- E8/E9 genealogy integrity.

## 25.4. Hypothesis linkage

Новая strategy должна быть связана с hypothesis.

Фактическая identity chain:

`Snapshot → Hypothesis → Experiment → StrategyVersion`

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_SNAPSHOT_OK`
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`

## 25.5. Experiment linkage

Новая strategy должна создаваться в рамках контролируемого experiment.

Experiment model и engine существуют.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 experiment/version chain;
- E12 promotion integration.

## 25.6. Strategy Genome requirement

Новая стратегия должна иметь machine-readable Strategy Genome.

Static validation поддерживает Strategy Definition / Genome schema.

Полная автоматическая генерация Genome для новой стратегии не доказана.

**Status:** `PARTIALLY VERIFIED`

## 25.7. Implementation / sandbox boundary

AI-generated implementation не должна получать production Python execution authority.

Static validation и downstream sandbox/research infrastructure существуют.

Полный доказанный generated-code sandbox lifecycle отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 25.8. Validation lifecycle

Downstream validation infrastructure существует:

- Static Validation;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow.

BLOCK D завершён.

Однако автоматическая orchestration именно для каждой newly generated strategy:

`generate → validate all stages`

отдельно не доказана.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 25.9. Evaluation

AI-generated strategy должна оцениваться отдельно по:

- PnL;
- win rate;
- profit factor;
- expectancy;
- drawdown;
- Sharpe / Sortino;
- stability;
- source;
- regime;
- symbol;
- side.

Metrics/evaluation infrastructure существует.

**Status:** `TEST VERIFIED`

**Evidence:**
- B3 canonical metrics;
- comparison infrastructure.

## 25.10. Production promotion boundary

AI-generated strategy не должна самостоятельно считаться production-ready.

Promotion requires controlled:

- validation evidence;
- formal gates;
- risk approval;
- permissions;
- audit.

**Status:** `TEST VERIFIED`

**Evidence:**
- E3 formal gates;
- E4 evidence binding;
- E5 risk approval;
- E6 permissions;
- E10 safety;
- E12 integration.

## 25.11. Autonomous creation

Не подтверждены отдельно:

- AI strategy generation engine;
- automatic strategy ID allocation;
- automatic Genome construction;
- automatic implementation generation;
- automatic test generation;
- automatic experiment creation immediately after generation;
- automatic full validation launch;
- automatic evaluation and ranking;
- automatic promotion request.

**Status:** `NOT VERIFIED`

## 25.12. Production isolation

Даже при наличии generated strategy infrastructure production permissions не выдаются автоматически.

**Status:** `VERIFIED`

**Evidence:**
- E6 permission policy;
- E10 production safety;
- E12 production isolation.

## 25.13. Итог

Подтверждены:

- Strategy Version infrastructure;
- hypothesis linkage;
- experiment linkage;
- validation infrastructure;
- metrics/evaluation;
- production permission boundary.

Частично подтверждены:

- Genome integration;
- sandbox boundary;
- generated-strategy validation orchestration.

Не подтверждён полностью:

- автономный lifecycle создания новой стратегии от AI до promotion request.

**Remaining:** отдельный factual audit autonomous Strategy Generation lifecycle.
# 26. Изменение существующих стратегий

**Status:** `NOT VERIFIED`

**Canonical requirement:**

AI может предложить:

* parameter change;
* rule addition;
* rule removal;
* entry modification;
* exit modification;
* filter modification;
* regime restriction;
* volatility restriction;
* volume filter;
* confidence threshold;
* risk/reward model change;
* SL model change;
* TP model change;
* News/Event filter;
* News/Event risk restriction.

Каждое изменение создаёт новую версию.

Существующая production-версия никогда не изменяется.

Для каждого изменения сохранять:

* parent strategy;
* parent version;
* hypothesis_id;
* experiment_id;
* Strategy Genome до изменения;
* Strategy Genome после изменения;
* причину изменения;
* ожидаемый эффект;
* фактический эффект;
* результаты validation.

Изменение стратегии не может попасть в production без полного прохождения Promotion Pipeline.

---

**Evidence:** NOT YET MAPPED

**Verification:** REQUIRED

**Remaining:** фактический code / DB / runtime / test audit.

# 27. Rollback

**Status:** `TEST VERIFIED / DONE`

## 27.1. Каноническое требование

Rollback должен возвращать предыдущую доказанную Strategy Version без изменения исторических данных.

При degradation или risk breach контролируемый rollback должен:

- сохранить текущую version;
- определить предыдущую доказанную version;
- перевести текущую version в `ROLLED_BACK`;
- восстановить допустимую предыдущую version;
- отозвать permissions rolled-back version;
- сохранить audit trail;
- не удалять experiment / hypothesis / paper / shadow / live history.

## 27.2. Фактическая реализация

Обнаружен отдельный сервис:

`services/ai_promotion_rollback.py`

Rollback является частью Promotion Pipeline.

**Status:** `VERIFIED`

## 27.3. Genealogy-based rollback

Rollback допускается только через существующую genealogy и parent version.

Проверяются:

- parent existence;
- same strategy;
- same hypothesis;
- stage / level consistency;
- parent approval;
- parent status.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_VALID_GENEALOGY_FIXTURE_OK`
- `E9_PARENT_REQUIRED_BLOCKED_OK`
- `E9_HYPOTHESIS_MISMATCH_BLOCKED_OK`
- `E9_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E9_PARENT_APPROVAL_REQUIRED_OK`
- `E9_PARENT_STATUS_MISMATCH_BLOCKED_OK`

## 27.4. Rollback execution

Rollback operation создаёт controlled state transition.

Текущая version не удаляется.

Предыдущая доказанная version сохраняется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLBACK_EXECUTED_OK`
- `E8_PARENT_VERSION_PRESERVED_OK`

## 27.5. Permission revocation

После rollback rolled-back version должна потерять promotion permissions.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLED_BACK_PERMISSION_REVOKED_OK`

## 27.6. Rollback audit

Rollback создаёт отдельную audit record/snapshot с информацией о переходе.

Должны сохраняться как минимум:

- source version;
- target/parent version;
- stage;
- level;
- reason;
- actor;
- timestamp;
- experiment context.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLBACK_AUDIT_OK`
- `E9_ROLLBACK_AUDIT_INTEGRITY_OK`

## 27.7. History preservation

Rollback не должен удалять:

- experiment;
- hypothesis;
- validation evidence;
- paper;
- shadow;
- audit history.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_HISTORY_PRESERVED_OK`

## 27.8. Repeated rollback protection

Повторный rollback уже rolled-back version должен блокироваться.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_SECOND_ROLLBACK_BLOCKED_OK`

## 27.9. Production isolation

Rollback service не должен напрямую выполнять exchange operations.

Production execution остаётся за контролируемым execution boundary.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_PRODUCTION_ISOLATION_OK`
- `E9_PRODUCTION_ISOLATION_OK`

## 27.10. Automatic rollback policy

Канонический план допускает automatic rollback только по заранее утверждённым:

- degradation criteria;
- risk breach criteria.

AI не должен менять rollback criteria.

Полный автоматический degradation-triggered runtime rollback отдельно не доказан.

**Status:** `PARTIALLY VERIFIED`

## 27.11. Rollback integrity

E.9 дополнительно обеспечивает:

- parent integrity;
- strategy consistency;
- hypothesis consistency;
- stage/level integrity;
- approval integrity;
- status integrity;
- audit integrity.

**Status:** `TEST VERIFIED`

## 27.12. Итог

Подтверждены:

- rollback service;
- genealogy-based rollback;
- parent preservation;
- permission revocation;
- rollback audit;
- history preservation;
- repeated rollback protection;
- production isolation;
- rollback integrity.

Частично остаётся:

- fully automatic degradation/risk-triggered rollback runtime.

**Final status:** `DONE + TEST VERIFIED`

**Remaining:** при будущей активации Restricted Live отдельно проверить runtime degradation-triggered rollback.
# 28. Kill Switch

**Status:** `PARTIALLY VERIFIED`

## 28.1. Каноническое требование

Для AIEA должны существовать отдельные контролируемые flags:

- `AI_EVOLUTION_ENABLED`;
- `AI_PAPER_ENABLED`;
- `AI_SHADOW_ENABLED`;
- `AI_ADVISORY_ENABLED`;
- `AI_LIVE_ENABLED`;
- `AI_LIVE_KILL_SWITCH`.

Kill switch должен иметь более высокий приоритет, чем AI decisions.

При активации AI live execution должен быть запрещён.

## 28.2. Production trading kill-switch

В production execution path уже существует общий trading kill-switch.

`ExecutionBoundary` проверяет возможность размещения нового order через:

`allow_new_order()`

**Status:** `VERIFIED`

**Evidence:**
- `services/execution_boundary.py`;
- production execution boundary audit.

## 28.3. AI Production Safety

Фактически существует:

`services/ai_production_safety.py`

Safety layer является отдельной защитой перед production execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10 production safety;
- E12 production isolation.

## 28.4. AI-specific enable flags

Канонический план требует отдельные AI lifecycle flags.

В проведённом audit не подтверждён полный набор и единый enforcement всех:

- `AI_EVOLUTION_ENABLED`;
- `AI_PAPER_ENABLED`;
- `AI_SHADOW_ENABLED`;
- `AI_ADVISORY_ENABLED`;
- `AI_LIVE_ENABLED`.

**Status:** `NOT VERIFIED`

## 28.5. AI_LIVE_KILL_SWITCH

Отдельный AI-specific live kill switch должен:

- запрещать новые AI live trades;
- блокировать promotion/activation при необходимости;
- иметь приоритет над AI decision;
- не закрывать существующие позиции автоматически без отдельной risk policy.

Полная отдельная implementation и runtime verification пока не подтверждены.

**Status:** `NOT VERIFIED`

## 28.6. Kill switch audit trail

Каноническое требование предусматривает:

- actor;
- activation time;
- deactivation time;
- reason;
- state before;
- state after.

Отдельный полный audit lifecycle для AI kill switch пока не подтверждён.

**Status:** `NOT VERIFIED`

## 28.7. Promotion interaction

Kill switch не должен позволять AIEA активировать новую live strategy или повышать permission при отключённом AI live path.

Promotion infrastructure уже fail-closed, но отдельная integration с dedicated AI kill switch не доказана.

**Status:** `PARTIALLY VERIFIED`

## 28.8. Existing positions

Kill switch должен запрещать новые AI live entries, при этом существующие позиции должны продолжать управляться обычным Risk/Execution контуром, если иное не определено risk policy.

Такое поведение отдельным AI kill-switch runtime тестом не подтверждено.

**Status:** `NOT VERIFIED`

## 28.9. Priority

Kill switch должен иметь приоритет над любыми AI решениями.

Production safety boundary уже является fail-closed перед exchange execution.

Однако отдельная proof priority для dedicated AI kill switch отсутствует.

**Status:** `PARTIALLY VERIFIED`

## 28.10. Production isolation

Kill switch не должен предоставлять AIEA прямой доступ к exchange или позволять обходить RiskAgent / ExecutionAgent.

**Status:** `VERIFIED`

**Evidence:**
- E10;
- E12;
- ExecutionBoundary.

## 28.11. Итог

Подтверждены:

- production trading kill-switch;
- AI Production Safety;
- fail-closed execution boundary;
- production isolation.

Не подтверждены полностью:

- полный набор AI lifecycle flags;
- dedicated `AI_LIVE_KILL_SWITCH`;
- dedicated kill-switch audit trail;
- runtime priority semantics;
- behaviour для уже открытых AI positions.

**Remaining:** отдельный factual audit и implementation verification dedicated AIEA Kill Switch.
# 29. Аудит

**Status:** `PARTIALLY VERIFIED`

## 29.1. Каноническое требование

Каждое существенное действие AIEA должно иметь неизменяемую audit trail.

Минимально должны сохраняться:

- timestamp;
- agent;
- agent_version;
- model;
- model_version;
- prompt_version;
- input_snapshot;
- decision;
- strategy;
- strategy_version;
- confidence;
- reasoning_summary;
- hypothesis_id;
- experiment_id;
- validation_stage;
- result;
- created_at.

Audit должен позволять восстановить цепочку:

`market context → observation → hypothesis → strategy version → experiment → validation → decision → promotion → production result`

## 29.2. Фактическая audit infrastructure

Обнаружена модель:

`models/ai_audit_log.py`

Также audit используется в Promotion Pipeline:

- `services/ai_promotion_audit.py`;
- promotion snapshots;
- rollback audit.

**Status:** `VERIFIED`

## 29.3. AI action logging

AI audit model предназначена для хранения действий/решений AIEA.

Факт полного покрытия всех AI actions отдельным exhaustive runtime audit ещё не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 29.4. Promotion audit

Promotion audit trail полностью реализован и сохраняет исторический snapshot.

Фиксируются:

- user;
- experiment;
- hypothesis;
- strategy version;
- previous/target stage;
- previous/target level;
- approver;
- timestamp;
- strategy definition hash;
- evidence binding;
- risk approval;
- permission state.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E7_PROMOTION_AUDIT_SNAPSHOT_OK`
- `E7_AUDIT_TRIPLE_SNAPSHOT_OK`
- `E7_HISTORICAL_SNAPSHOT_STABLE_OK`
- `E7_PRODUCTION_ISOLATION_OK`

## 29.5. Rollback audit

Rollback создаёт отдельную audit record.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_ROLLBACK_AUDIT_OK`
- `E9_ROLLBACK_AUDIT_INTEGRITY_OK`

## 29.6. Immutable audit history

Audit history не должна зависеть от последующих mutation StrategyVersion или experiment state.

Promotion snapshot stability уже проверена.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E7_HISTORICAL_SNAPSHOT_STABLE_OK`

## 29.7. Identity binding

Audit records должны быть связаны с правильными:

- user;
- hypothesis;
- experiment;
- strategy version.

Identity isolation реализована в A8/E11.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8 cross-user isolation;
- E11 identity isolation;
- E7 promotion snapshot.

## 29.8. AI model version

Каждое AI decision должно сохранять версию AI model.

Модель `ai_audit_log` существует, однако полный factual audit заполнения:

- `model`;
- `model_version`;
- `agent_version`;
- `prompt_version`

для всех AI actions не проведён.

**Status:** `PARTIALLY VERIFIED`

## 29.9. Input snapshot

Audit должен сохранять input snapshot, достаточный для последующего восстановления контекста решения.

Promotion audit уже сохраняет snapshots.

Полное покрытие обычных research decisions отдельно не подтверждено.

**Status:** `PARTIALLY VERIFIED`

## 29.10. Reasoning summary

Каноническое требование предусматривает `reasoning_summary`.

Наличие поля/инфраструктуры не доказывает, что оно стабильно заполняется для каждого AI action.

**Status:** `PARTIALLY VERIFIED`

## 29.11. Audit immutability

AI не должен изменять или удалять исторические audit records.

Promotion audit snapshots являются историческими.

Полный negative-path audit mutation/delete для всех audit records ещё не выполнен.

**Status:** `PARTIALLY VERIFIED`

## 29.12. Audit → Production traceability

Цепочка до production должна сохранять:

`AI → promotion → permission → production result`

Promotion E.1–E.12 обеспечивает значительную часть этой трассируемости.

Однако end-to-end proof до фактического production trade результата для AI Live пока невозможен, поскольку Restricted Live и Full Live отключены.

**Status:** `PARTIALLY VERIFIED`

## 29.13. Research / validation audit

Research, validation и experiments имеют persistent models/services.

Полное унифицированное audit coverage всех research actions пока не доказано.

**Status:** `PARTIALLY VERIFIED`

## 29.14. Audit isolation

Audit не должен давать AI возможность:

- менять production;
- обходить RiskAgent;
- обходить ExecutionAgent;
- самостоятельно повышать permissions.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8 production isolation;
- E6;
- E10;
- E12.

## 29.15. Итог

Подтверждены:

- AI audit model;
- promotion audit;
- rollback audit;
- historical snapshot stability;
- identity binding;
- production isolation.

Частично подтверждены:

- exhaustive AI action logging;
- model/prompt version coverage;
- input snapshot coverage;
- reasoning summary coverage;
- universal audit immutability;
- full research-to-production traceability.

**Remaining:** полный audit coverage / immutability / model-version population audit.
# 30. Безопасность AI-generated Code

**Status:** `PARTIALLY VERIFIED`

## 30.1. Каноническое требование

Production не должен исполнять необработанный AI-generated Python.

Для generated code требуется sandbox с:

- container isolation;
- CPU limit;
- memory limit;
- timeout;
- filesystem isolation;
- network disabled;
- allowed imports whitelist;
- ограниченными system calls;
- отсутствием production credentials;
- отсутствием Docker socket;
- отсутствием прямого доступа к production database;
- отсутствием прямого доступа к BingX;
- отсутствием прямого доступа к RiskAgent / ExecutionAgent.

## 30.2. Static Strategy Validation

Фактически существует:

`services/ai_static_strategy_validator.py`

Validator проверяет:

- structure;
- required fields;
- allowed parameters;
- forbidden operations;
- production/exchange isolation;
- RiskAgent restrictions;
- ExecutionAgent restrictions;
- Strategy Definition / Genome schema.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK D / D.1 static validation;
- forbidden operations tests;
- malformed definition tests;
- validation gate integration.

## 30.3. Forbidden operations

Static validation содержит запреты на опасные операции, включая обращения к execution/risk/exchange слоям.

**Status:** `VERIFIED`

**Evidence:**
- `services/ai_static_strategy_validator.py`.

## 30.4. Generated strategy production boundary

Generated strategy не должна автоматически получать production permission.

Promotion layer требует:

- validation evidence;
- formal gate;
- risk approval;
- permission;
- production safety.

**Status:** `TEST VERIFIED`

**Evidence:**
- E3;
- E4;
- E5;
- E6;
- E10;
- E12.

## 30.5. Sandbox execution

Каноническое требование предусматривает выполнение generated code только внутри изолированного sandbox.

В текущем factual audit отдельный production-grade sandbox executor с доказанными:

- CPU limits;
- memory limits;
- timeout;
- network isolation;
- filesystem isolation;
- import whitelist;
- syscall restrictions

не подтверждён.

**Status:** `NOT VERIFIED`

## 30.6. Secrets isolation

Generated code не должно получать production credentials или secrets.

Отдельный dedicated runtime proof secrets isolation для generated code пока не проведён.

**Status:** `NOT VERIFIED`

## 30.7. Filesystem isolation

Generated code не должен получать доступ к production filesystem.

Static validator ограничивает strategy definition operations, но этого недостаточно как доказательство runtime filesystem isolation.

**Status:** `NOT VERIFIED`

## 30.8. Network isolation

Generated code не должен выполнять произвольные network calls.

Static validation может блокировать известные запрещённые operations, но отдельная runtime network isolation не доказана.

**Status:** `NOT VERIFIED`

## 30.9. Database isolation

Generated code не должен иметь прямого доступа к production database credentials.

Отдельный controlled interface для sandbox database access не подтверждён полным runtime audit.

**Status:** `NOT VERIFIED`

## 30.10. Docker isolation

Generated code не должен иметь доступ к Docker socket или host-level control.

Отдельный sandbox runtime proof отсутствует.

**Status:** `NOT VERIFIED`

## 30.11. Resource limits

Обязательны:

- CPU;
- memory;
- timeout.

Фактический isolated execution manager с доказанными hard limits в текущем audit не подтверждён.

**Status:** `NOT VERIFIED`

## 30.12. Sandbox → Validation

Generated strategy должна сначала пройти static validation и только после этого попасть в следующий controlled stage.

Static validation gate существует и интегрирован в validation pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- D.1 validation gate;
- malformed/forbidden strategy tests.

## 30.13. Sandbox → Production

Даже после sandbox execution generated strategy не получает production execution authority автоматически.

**Status:** `TEST VERIFIED`

**Evidence:**
- E6 permissions;
- E10 production safety;
- E12 integration.

## 30.14. Итог

Подтверждены:

- static validation;
- forbidden operations guard;
- Strategy Definition / Genome validation;
- production permission boundary;
- validation-before-promotion principle.

Не подтверждены:

- полноценный runtime sandbox;
- resource limits;
- filesystem isolation;
- network isolation;
- secrets isolation;
- database isolation;
- Docker socket isolation;
- complete generated-code execution lifecycle.

**Remaining:** отдельный factual/security audit sandbox runtime architecture.
# 31. Database Model

**Status:** `PARTIALLY VERIFIED`

## 31.1. Каноническое требование

Database model должна поддерживать:

- AI agents;
- hypotheses;
- strategy versions;
- experiments;
- experiment results;
- paper trades;
- shadow decisions;
- lessons;
- audit trail;
- validation evidence;
- News/Event context;
- comparison;
- promotion / rollback;
- multi-user isolation;
- versioning / genealogy.

## 31.2. AI Agent

Фактически существует:

`models/ai_agent.py`

Должны храниться как минимум:

- id;
- name;
- version;
- status;
- trust_level;
- model;
- created_at;
- updated_at.

`trust_level` фактически используется как отдельное поле AI identity.

**Status:** `VERIFIED`

## 31.3. AI Hypothesis

Фактически существует:

`models/ai_hypothesis.py`

Hypothesis является отдельной persistent сущностью и используется в identity chain.

**Status:** `TEST VERIFIED`

**Evidence:**
- B2 hypothesis tests;
- A9 hypothesis identity chain;
- E11 isolation evidence.

## 31.4. AI Strategy Version

Фактически существует:

`models/ai_strategy_version.py`

Version используется в:

`Hypothesis → Experiment → Validation → Promotion`

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`;
- E4/E9/E12.

## 31.5. AI Experiment

Фактически существует:

`models/ai_experiment.py`

Experiment связывает:

- hypothesis;
- strategy version;
- user;
- dataset / parameters;
- lifecycle.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 experiment/version chain;
- A8 ownership isolation;
- E12 promotion chain.

## 31.6. AI Experiment Result

Фактически существует:

`models/ai_experiment_result.py`

Используется для хранения validation / evaluation metrics.

**Status:** `VERIFIED`

## 31.7. AI Paper Trade

Фактически существует:

`models/ai_paper_trade.py`

Paper infrastructure отделена от production execution.

**Status:** `VERIFIED`

## 31.8. AI Shadow Decision

Фактически существует:

`models/ai_shadow_decision.py`

Также существует additional shadow/advisory infrastructure.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK E shadow infrastructure;
- BLOCK F comparison integration.

## 31.9. AI Lesson / Memory

Фактически существует:

`models/ai_lesson.py`

AI Memory B4 подтверждена тестами.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_LESSON_RECORD_OK`
- `B4_USER_MEMORY_ISOLATION_OK`
- `B4_APPEND_ONLY_MEMORY_OK`

## 31.10. AI Audit Log

Фактически существует:

`models/ai_audit_log.py`

Используется для AI audit / promotion history.

**Status:** `VERIFIED`

## 31.11. AI Validation Evidence

Фактически существует:

`models/ai_validation_evidence.py`

Evidence binding используется Promotion Pipeline.

**Status:** `TEST VERIFIED`

**Evidence:**
- E4 exact evidence binding.

## 31.12. News/Event model

Фактически существует:

`models/ai_news_event.py`

News/Event foundation существует, однако полный ingestion / historical linkage lifecycle ещё не закрыт.

**Status:** `PARTIALLY VERIFIED`

## 31.13. Comparison models

Фактически существуют:

- `models/ai_comparison_observation.py`;
- `models/ai_comparison_result.py`.

Persistence и identity reviewed в BLOCK F.

**Status:** `TEST VERIFIED`

**Evidence:**
- F.8;
- F-REVIEW-4;
- F-REVIEW-5.

## 31.14. Promotion state persistence

Promotion migrations/model fields фактически существуют и используются:

- promotion stage;
- promotion level;
- approval state;
- rollback state;
- audit snapshots.

Миграции включают:

- `b925e8aaa0bf_e1_add_promotion_state_fields.py`;
- `eebb9e6fdbf3_e1_add_promotion_approval_fields.py`;
- `3fe13dcb0b28_e5_add_promotion_risk_approval_state.py`.

**Status:** `TEST VERIFIED`

**Evidence:** E.1–E.12.

## 31.15. User / identity isolation

Database model supports identity chains, которые проверяются через A8/E11.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8 cross-user evidence;
- E11 cross-user identity isolation.

## 31.16. Production trade metadata

`models/position.py` and `models/trade_history.py` фактически содержат:

- strategy;
- market_regime;
- trade_source;
- strategy_version;
- ai_experiment_id;
- ai_decision_id.

**Status:** `VERIFIED`

**Evidence:** model audit.

## 31.17. Migration coverage

AI-related migrations фактически существуют для:

- AIEA foundation;
- knowledge snapshots;
- AI trade metadata;
- shadow quality;
- comparison;
- News/Event;
- user isolation;
- promotion;
- validation evidence.

**Status:** `VERIFIED`

## 31.18. Database schema completeness

Не все канонические database requirements доказаны как полностью реализованные:

- dedicated learning-cycle persistence;
- complete sandbox execution records;
- dedicated AI live risk-budget state;
- dedicated AI kill-switch state/audit;
- complete News/Event linkage schema;
- complete Strategy Genome before/after persistence.

**Status:** `PARTIALLY VERIFIED`

## 31.19. Production database isolation

Research / experiment / promotion services не должны получать unrestricted production database control.

Existing identity and execution boundaries обеспечивают значительную часть separation, но dedicated sandbox DB boundary ещё не закрыт.

**Status:** `PARTIALLY VERIFIED`

## 31.20. Итог

Подтверждены:

- AI Agent;
- Hypothesis;
- Strategy Version;
- Experiment;
- Experiment Result;
- Paper Trade;
- Shadow Decision;
- Lesson / Memory;
- Audit Log;
- Validation Evidence;
- News/Event model foundation;
- Comparison models;
- Promotion persistence;
- production trade AI metadata;
- migration infrastructure;
- user isolation.

Не закрыты полностью:

- learning-cycle persistence;
- sandbox execution persistence;
- AI live risk-budget state;
- dedicated kill-switch state/audit;
- full News/Event relationship schema;
- Genome before/after persistence;
- dedicated database sandbox boundary.

**Remaining:** factual audit database schema completeness и runtime migration/model consistency.
# 32. Связь с существующей моделью NEXUS

**Status:** `PARTIALLY VERIFIED`

## 32.1. Каноническое требование

Для реальных сделок AI-related metadata должна сохраняться без потери данных в цепочке:

`Signal → Risk → Execution → Position → TradeHistory`

Для AI-сделок дополнительно:

- `ai_experiment_id`;
- `ai_decision_id`.

Существующие production fields не должны заменяться AI metadata.

## 32.2. Position model

Фактически `models/position.py` содержит:

- `strategy`;
- `market_regime`;
- `trade_source`;
- `strategy_version`;
- `ai_experiment_id`;
- `ai_decision_id`.

**Status:** `VERIFIED`

**Evidence:** `models/position.py`

## 32.3. TradeHistory model

Фактически `models/trade_history.py` содержит:

- `strategy`;
- `market_regime`;
- `trade_source`;
- `strategy_version`;
- `ai_experiment_id`;
- `ai_decision_id`.

**Status:** `VERIFIED`

**Evidence:** `models/trade_history.py`

## 32.4. Signal layer

`SignalAgent` формирует production decision output с:

- signal;
- confidence;
- strategy;
- regime;
- decision_score.

Strategy и regime передаются дальше по production chain.

**Status:** `VERIFIED`

**Evidence:**
- `agents/signal_agent.py`;
- Strategy Decision Engine audit.

## 32.5. Risk layer

Production execution path использует:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent`

Risk layer находится между strategy decision и execution.

**Status:** `VERIFIED`

**Evidence:**
- `agents/orchestrator.py`;
- `agents/ai_risk_agent.py`;
- production execution boundary audit.

## 32.6. Execution layer

`ExecutionAgent` передаёт в `ExecutionBoundary` production execution parameters и source.

В production path используется:

`source="STRATEGY_ENGINE"`

**Status:** `VERIFIED`

**Evidence:**
- `agents/execution_agent.py`;
- `services/execution_boundary.py`.

## 32.7. Position persistence

После успешного exchange order создаётся Position.

Position model поддерживает AI metadata.

**Status:** `VERIFIED`

**Evidence:** `models/position.py`

## 32.8. TradeHistory persistence

Trade history model поддерживает AI metadata для последующей traceability.

**Status:** `VERIFIED` для schema support.

**Remaining:** отдельный end-to-end runtime proof полного сохранения всех AI fields до TradeHistory.

## 32.9. Strategy Version propagation

AI strategy version должна сохраняться отдельно от strategy name.

Strategy Version infrastructure и promotion identity chain это поддерживают.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`;
- E4/E12 identity evidence.

## 32.10. AI experiment propagation

`ai_experiment_id` присутствует в Position и TradeHistory schema.

Однако full live execution path для AI Live currently disabled, поэтому end-to-end production runtime propagation через реальную AI Live сделку не доказана.

**Status:** `PARTIALLY VERIFIED`

## 32.11. AI decision propagation

`ai_decision_id` присутствует в Position и TradeHistory schema.

Full runtime propagation through an enabled AI Live execution path не подтверждена.

**Status:** `PARTIALLY VERIFIED`

## 32.12. Metadata integrity

AI metadata не должна заменять:

- strategy;
- strategy version;
- market regime;
- trade source;
- standard production trade fields.

Schema и production boundary допускают хранение дополнительных AI fields.

**Status:** `VERIFIED` на уровне model/boundary design.

## 32.13. Production isolation

AI metadata fields сами по себе не дают AIEA direct execution authority.

Promotion / execution safety layers сохраняют production boundary.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10;
- E12;
- production execution boundary.

## 32.14. Итог

Подтверждены:

- AI metadata fields в Position;
- AI metadata fields в TradeHistory;
- strategy / regime propagation;
- production Risk / Execution sequence;
- Strategy Version identity;
- production isolation.

Частично подтверждены:

- полная runtime propagation `ai_experiment_id`;
- полная runtime propagation `ai_decision_id`;
- end-to-end AI Live trade traceability.

Причина ограниченного статуса — AI Live execution в текущем состоянии отключён.

**Remaining:** отдельный runtime audit metadata propagation через paper/shadow/и будущий controlled live path.
# 33. Разделение источников торговли

**Status:** `TEST VERIFIED`

## 33.1. Каноническое требование

Каждая Position и каждая запись TradeHistory должны иметь однозначный `trade_source`.

Канонические источники:

- `STRATEGY_ENGINE`;
- `GRID`;
- `AI_SANDBOX`;
- `AI_PAPER`;
- `AI_SHADOW`;
- `AI_LIVE`;
- `MANUAL`.

Исторические `LEGACY` записи не должны смешиваться с валидной production statistics.

`BASELINE` является comparison participant, а не trade_source.

## 33.2. Position source field

`models/position.py` содержит:

`trade_source`

и связанные AI metadata fields.

**Status:** `VERIFIED`

**Evidence:** `models/position.py`

## 33.3. TradeHistory source field

`models/trade_history.py` содержит:

`trade_source`

и связанные AI metadata fields.

**Status:** `VERIFIED`

**Evidence:** `models/trade_history.py`

## 33.4. Production source

Production ExecutionAgent передаёт source:

`STRATEGY_ENGINE`

в ExecutionBoundary.

**Status:** `VERIFIED`

**Evidence:**
- `agents/execution_agent.py`;
- `services/execution_boundary.py`.

## 33.5. Grid separation

Grid является отдельным торговым контуром.

Grid не должен рассматриваться как обычная Strategy Engine strategy.

**Status:** `VERIFIED` на уровне архитектурного разделения.

## 33.6. AI Paper separation

AI Paper должен существовать отдельно от real production trades.

Paper trade инфраструктура реализована отдельной моделью:

`models/ai_paper_trade.py`

**Status:** `VERIFIED`

## 33.7. AI Shadow separation

AI Shadow decisions не являются реальными Trade records.

Используется отдельная shadow infrastructure.

**Status:** `TEST VERIFIED`

**Evidence:**
- `models/ai_shadow_decision.py`;
- BLOCK F comparison identity;
- shadow outcome infrastructure.

## 33.8. AI Live separation

`AI_LIVE` предусмотрен канонической архитектурой как отдельный source.

При этом Restricted Live и Full Live в текущем состоянии отключены.

**Status:** `VERIFIED` для архитектурного source definition; `NOT VERIFIED` для фактических live records.

## 33.9. Comparison source isolation

Comparison Engine имеет отдельный source isolation layer:

`services/ai_comparison_trade_source.py`

Comparison participants не должны автоматически становиться Trade records.

**Status:** `TEST VERIFIED`

**Evidence:** BLOCK F / F.6 + F-REVIEW-5.

## 33.10. Production performance isolation

Production performance не должна включать:

- AI Paper;
- AI Shadow;
- AI Live;
- Grid;
- Legacy;
- test data.

**Status:** `TEST VERIFIED`

**Evidence:**
- B1 source/data quality;
- BLOCK F trade_source separation;
- comparison source isolation.

## 33.11. Legacy handling

Legacy trades должны быть исключены или отдельно маркированы при research analysis.

Knowledge/Data Quality infrastructure содержит соответствующие source/data guards.

**Status:** `VERIFIED` для research filtering.

## 33.12. Trade source integrity

Обнаружен отдельный сервис:

`services/ai_trade_source_integrity.py`

Он предназначен для контроля source identity и недопущения некорректного mixing.

**Status:** `VERIFIED`

## 33.13. Source propagation

Source должен сохраняться через:

`Execution → Position → TradeHistory`

Schema поддерживает эту трассируемость.

**Status:** `PARTIALLY VERIFIED`

Полный runtime proof всех AI source variants требует фактических executions соответствующих типов, а `AI_LIVE` currently disabled.

## 33.14. Statistical isolation

Все research/validation/comparison calculations должны явно задавать допустимый source scope.

Implicit cross-source aggregation запрещён.

**Status:** `TEST VERIFIED`

**Evidence:**
- B1 data quality/source filtering;
- F.6 trade_source separation.

## 33.15. Итог

Подтверждены:

- trade_source в Position;
- trade_source в TradeHistory;
- production source;
- Grid separation;
- AI Paper separation;
- AI Shadow separation;
- comparison source isolation;
- Legacy filtering;
- trade-source integrity service;
- production statistics isolation.

Частично подтверждено:

- полный runtime propagation каждого source через весь production lifecycle;
- AI Live source, поскольку live AI execution отключён.

**Remaining:** периодический source-integrity audit и runtime proof новых source variants при их фактическом появлении.
# 34. API

**Status:** `PARTIALLY VERIFIED`

## 34.1. Каноническое требование

AIEA должен предоставлять контролируемый API как минимум для:

- AI status;
- strategies;
- experiments;
- strategy versions;
- performance;
- shadow;
- hypotheses;
- memory;
- lessons;
- audit;
- news;
- events;
- comparison.

Mutation endpoints должны быть отделены от read-only endpoints и требовать соответствующий permission level.

API не должен предоставлять AIEA прямой доступ к:

- ExecutionAgent;
- RiskAgent;
- BingX exchange execution.

## 34.2. Фактически существующая API infrastructure

В проекте существует FastAPI application и набор routers:

- `routers/agents.py`;
- `routers/dashboard.py`;
- `routers/history.py`;
- `routers/markets.py`;
- `routers/portfolio.py`;
- `routers/signals.py`;
- `routers/trading.py`;
- другие production routers.

Основной application entry:

`app_fastapi.py`

**Status:** `VERIFIED`

## 34.3. AIEA-specific endpoints

Канонический план предусматривает:

`GET /api/ai/status`
`GET /api/ai/strategies`
`GET /api/ai/experiments`
`GET /api/ai/experiments/{id}`
`GET /api/ai/strategy-versions`
`GET /api/ai/performance`
`GET /api/ai/shadow`

и mutation endpoints для:

- experiment creation;
- validation;
- promotion;
- rollback;
- kill-switch.

В проведённом audit полный набор этих endpoints как единого AIEA API не подтверждён.

**Status:** `NOT VERIFIED`

## 34.4. Read-only AI API

Должны существовать read-only operations для:

- hypotheses;
- memory;
- lessons;
- audit;
- News/Event;
- comparison.

Отдельный полный AIEA read API surface пока не подтверждён.

**Status:** `NOT VERIFIED`

## 34.5. Promotion API

Promotion endpoint должен требовать отдельный permission level.

Promotion Manager уже существует как internal controlled mutation boundary.

**Status:** `TEST VERIFIED` для internal promotion control; `NOT VERIFIED` для полного public HTTP API surface.

**Evidence:**
- E1;
- E6;
- E10;
- E12.

## 34.6. Rollback API

Rollback должен быть controlled operation и не должен быть доступен без соответствующей identity / state validation.

Internal rollback service существует:

`services/ai_promotion_rollback.py`

**Status:** `TEST VERIFIED` для service boundary; HTTP endpoint отдельно не подтверждён.

**Evidence:** E8/E9.

## 34.7. Kill-switch API

Канонический API предусматривает:

`POST /api/ai/kill-switch`

Должен использовать более высокий permission level.

Dedicated AIEA kill-switch API пока не подтверждён.

**Status:** `NOT VERIFIED`

## 34.8. API authorization

Production API имеет authentication / authorization infrastructure.

Однако отдельная exhaustive authorization matrix именно для AIEA endpoints не доказана.

**Status:** `PARTIALLY VERIFIED`

## 34.9. Direct execution exposure

API не должен позволять AIEA вызывать:

- ExecutionAgent напрямую;
- RiskAgent напрямую;
- BingX напрямую.

Production architecture использует ExecutionBoundary.

**Status:** `VERIFIED` для production execution architecture.

**Evidence:**
- ExecutionBoundary;
- E10/E12 production isolation.

## 34.10. User isolation at API layer

AIEA API должен сохранять user ownership при работе с:

- hypotheses;
- experiments;
- versions;
- evidence;
- memory;
- audit;
- comparison.

A8/E11 подтверждают underlying identity isolation, но полный HTTP-layer isolation audit не выполнен.

**Status:** `PARTIALLY VERIFIED`

## 34.11. API mutation safety

Mutation endpoints не должны позволять:

- direct strategy overwrite;
- permission escalation;
- promotion bypass;
- rollback bypass;
- risk approval bypass;
- execution bypass.

Internal promotion controls уже защищены.

**Status:** `TEST VERIFIED` для internal mutation boundaries.

**Evidence:**
- E1–E12.

## 34.12. API observability / audit

AI mutations должны оставлять audit trail.

Promotion/rollback audit уже реализованы.

Полный audit всех AIEA HTTP mutations пока не доказан.

**Status:** `PARTIALLY VERIFIED`

## 34.13. Итог

Подтверждены:

- FastAPI production infrastructure;
- controlled internal promotion/rollback boundaries;
- production execution isolation;
- underlying identity isolation;
- internal mutation safety.

Не подтверждены полностью:

- полный AIEA REST API;
- read-only AI endpoints;
- promotion HTTP API;
- rollback HTTP API;
- dedicated kill-switch HTTP API;
- exhaustive API authorization matrix;
- HTTP-layer user isolation;
- complete API mutation audit coverage.

**Remaining:** отдельный factual audit и implementation mapping AIEA API surface.
# 35. Dashboard

**Status:** `PARTIALLY VERIFIED`

## 35.1. Каноническое требование

Dashboard должен иметь отдельный раздел:

`AI EVOLUTION`

Он должен показывать отдельно experimental и production результаты.

Обязательные категории:

- current AI level;
- active AI model;
- current experiments;
- AI-created strategies;
- AI-modified strategies;
- best AI strategy;
- worst AI strategy;
- paper PnL;
- shadow PnL;
- live PnL;
- AI vs Production;
- promotions;
- rollbacks;
- failed experiments;
- hypotheses;
- learning history;
- News & Event Intelligence;
- high-impact events;
- news impact on strategies;
- AI performance by market regime;
- AI performance by symbol;
- AI performance by LONG/SHORT.

Нельзя объединять Paper / Shadow / Restricted Live / Full Live PnL без явного указания source.

## 35.2. Фактически существующая Dashboard infrastructure

В проекте обнаружены:

- `routers/dashboard.py`;
- `templates/dashboard.html`;
- `static/js/dashboard.js`;
- dashboard-related API functionality.

Основное приложение использует FastAPI и отдельный dashboard router.

**Status:** `VERIFIED`

**Evidence:**
- `routers/dashboard.py`;
- `templates/dashboard.html`;
- `static/js/dashboard.js`.

## 35.3. Existing production dashboard

Production dashboard уже содержит торговые/portfolio views NEXUS.

Это не является автоматически доказательством полноценного AI Evolution Dashboard.

**Status:** `VERIFIED` для существующего production UI.

## 35.4. AI Evolution section

Отдельный полноценный Dashboard section `AI EVOLUTION` со всеми каноническими AI metrics в проведённом audit не подтверждён.

**Status:** `NOT VERIFIED`

## 35.5. Experiment visibility

AI experiments должны отображаться с:

- experiment identity;
- strategy version;
- status;
- validation stage;
- result;
- timestamp.

Backend experiment infrastructure существует, но полный UI mapping не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 35.6. Strategy Version visibility

Dashboard должен показывать:

- strategy;
- version;
- parent;
- promotion level;
- status;
- validation state.

Strategy Version backend infrastructure существует.

Полный dashboard presentation не доказан.

**Status:** `PARTIALLY VERIFIED`

## 35.7. Performance separation

Dashboard должен явно разделять:

- production;
- AI Paper;
- AI Shadow;
- AI Restricted Live;
- AI Full Live;
- Grid.

Существующие comparison/source infrastructure поддерживают source separation на backend level.

Полное UI enforcement не проверено.

**Status:** `PARTIALLY VERIFIED`

## 35.8. AI vs Production

Comparison Engine предоставляет backend data для AI vs production comparison.

Полный dashboard visualization этого comparison не подтверждён.

**Status:** `PARTIALLY VERIFIED`

**Evidence:** BLOCK F comparison infrastructure.

## 35.9. Promotion / Rollback visualization

Promotion и rollback backend audit infrastructure существует.

UI отображение:

- promotion history;
- rollback history;
- current stage;
- permission level;
- risk approval

отдельно не подтверждено.

**Status:** `PARTIALLY VERIFIED`

## 35.10. Hypothesis / Learning history

Hypothesis and Memory infrastructure существует:

- Hypothesis;
- Lessons;
- Experiments.

Полный dashboard workflow для:

`Observation → Hypothesis → Experiment → Lesson`

не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 35.11. News/Event dashboard

Канонически Dashboard должен показывать:

- current high-impact events;
- event context;
- affected symbols;
- event direction / impact;
- strategy behaviour around events.

News/Event backend foundation существует, но полноценный dashboard visualization не подтверждён.

**Status:** `NOT VERIFIED`

## 35.12. Market regime analytics

Dashboard должен показывать AI performance по:

- market regime;
- symbol;
- LONG/SHORT.

Comparison and research infrastructure уже содержит соответствующие dimensions.

Полное UI представление не доказано.

**Status:** `PARTIALLY VERIFIED`

## 35.13. Trust / promotion state

Dashboard должен отображать AI trust level и promotion state без возможности UI обойти permission boundaries.

Backend permission layer существует.

Полный UI security audit отсутствует.

**Status:** `PARTIALLY VERIFIED`

## 35.14. Dashboard data isolation

Multi-user AI data должна быть изолирована.

Underlying A8/E11 identity controls существуют, но HTTP/dashboard-layer user isolation отдельно не проверена полностью.

**Status:** `PARTIALLY VERIFIED`

## 35.15. Dashboard mutation safety

Dashboard не должен позволять обходить:

- promotion gates;
- risk approval;
- permission policy;
- rollback integrity;
- kill switch;
- production execution boundary.

Internal backend controls уже существуют.

Полный UI negative-path audit не проведён.

**Status:** `PARTIALLY VERIFIED`

## 35.16. Итог

Подтверждены:

- существующий production Dashboard;
- FastAPI dashboard router;
- dashboard template / JS;
- backend comparison data;
- backend promotion / rollback infrastructure;
- AI research data sources.

Не подтверждены полностью:

- отдельный полноценный `AI EVOLUTION` UI;
- полный experiment/strategy/version views;
- source-separated PnL visualization;
- complete AI vs Production visualization;
- promotion/rollback UI;
- learning/hypothesis history UI;
- News/Event dashboard;
- полный regime/symbol/side AI analytics UI;
- dashboard-layer user isolation;
- UI mutation security audit.

**Remaining:** отдельный полный Dashboard audit/rework, включая API contracts, UI data isolation и security.
# 36. Критерии повышения стратегии

**Status:** `PARTIALLY VERIFIED`

## 36.1. Каноническое требование

Каждый переход между стадиями Promotion Pipeline должен иметь формальные критерии.

Минимальная последовательность:

`Paper → Shadow → Advisory → Restricted Live → Live`

Критерии должны учитывать не только PnL, но также:

- statistical significance;
- stability;
- sample size;
- symbol coverage;
- regime coverage;
- LONG/SHORT stability;
- degradation;
- catastrophic risk;
- News/Event behaviour.

Пороги должны быть конфигурационными и недоступными для самостоятельного изменения AIEA.

## 36.2. Paper → Shadow

Канонический пример требует:

- minimum trades >= 100;
- profit factor >= 1.20;
- expectancy > 0;
- max drawdown <= predefined limit;
- positive OOS;
- no catastrophic risk behaviour.

**Status:** `PARTIALLY VERIFIED`

Formal promotion gate существует, однако полный отдельный audit всех перечисленных quantitative thresholds именно для этого перехода не выполнен.

## 36.3. Shadow → Advisory

Требуется:

- minimum shadow trades >= 200;
- stability across at least 2 regimes;
- no significant degradation.

**Status:** `PARTIALLY VERIFIED`

Shadow quality/stability infrastructure существует, но полный formal gate по всем перечисленным условиям отдельно не доказан.

## 36.4. Advisory → Restricted Live

Требуется:

- statistically significant edge;
- positive shadow expectancy;
- risk approval;
- sufficient AI trust level;
- no critical News/Event risk violation.

**Status:** `PARTIALLY VERIFIED`

Promotion/risk/permission infrastructure существует.

Restricted Live operational stage пока disabled.

## 36.5. Restricted Live → Live

Требуется:

- minimum live sample;
- drawdown within limit;
- stable performance;
- no anomaly.

**Status:** `NOT VERIFIED`

Restricted Live и Full Live отключены, поэтому runtime evidence данного перехода отсутствует.

## 36.6. Promotion Gate enforcement

Formal gates уже реализованы через:

`services/ai_promotion_gates.py`

Gate проверяет validation evidence и stage-specific result requirements.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E3_BACKTEST_PASS_OK`
- `E3_OOS_PASS_OK`
- `E3_OOS_INSUFFICIENT_DATA_BLOCKED_OK`
- `E3_MISSING_RESULT_BLOCKED_OK`
- `E3_SHADOW_MISSING_BLOCKED_OK`
- `E3_SHADOW_PASS_OK`

## 36.7. Risk Approval

Promotion не должен происходить без обязательного risk approval.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E5_NOT_EVALUATED_BLOCKED_OK`
- `E5_REJECT_BLOCKED_OK`
- `E5_MANAGER_RISK_BLOCK_OK`
- `E5_MANAGER_RISK_APPROVAL_PASS_OK`

## 36.8. Permission enforcement

Promotion stage должен соответствовать promotion level и permissions.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E6_ALL_STAGE_LEVELS_VALID_OK`
- `E6_STAGE_LEVEL_MISMATCH_BLOCKED_OK`
- `E6_UNKNOWN_STAGE_BLOCKED_OK`
- `E6_PERMISSION_ESCALATION_BLOCKED_OK`
- `E6_INVALID_STATE_NO_PERMISSION_OK`

## 36.9. Evidence binding

Promotion criteria должны использовать exact validation evidence для соответствующих:

- user;
- experiment;
- strategy version;
- hypothesis;
- strategy definition.

**Status:** `TEST VERIFIED`

**Evidence:** E4 exact evidence binding.

## 36.10. Risk limits / Promotion criteria immutability

AIEA не должен самостоятельно изменять:

- promotion thresholds;
- risk limits;
- required evidence;
- permission mapping.

Promotion/risk infrastructure отделена от AI research layer.

**Status:** `TEST VERIFIED` для permission/safety boundaries.

**Evidence:**
- E5;
- E6;
- E10;
- E12.

## 36.11. News/Event criteria

Promotion criteria должны учитывать News/Event behaviour там, где это релевантно.

Полный News/Event-aware promotion gate пока не подтверждён.

**Status:** `NOT VERIFIED`

## 36.12. Automated quantitative gate coverage

Формальные gates существуют, однако отдельная exhaustive matrix, связывающая каждый promotion transition со всеми каноническими quantitative criteria, ещё не проведена.

**Status:** `PARTIALLY VERIFIED`

## 36.13. Current safety state

Promotion infrastructure не включает unrestricted AI live trading.

Текущие состояния:

- Restricted Live = DISABLED;
- Full Live = DISABLED.

**Status:** `VERIFIED`

## 36.14. Итог

Подтверждены:

- formal promotion gate infrastructure;
- evidence binding;
- mandatory risk approval;
- permission enforcement;
- stage/level consistency;
- blocked insufficient-data cases;
- protection against AI self-modification of permissions/limits.

Частично подтверждены:

- complete quantitative criteria for Paper → Shadow;
- Shadow → Advisory;
- Advisory → Restricted Live;
- unified gate matrix.

Не подтверждены:

- Restricted Live → Live runtime criteria;
- complete News/Event-aware promotion criteria.

**Remaining:** exhaustive audit promotion threshold matrix and future live-stage gates.
# 37. Генерация стратегии

**Status:** `PARTIALLY VERIFIED`

## 37.1. Каноническое требование

AIEA должен получать структурированный research context для генерации новой стратегии:

- market_state;
- market_regime;
- historical performance;
- strategy registry;
- failed experiments;
- successful experiments;
- risk constraints;
- available indicators;
- News/Event context;
- historical event behaviour.

AIEA не должен получать произвольный доступ к production filesystem или production execution.

## 37.2. Generation environment

Генерация должна происходить в research / sandbox environment.

Generated strategy не получает production permission автоматически.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- Strategy Version infrastructure;
- static validation;
- E3/E6/E10/E12 promotion boundaries.

## 37.3. Unique strategy identity

Каждая generated strategy должна сразу получать:

- unique strategy ID;
- version;
- hypothesis ID;
- Strategy Genome;
- validation state;
- experiment ID.

Strategy Version и experiment identity infrastructure существуют.

**Status:** `TEST VERIFIED` для identity/linkage components.

**Evidence:**
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- `models/ai_strategy_version.py`

## 37.4. Generation context isolation

Generation context должен быть сформирован из разрешённых research inputs.

Direct access к:

- production filesystem;
- exchange credentials;
- execution interfaces;
- unrestricted production database

не допускается.

**Status:** `PARTIALLY VERIFIED`

Static validation и production safety boundaries существуют, но отдельный complete generation-context access audit не выполнен.

## 37.5. Strategy Genome generation

Generated strategy должна иметь machine-readable Genome.

Static validation поддерживает Strategy Definition / Genome schema.

Полная автоматическая генерация Genome самим AI не доказана.

**Status:** `PARTIALLY VERIFIED`

## 37.6. Hypothesis linkage

Генерация должна быть мотивирована конкретной hypothesis.

Фактическая chain infrastructure:

`Knowledge Snapshot → Hypothesis → Experiment → StrategyVersion`

**Status:** `TEST VERIFIED`

**Evidence:**
- `A9_SNAPSHOT_OK`
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- B2 hypothesis validation evidence.

## 37.7. Experiment linkage

Generated strategy должна быть частью reproducible experiment.

Experiment model и engine существуют.

**Status:** `TEST VERIFIED`

**Evidence:** A9 experiment/version binding.

## 37.8. Static validation before execution

Generated strategy должна пройти static validation до downstream execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK D / D.1;
- forbidden-operation guard;
- Genome/definition validation.

## 37.9. Sandbox execution

Generated implementation должна выполняться только в изолированном sandbox.

На текущем factual audit production-grade runtime sandbox не доказан.

**Status:** `NOT VERIFIED`

## 37.10. Validation lifecycle

Generated strategy должна пройти:

`Static → Backtest → OOS → Walk-Forward → Paper → Shadow → Evaluation → Promotion`

Validation infrastructure существует, но automatic orchestration from generator through all stages не подтверждена.

**Status:** `PARTIALLY VERIFIED`

## 37.11. Audit trail

Generation context должен фиксироваться вместе с:

- AI agent;
- model;
- model_version;
- prompt_version;
- input snapshot;
- hypothesis;
- experiment;
- strategy version.

AI audit model и promotion audit существуют, но полный population audit для generation actions отсутствует.

**Status:** `PARTIALLY VERIFIED`

## 37.12. Production permission boundary

Generated strategy не должна автоматически становиться production-ready.

Promotion требуется пройти через:

- validation evidence;
- formal gate;
- risk approval;
- permission;
- production safety.

**Status:** `TEST VERIFIED`

**Evidence:**
- E3;
- E4;
- E5;
- E6;
- E10;
- E12.

## 37.13. Autonomous generator

Не подтверждены:

- полноценный autonomous Strategy Generator service;
- automatic context assembly;
- automatic Genome generation;
- automatic implementation generation;
- automatic test creation;
- automatic experiment creation;
- automatic validation launch;
- automatic evaluation;
- automatic promotion request.

**Status:** `NOT VERIFIED`

## 37.14. Итог

Подтверждены:

- strategy identity infrastructure;
- hypothesis linkage;
- experiment linkage;
- static validation;
- downstream validation infrastructure;
- production permission boundary.

Частично подтверждены:

- generation environment;
- generation context isolation;
- Genome integration;
- validation orchestration;
- generation audit coverage.

Не подтверждён:

- полноценный autonomous Strategy Generator.

**Remaining:** factual audit autonomous generation engine и его end-to-end lifecycle.
# 38. Изменение существующих стратегий

**Status:** `PARTIALLY VERIFIED`

## 38.1. Каноническое требование

AIEA должен иметь возможность предлагать изменения существующих стратегий только через создание новой версии.

Существующая версия не должна переписываться.

Каждое изменение должно проходить тот же controlled lifecycle, что и новая стратегия:

`Hypothesis → New Version → Experiment → Validation → Evaluation → Promotion`

## 38.2. Допустимые типы изменений

Канонически предусмотрены:

- parameter change;
- rule addition;
- rule removal;
- entry modification;
- exit modification;
- filter modification;
- regime restriction;
- volatility restriction;
- volume filter;
- confidence threshold;
- risk/reward model;
- SL model;
- TP model;
- News/Event filter;
- News/Event risk restriction.

Полный implementation всех операторов отдельно не подтверждён.

**Status:** `NOT VERIFIED`

## 38.3. Parent version requirement

Новая изменённая версия должна быть связана с исходной:

`parent_strategy`
`parent_version`

Genealogy infrastructure поддерживает parent linkage.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E9_VALID_GENEALOGY_FIXTURE_OK`
- `E9_PARENT_REQUIRED_BLOCKED_OK`
- `E9_PARENT_PRESERVED_OK`

## 38.4. Required change metadata

Для каждого изменения должны сохраняться:

- parent strategy;
- parent version;
- new version;
- hypothesis_id;
- experiment_id;
- expected_effect;
- actual_effect;
- validation_history.

Strategy Version / Experiment / Hypothesis infrastructure существует.

Полная persistence именно change-level metadata отдельно не подтверждена.

**Status:** `PARTIALLY VERIFIED`

## 38.5. Before / After Strategy Definition

Должны сохраняться:

`Genome_before`
`Genome_after`

чтобы было возможно определить точное изменение.

Отдельный полноценный before/after Genome persistence не доказан.

**Status:** `NOT VERIFIED`

## 38.6. Immutable parent

Исходная version должна оставаться неизменной после modification.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E8_PARENT_VERSION_PRESERVED_OK`
- `E9_PARENT_PRESERVED_OK`

## 38.7. Modification → Experiment

Каждая modification должна быть проверена отдельным experiment.

**Status:** `TEST VERIFIED` для identity infrastructure, но automatic modification-to-experiment orchestration не доказана.

**Evidence:**
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`

## 38.8. Modification → Validation

Изменённая version должна пройти validation заново.

Validation infrastructure существует:

- Static;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow.

**Status:** `TEST VERIFIED` для validation boundary.

**Evidence:** BLOCK D + E2/E3.

## 38.9. Parent versus child comparison

Необходимо сравнивать новую version с parent по:

- PnL;
- win rate;
- PF;
- expectancy;
- drawdown;
- stability;
- regime;
- symbol;
- side;
- source.

Comparison infrastructure существует.

Полный автоматический parent-vs-child evaluation lifecycle отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 38.10. Promotion protection

Modified strategy не должна получать production permissions автоматически.

**Status:** `TEST VERIFIED`

**Evidence:**
- E3;
- E4;
- E5;
- E6;
- E10;
- E12.

## 38.11. News/Event modifications

Допустимы:

- News/Event filter;
- News/Event risk restriction.

Полный автоматический event-aware modification cycle не подтверждён.

**Status:** `NOT VERIFIED`

## 38.12. Autonomous modification engine

Не подтверждены:

- automatic parent selection;
- automatic modification operator selection;
- automatic Genome mutation;
- automatic before/after persistence;
- automatic experiment creation;
- automatic validation;
- automatic parent/child ranking;
- automatic promotion request.

**Status:** `NOT VERIFIED`

## 38.13. Итог

Подтверждены:

- immutable Strategy Version;
- parent genealogy;
- hypothesis/experiment identity;
- validation infrastructure;
- production promotion boundary.

Частично подтверждены:

- change metadata;
- parent-vs-child comparison.

Не подтверждены:

- полный набор modification operators;
- before/after Genome persistence;
- autonomous modification engine;
- automatic retest/evaluation;
- News/Event modification lifecycle.

**Remaining:** factual audit полного automated Strategy Modification pipeline.
# 39. Главный принцип

**Status:** `VERIFIED`

## 39.1. Каноническая модель

AIEA не должен работать по модели:

`AI → придумал → сразу торгует`

Каноническая модель:

`AI → гипотеза → эксперимент → доказательство → версия → наблюдение → ограниченное применение → подтверждение → расширение полномочий`

## 39.2. Separation of concerns

NEXUS должен разделять:

- Strategy Decision Engine;
- Grid Engine;
- AI Evolution Agent;
- Risk Engine;
- Execution;
- Exchange.

AIEA не должен заменять Strategy Decision Engine или Grid Engine.

**Status:** `VERIFIED`

**Evidence:**
- production signal flow;
- Grid separate contour;
- AIEA research/promotion services.

## 39.3. Human-controlled boundaries

Человек сохраняет контроль над:

- risk boundaries;
- promotion levels;
- validation criteria;
- rollback criteria;
- kill switch;
- production security;
- permitted data sources.

AI не должен самостоятельно расширять собственные полномочия.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5 risk approval;
- E6 permission controls;
- E10 production safety;
- E12 integration;
- A8/E11 identity isolation.

## 39.4. Controlled promotion

AI strategy должна пройти последовательную validation / promotion pipeline.

Пропуск стадий запрещён.

**Status:** `TEST VERIFIED`

**Evidence:**
- E2 state machine;
- E3 formal gates;
- E4 evidence binding;
- E5 risk approval;
- E6 permissions;
- E12 integration.

## 39.5. Production execution boundary

AI не должен напрямую выполнять exchange orders.

Production execution проходит контролируемую цепочку:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary → BaseExchangeClient`

**Status:** `VERIFIED`

## 39.6. Research-first operation

Knowledge, Hypothesis, Experiment, Validation, Memory и Comparison должны оставаться research/controlled layers до прохождения promotion requirements.

**Status:** `VERIFIED / TEST VERIFIED`

**Evidence:**
- B1/B2/B3/B4;
- D6_8;
- E10/E12;
- F.1–F.9.

## 39.7. Version immutability

Strategy evolution должна происходить через новые versions.

Existing versions не переписываются.

**Status:** `TEST VERIFIED`

**Evidence:**
- E8 parent preservation;
- E9 genealogy integrity.

## 39.8. Auditability

Ключевые действия должны быть восстанавливаемыми через:

`context → observation → hypothesis → strategy version → experiment → validation → promotion → result`

Promotion and rollback audit уже обеспечивают значительную часть этой traceability.

**Status:** `PARTIALLY VERIFIED`

## 39.9. News/Event constraint

News/Event Intelligence должна быть дополнительным market-context source, а не механизмом обхода risk/promotion controls.

**Status:** `VERIFIED` для архитектурного constraint; full News/Event implementation остаётся незавершённой.

## 39.10. Итог

Архитектурный принцип фактически соблюдается в текущей реализации:

- research-first;
- versioned evolution;
- controlled validation;
- promotion gates;
- risk approval;
- permission boundaries;
- production execution isolation;
- immutable genealogy.

**Final status:** `VERIFIED`

**Remaining:** расширение AIEA capability не должно нарушать этот принцип; новые компоненты должны проходить тот же FACT → CHECK → EVIDENCE → AUDIT цикл.
# 40. Этапы реализации

**Status:** `PARTIALLY VERIFIED`

## 40.1. Этап A — Foundation

Канонически включает:

- AI Agent module;
- DB schema;
- Strategy Versioning;
- Experiment model;
- Knowledge Engine;
- trade_source;
- audit logging;
- News/Event foundation;
- event storage / market context integration;
- identity / isolation.

Фактически подтверждены отдельные foundation components, включая A8.

**Status:** `IN PROGRESS`

**Evidence:**
- A8 foundation isolation;
- A9 foundation chain;
- B4 memory;
- AI database models/migrations.

## 40.2. Этап B — Research

Канонически включает:

- historical analysis;
- hypothesis generation;
- strategy evaluation;
- AI Memory;
- News/Event correlation;
- regime/event-dependent research.

Фактически подтверждены:

- B1 Data Quality / Historical Analysis;
- B2 Hypothesis Research;
- B3 Strategy Evaluation;
- B4 AI Memory.

B.5 News/Event Correlation остаётся active.

**Status:** `IN PROGRESS`

**Evidence:**
- B1;
- B2;
- B3;
- B4;
- current B.5 track.

## 40.3. Этап C — Strategy Generation

Канонически включает:

- new strategy generation;
- existing strategy modification;
- versioning;
- Strategy Genome;
- sandbox execution;
- static security validation.

Фактически существуют Strategy Version / Genome validation components, но autonomous generation и modification engines полностью не подтверждены.

**Status:** `PARTIALLY VERIFIED`

## 40.4. Этап D — Validation

Включает:

- Static Validation;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow;
- metrics;
- evidence;
- production isolation.

Фактически завершён:

`D.1–D.6.8`

Final evidence:

`D6_8_BLOCK_D_FULL_COMPILE_OK`

**Status:** `DONE + TEST VERIFIED`

## 40.5. Этап E — Paper Trading

Paper infrastructure существует и validation pipeline использует paper stage.

**Status:** `TEST VERIFIED` как validation capability.

Полный самостоятельный long-running production-like Paper operating lifecycle отдельно не подтверждён.

## 40.6. Этап F — Shadow Trading

Shadow infrastructure существует:

- shadow decisions;
- outcome accumulation;
- quality;
- stability;
- advisory;
- comparison.

Current safety:

`Strategy Decision Engine = SHADOW-ONLY`

**Status:** `TEST VERIFIED / IN PROGRESS`

Shadow data accumulation продолжается.

## 40.7. Этап G — Advisory

Advisory infrastructure существует, однако текущая policy:

`OBSERVE_ONLY`

Advisory:

- cannot change signal;
- cannot change strategy;
- cannot change confidence;
- cannot block execution;
- cannot trigger execution.

**Status:** `PARTIALLY VERIFIED / DISABLED FOR CONTROL`

**Evidence:**
- `services/ai_shadow_advisory_influence_policy.py`;
- current production safety state.

## 40.8. Этап H — Restricted Live

Restricted Live operational contour не разрешён.

Required controls:

- AI risk budget;
- strict position limits;
- daily loss limit;
- symbol whitelist;
- leverage limit;
- mandatory SL/TP;
- RiskAgent;
- protection validation;
- AI kill switch.

**Status:** `DISABLED / NOT VERIFIED`

## 40.9. Этап I — Full Live

Full Live требует доказанной статистической устойчивости и завершения предыдущих controlled stages.

Текущий state:

`Full Live = DISABLED`

**Status:** `DISABLED / NOT STARTED`

## 40.10. Stage dependencies

Stages должны выполняться последовательно.

Promotion State Machine и Formal Gates запрещают произвольный переход через stages.

**Status:** `TEST VERIFIED`

**Evidence:**
- E2;
- E3;
- E4;
- E5;
- E6.

## 40.11. Production safety across stages

Ни один этап сам по себе не должен автоматически получать production execution authority.

Production boundary сохраняется через:

- RiskAgent;
- ExecutionAgent;
- ExecutionBoundary;
- AIProductionSafetyService;
- Promotion permissions.

**Status:** `TEST VERIFIED`

**Evidence:** E10/E12.

## 40.12. Current overall stage position

Фактическое состояние проекта:

- Foundation — active;
- Research — active;
- Strategy Evolution — partially implemented;
- Validation — completed;
- Paper — implemented as validation capability;
- Shadow — active;
- Advisory — observe-only;
- Restricted Live — disabled;
- Full Live — disabled.

**Status:** `VERIFIED` как текущая consolidated state.

## 40.13. Итог

Полностью закрыт:

- Этап D / Validation.

Активны:

- A / Foundation;
- B / Research;
- F / Shadow.

Частично реализован:

- C / Strategy Generation.

Контролируемо отключены:

- G / Advisory operational influence;
- H / Restricted Live;
- I / Full Live.

**Remaining:** завершение Foundation/Research/Strategy Evolution и только после доказанного prerequisite — controlled progression к следующим operational stages.
# 41. Критерий готовности первой версии AIEA

**Status:** `PARTIALLY VERIFIED`

## 41.1. Канонический критерий

Первая production-ready версия AIEA считается завершённой только если выполнены все обязательные условия:

1. AI анализирует исторические сделки NEXUS.
2. AI формирует проверяемые гипотезы.
3. AI создаёт новые версии стратегий.
4. Новая стратегия запускается только в sandbox/research environment.
5. Существует автоматический Backtest.
6. Существует OOS Validation.
7. Существует Walk-Forward Validation.
8. Существует Paper Trading.
9. Существует Shadow Trading.
10. Результаты сохраняются в БД.
11. Strategy Versions immutable.
12. Существует Promotion / Rollback.
13. AIEA не имеет прямого доступа к ExecutionAgent.
14. AIEA не имеет прямого доступа к BingX.
15. Существует отдельный AI risk budget.
16. Существует AI kill switch.
17. Существует полный audit trail.
18. Существует AI vs Strategy Engine comparison.
19. Production trades однозначно маркируются trade_source.
20. AI может самостоятельно сформировать и проверить новую hypothesis.
21. AI не может самостоятельно повысить собственный access level.
22. Только доказанная стратегия может перейти на следующий promotion level.
23. News & Event Intelligence интегрирован в market context.
24. Исторический News/Event context используется в research/validation при наличии данных.
25. Существуют отдельные News/Event influence metrics.
26. News/Event Risk controls не могут быть отключены AIEA.
27. Experimental trade sources отделены от production.
28. Strategy genealogy восстанавливаема.
29. Для каждого AI decision сохраняется AI model version.
30. Promotion criteria и risk limits недоступны для самостоятельного изменения AIEA.

## 41.2. Исторический анализ

B1 подтверждает research infrastructure для historical data analysis.

**Status:** `TEST VERIFIED`

**Evidence:** B1 data quality / historical analysis.

## 41.3. Hypothesis generation

B2 подтверждает формирование structured hypotheses и обязательность дальнейшей validation.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B2_REGIME_CONTRAST_OK`
- `B2_HYPOTHESIS_STRUCTURE_OK`
- `B2_VALIDATION_REQUIRED_OK`

## 41.4. Strategy Versioning

Strategy Version infrastructure существует и связана с hypothesis / experiment.

**Status:** `TEST VERIFIED`

**Evidence:**
- A9 strategy-version binding;
- E4/E9/E12.

## 41.5. Validation pipeline

Фактически подтверждены:

- Static Validation;
- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow.

**Status:** `DONE + TEST VERIFIED`

**Evidence:** `D6_8_BLOCK_D_FULL_COMPILE_OK`

## 41.6. Database persistence

AI-related models и migrations существуют для:

- agents;
- hypotheses;
- strategy versions;
- experiments;
- results;
- paper;
- shadow;
- memory;
- audit;
- validation evidence;
- comparison;
- promotion;
- News/Event foundation.

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

Не все required lifecycle states имеют отдельную persistence model.

## 41.7. Immutable versions / genealogy

Strategy versions и genealogy защищены.

**Status:** `TEST VERIFIED`

**Evidence:**
- E8;
- E9;
- parent preservation;
- rollback integrity.

## 41.8. Promotion / Rollback

E.1–E.12 полностью реализованы и интеграционно проверены.

**Status:** `DONE + TEST VERIFIED`

## 41.9. Execution isolation

AIEA не должен иметь прямого execution authority.

Production execution проходит через controlled boundary.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8;
- E10;
- E12;
- ExecutionBoundary.

## 41.10. AI risk budget

Требуется отдельный AI risk budget для Restricted Live.

Dedicated operational AI risk-budget layer не подтверждён.

**Status:** `NOT VERIFIED`

## 41.11. AI kill switch

Dedicated `AI_LIVE_KILL_SWITCH` и полный AI lifecycle flag set не подтверждены.

**Status:** `NOT VERIFIED`

## 41.12. Audit trail

AI audit / promotion / rollback infrastructure существует.

Полное покрытие каждого AI decision model/version/prompt/input snapshot отдельно не завершено.

**Status:** `PARTIALLY VERIFIED`

## 41.13. AI vs Strategy Engine

Comparison Engine F.1–F.9 реализован и reviewed.

**Status:** `DONE + TEST VERIFIED`

## 41.14. trade_source separation

Production and experimental sources разделены.

**Status:** `TEST VERIFIED`

## 41.15. Autonomous hypothesis lifecycle

Hypothesis research pipeline существует.

Полный autonomous loop:

`observe → hypothesize → experiment → validate → learn`

не полностью автоматизирован и не подтверждён end-to-end.

**Status:** `PARTIALLY VERIFIED`

## 41.16. Self-promotion protection

Permission escalation блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E6_PERMISSION_ESCALATION_BLOCKED_OK`
- `E10_AI_PERMISSION_ESCALATION_BLOCKED_OK`

## 41.17. News/Event Intelligence

News/Event foundation существует, но полный ingestion → historical context → research → validation → influence metrics lifecycle не завершён.

**Status:** `PARTIALLY VERIFIED`

## 41.18. Genealogy

Strategy genealogy infrastructure подтверждена E8/E9.

**Status:** `TEST VERIFIED`

## 41.19. AI model version traceability

AI audit model существует, но exhaustive population proof model/version fields для каждого AI action отсутствует.

**Status:** `PARTIALLY VERIFIED`

## 41.20. Promotion criteria / risk limits immutability

Promotion permission и risk approval boundaries защищены.

Полный audit configuration mutation protection отдельно не завершён.

**Status:** `PARTIALLY VERIFIED`

## 41.21. Overall readiness

Первая версия AIEA **не считается полностью production-ready** на текущем этапе.

Причины:

- autonomous Strategy Generation не доказана полностью;
- autonomous Strategy Modification не доказана полностью;
- runtime sandbox не доказан;
- dedicated AI risk budget не доказан;
- dedicated AI kill switch не доказан;
- полный API не доказан;
- полный Dashboard не доказан;
- News/Event Intelligence не завершён;
- Restricted Live / Full Live отключены;
- полный end-to-end autonomous learning cycle не доказан.

**Final Status:** `PARTIALLY VERIFIED`

**Remaining:** закрытие всех обязательных readiness gaps перед любым переходом к operational AI live.
# 42. Итоговая концепция

**Status:** `VERIFIED`

## 42.1. Каноническая архитектурная идея

NEXUS является эволюционирующей торгово-исследовательской платформой, в которой:

- Strategy Decision Engine отвечает за production strategy decisions;
- Grid Engine является отдельным торговым контуром;
- AIEA отвечает за research, discovery, hypothesis, strategy evolution и validation;
- Risk Engine / RiskAgent контролирует риск;
- ExecutionAgent контролирует execution;
- Exchange является внешним execution destination.

## 42.2. AIEA lifecycle

Канонический lifecycle:

`Research → Hypothesis → Strategy Version → Experiment → Validation → Comparison → Controlled Promotion → Production Observation → Learning`

AIEA не получает production authority автоматически.

**Status:** `VERIFIED`

## 42.3. Human control

Человек сохраняет контроль над:

- risk boundaries;
- promotion criteria;
- rollback criteria;
- permission levels;
- kill switch;
- production security.

AIEA не должен самостоятельно расширять собственные полномочия.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5;
- E6;
- E10;
- E12.

## 42.4. Production execution boundary

AI-related research и promotion не заменяют production execution chain.

Подтверждённый production boundary:

`SignalAgent → StrategyDecisionEngine → AIRiskAgent → ExecutionAgent → ExecutionBoundary → BaseExchangeClient`

**Status:** `VERIFIED`

## 42.5. Versioned evolution

Strategy evolution происходит через новые Strategy Versions.

Parent versions сохраняются.

Genealogy должна быть восстанавливаемой.

**Status:** `TEST VERIFIED`

**Evidence:**
- E8;
- E9.

## 42.6. Validation-first principle

Strategy не должна попадать в следующую стадию только из-за высокого PnL предыдущего теста.

Обязательны соответствующие validation evidence и formal promotion gates.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK D;
- E2;
- E3;
- E4.

## 42.7. Research / Production separation

Experimental sources и production sources должны оставаться раздельными.

Comparison Observation не является Trade.

AI Paper / Shadow / Live не должны смешиваться с production statistics.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK F;
- trade_source isolation;
- AIEA validation isolation.

## 42.8. News/Event Intelligence

News/Event Intelligence является самостоятельным market-context контуром.

Он должен быть связан с:

`event → market → regime → strategy → outcome`

и не имеет права обходить risk / execution controls.

Полная реализация News/Event Intelligence остаётся незавершённой.

**Status:** `PARTIALLY VERIFIED`

## 42.9. Dynamic Opportunity Discovery

NEXUS должен поддерживать Dynamic Market Universe / Opportunity Discovery, а не ограничивать research только фиксированным ручным списком symbols.

Этот контур требует отдельного factual audit.

**Status:** `NOT VERIFIED`

## 42.10. Safety model

AIEA должен оставаться:

- fail-closed;
- isolated;
- versioned;
- auditable;
- permission-controlled;
- risk-bounded.

Текущий production safety state сохраняется.

**Status:** `VERIFIED`

## 42.11. Current architectural position

Фактически подтверждено:

- Foundation isolation partially/actively evolving;
- Research infrastructure active;
- Validation complete;
- Promotion infrastructure complete and fail-closed;
- Comparison complete and reviewed;
- Shadow/advisory infrastructure active;
- Restricted Live disabled;
- Full Live disabled.

## 42.12. Итог

Архитектурная концепция NEXUS подтверждается существующей системой и уже реализованными safety/validation/promotion boundaries.

При этом полный AIEA evolutionary lifecycle ещё не считается завершённым, поскольку остаются:

- autonomous generation;
- autonomous modification;
- runtime sandbox;
- dedicated AI risk budget;
- dedicated AI kill switch;
- complete News/Event Intelligence;
- full Dashboard;
- full API;
- Dynamic Opportunity Discovery;
- complete Learning Loop.

**Final status:** `VERIFIED` как архитектурная концепция, `NOT DONE` как полный конечный implementation state.

**Remaining:** аудит и реализация оставшихся архитектурных контуров без нарушения established safety boundaries.
## 43. NEWS & EVENT INTELLIGENCE

**Status:** `PARTIALLY VERIFIED`

## 43.1. Каноническое назначение

News & Event Intelligence является самостоятельным источником market context для NEXUS и AIEA.

Система должна:

- получать и нормализовать news/events;
- определять event type;
- хранить source;
- фиксировать publication time;
- определять affected symbols / market scope;
- определять expected direction;
- определять actual direction;
- оценивать impact;
- определять risk window;
- связывать event с market;
- связывать event с market regime;
- связывать event с strategy;
- связывать event с outcome;
- сохранять исторический event context.

## 43.2. Event model

Фактически существует:

`models/ai_news_event.py`

Также существует:

- `services/ai_news_event_service.py`;
- `services/ai_news_ingestion.py`.

Минимальная event structure архитектурно предусматривает:

- event_id;
- event_type;
- source;
- published_at;
- affected_symbols;
- market_scope;
- expected_direction;
- actual_direction;
- impact_score;
- risk_window_before;
- risk_window_after;
- market_regime;
- related_strategy;
- outcome.

**Status:** `PARTIALLY VERIFIED`

## 43.3. Event normalization

News/Event context имеет normalization layer.

Comparison Engine уже умеет принимать normalized News/Event context.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK F.7;
- `AIComparisonNewsContextService`.

## 43.4. Symbol / scope matching

Event context должен быть связан с конкретными symbols или broader market scope.

Фактический comparison context layer поддерживает symbol/scope matching.

**Status:** `TEST VERIFIED`

**Evidence:** F.7.

## 43.5. News/Event ingestion

Фактически обнаружен:

`services/ai_news_ingestion.py`

Однако полный production-grade ingestion lifecycle с реальными external source adapters не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 43.6. External source adapters

Фактически реализован внешний RSS/Atom provider:

- `services/ai_news_rss_provider.py`;
- `RSSNewsProvider`;
- default feeds для CoinDesk / Cointelegraph;
- RSS 2.0 / Atom parsing;
- deterministic event identity;
- symbol extraction;
- time / symbol / limit filtering;
- failure isolation per feed;
- research-only ingestion без trading side effects.

Отдельно существует periodic ingestion runner:

- `services/ai_news_poller.py`.

Позитивный provider E2E подтверждён в live `nexus-app`.

**Status:** `TEST VERIFIED` для RSS/Atom adapter.

**Evidence:**

- `B5_RSS_PROVIDER_RSS_PARSE_OK`
- `B5_RSS_SYMBOL_EXTRACTION_OK`
- `B5_RSS_EVENT_ID_DETERMINISTIC_OK`
- `B5_RSS_RAW_PAYLOAD_OK`
- `B5_RSS_ATOM_PARSE_OK`
- `B5_RSS_TIME_FILTER_OK`
- `B5_RSS_SYMBOL_FILTER_OK`
- `B5_RSS_INGESTION_OK`
- `B5_RSS_DB_PERSISTENCE_OK`
- `B5_RSS_INGESTION_DEDUP_OK`
- `B5_RSS_PROVIDER_E2E_OK`
- `B5_RSS_FAILURE_ISOLATION_E2E_OK`

**Remaining:** дополнительные provider types / source coverage могут добавляться отдельно; отсутствие других provider classes не отменяет подтверждённый RSS/Atom adapter.

## 43.7. Event storage

AI News Event model существует, а migrations для event store обнаружены.

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

**Evidence:**
- `models/ai_news_event.py`;
- News/Event migrations:
  - `b5f1e2d3c4a5_b5_event_store.py`;
  - `c2d8e4f1a607_b5_1_news_event_store.py`;
  - `d41e7c92b5f0_b5_1_news_event_schema_fix.py`.

Полная runtime verification ingestion → persistence ещё не завершена.

## 43.8. Historical event backfill

Канонически требуется исторический event context.

Фактически подтверждены backfill-relevant primitives:

- `AINewsProvider.fetch()` поддерживает `since`, `until`, `symbols`, `limit`;
- `AINewsIngestionAdapter.ingest()` передаёт time-range parameters provider-у;
- `StaticTestNewsProvider` поддерживает deterministic time-range filtering;
- `RSSNewsProvider` поддерживает `since/until` filtering;
- RSS provider time filtering подтверждено E2E;
- ingestion deduplication позволяет безопасно повторять overlapping fetch windows.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**

- `services/ai_news_ingestion.py`
- `services/ai_news_rss_provider.py`
- `B5_RSS_TIME_FILTER_OK`
- `B5_RSS_INGESTION_DEDUP_OK`

Не подтверждены:

- отдельный historical backfill orchestrator;
- historical source с достаточной глубиной истории;
- pagination/cursor traversal;
- batch window traversal;
- resumable checkpoint/state;
- dedicated historical backfill E2E;
- guaranteed retrieval полного requested historical range.

Текущий RSS provider является ограниченным external feed adapter и сам по себе не доказывает полноценный historical backfill lifecycle.

**Current blocker:** в live project audit не обнаружен historical-capable News/Event provider/API с гарантированной глубиной истории, pagination/cursor или archive access.

Проверены current code/config paths; обнаружен только RSS/Atom source layer. Отдельные NewsAPI / CryptoPanic / GDELT / EventRegistry / Finnhub / Messari-like historical adapters и соответствующая runtime configuration не обнаружены.

До выбора и архитектурного согласования historical data source полноценный backfill orchestrator реализовывать нельзя.

## 43.9. Event deduplication

Одинаковые / повторные events должны дедуплицироваться.

Фактически подтверждены:

- deterministic event identity;
- duplicate suppression на ingestion path;
- отсутствие повторной DB row для одинакового event;
- unique event ID preservation;
- RSS provider ingestion deduplication.

**Status:** `TEST VERIFIED`

**Evidence:**

- `B5_DEDUP_FIRST_INGEST_OK`
- `B5_DEDUP_SINGLE_ROW_OK`
- `B5_DEDUP_SECOND_INGEST_NO_DUPLICATE_OK`
- `B5_DEDUP_UNIQUE_EVENT_ID_OK`
- `B5_RSS_INGESTION_DEDUP_OK`

## 43.10. Event → market linkage

Event должен быть связан с market context.

Полный independent event → market persistence/linkage lifecycle не подтверждён.

**Status:** `NOT VERIFIED`

## 43.11. Event → regime linkage

Event должен быть связан с market regime.

Comparison layer способен потреблять regime context, но полный persistent event → regime linkage не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 43.12. Event → strategy linkage

Event должен быть связан с поведением Strategy Version.

Полный research lifecycle event → strategy не завершён.

**Status:** `PARTIALLY VERIFIED`

## 43.13. Event → outcome linkage

Необходимо анализировать:

- outcome before event;
- outcome during event;
- outcome after event;
- strategy degradation;
- strategy improvement.

Полный outcome-linkage engine не подтверждён.

**Status:** `NOT VERIFIED`

## 43.14. B.5 News / Event Correlation

B.5 базовый ingestion / dedup / RSS failure isolation / News-Event correlation scope завершён и подтверждён end-to-end.

Подтверждено:

- canonical News/Event ingestion;
- RSS/Atom provider;
- provider failure isolation;
- deterministic deduplication;
- symbol/global scope correlation;
- comparison context propagation;
- immutable comparison records;
- отсутствие production execution authority.

**Status:** `TEST VERIFIED / DONE`

**Evidence:**

- `B5_NEWS_INGESTION_E2E_OK`
- `B5_RSS_PROVIDER_E2E_OK`
- `B5_RSS_FAILURE_ISOLATION_E2E_OK`
- `B5_NEWS_CORRELATION_E2E_OK`

Broader News/Event Intelligence remains open outside completed B.5 scope.

## 43.15. News/Event-aware research

Knowledge / Research должны использовать historical event context при наличии данных.

Полная интеграция в research cycle не подтверждена.

**Status:** `PARTIALLY VERIFIED`

## 43.16. News/Event-aware validation

Validation должна учитывать event context в:

- Backtest;
- OOS;
- Walk-Forward;
- Paper;
- Shadow.

Полный event-aware validation pipeline не завершён.

**Status:** `NOT VERIFIED`

## 43.17. News/Event metrics

Должны существовать отдельные метрики:

- impact by event type;
- strategy performance around events;
- pre/during/post event performance;
- degradation;
- recovery;
- event-specific risk.

Отдельный полный News/Event metrics framework не подтверждён.

**Status:** `NOT VERIFIED`

## 43.18. News/Event risk controls

AIEA не должен обходить News/Event Risk restrictions и не должен самостоятельно отключать News/Event Risk controls.

**Status:** `VERIFIED` как архитектурное ограничение.

## 43.19. Comparison integration

Comparison Engine имеет News/Event context consumer:

`services/ai_comparison_news_context.py`

Это подтверждает integration на уровне comparison context, но не complete News/Event Intelligence.

**Status:** `TEST VERIFIED`

## 43.20. Production isolation

News/Event Intelligence является research/context layer и не должен:

- отправлять orders;
- bypass RiskAgent;
- bypass ExecutionAgent;
- изменять production risk limits;
- самостоятельно promotion strategy.

**Status:** `VERIFIED`

## 43.21. Итог

Подтверждены:

- News/Event model foundation;
- event normalization;
- symbol/scope context;
- comparison integration;
- migration foundation;
- research-only B.5 boundary;
- production isolation.

Частично подтверждены:

- ingestion service;
- event → regime linkage;
- event → strategy linkage;
- research integration.

Не подтверждены полностью:

- external source adapters;
- historical backfill;
- deduplication;
- event → market persistent linkage;
- event → outcome linkage;
- event-aware validation;
- event influence metrics;
- complete production-grade News/Event pipeline.

**Remaining:** завершение factual audit и дальнейшая реализация полного News & Event Intelligence контура.
## 44. DYNAMIC MARKET UNIVERSE / OPPORTUNITY DISCOVERY

**Status:** `PARTIALLY VERIFIED`

## 44.1. Каноническое назначение

NEXUS не должен ограничивать market analysis только фиксированным ручным списком символов.

Канонический контур:

`Full USDT Perpetual Universe → Market Scanner → Liquidity / Volume / Volatility Filters → Market Regime / Session → Strategy Engine → AIEA Evidence / Trust → Dynamic Opportunity Pool → RiskAgent → Execution`

## 44.2. Market infrastructure

Фактически существуют:

- `market/models.py`;
- `market/scanner.py`;
- `agents/market_agent.py`;
- `agents/market_data_agent.py`;
- `agents/market_regime_agent.py`;
- `services/market_service.py`;
- `services/market_state_builder.py`.

**Status:** `VERIFIED`

## 44.3. Market Scanner

Фактически обнаружен:

`market/scanner.py`

Scanner является основой для дальнейшего dynamic-universe analysis.

**Status:** `VERIFIED`

## 44.4. Exchange universe discovery

Канонически требуется получение доступного USDT perpetual universe непосредственно с exchange, а не только из ручного списка.

Exchange / BingX infrastructure существует, однако полный factual proof:

`exchange instruments → normalized universe → scanner`

end-to-end отдельно не завершён.

**Status:** `PARTIALLY VERIFIED`

## 44.5. Liquidity filtering

Dynamic universe должен применять liquidity filters.

В market/scanner infrastructure есть market-selection logic, однако complete production-grade liquidity policy и threshold audit не завершены.

**Status:** `PARTIALLY VERIFIED`

## 44.6. Volume filtering

Volume должен учитываться при формировании opportunity universe.

Market data infrastructure существует.

Полный unified volume ranking / filtering policy отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 44.7. Volatility filtering

Volatility является обязательным фактором market selection.

Market regime infrastructure и indicator utilities существуют.

Отдельный complete volatility threshold policy для dynamic universe не доказан.

**Status:** `PARTIALLY VERIFIED`

## 44.8. Spread / execution quality

Dynamic universe должен учитывать trading quality:

- spread;
- liquidity;
- executable market conditions.

Полный spread/execution-quality filter для universe discovery отдельно не подтверждён.

**Status:** `NOT VERIFIED`

## 44.9. Market regime integration

Market regime infrastructure существует:

- `agents/market_regime_agent.py`;
- strategy `regime_detector`;
- `services/market_state_builder.py`.

Regime должен использоваться как часть opportunity selection context.

**Status:** `VERIFIED` для regime infrastructure; `PARTIALLY VERIFIED` для full universe-selection integration.

## 44.10. Session / temporal context

Dynamic opportunity selection должна учитывать session/time context.

Общий temporal analysis существует в research/strategy layers, но отдельный universe-selection session policy не подтверждён.

**Status:** `NOT VERIFIED`

## 44.11. TOP-50 ranking

Канонически:

`Full Universe → Market Score → TOP-50`

TOP-50 должен быть результатом ranking всего допустимого universe, а не жёстким ограничением market analysis.

Отдельный exhaustive end-to-end TOP-50 ranking proof не завершён.

**Status:** `NOT VERIFIED`

## 44.12. Dynamic Opportunity Pool

После TOP-50 должен формироваться dynamic opportunity pool, из которого Strategy Engine / AIEA выбирают актуальные opportunities.

Отдельная persistent / runtime opportunity-pool сущность не подтверждена.

**Status:** `NOT VERIFIED`

## 44.13. Strategy Engine integration

Strategy Decision Engine уже получает market context и выбирает strategy.

Однако полный путь:

`Dynamic Opportunity Pool → Strategy Decision Engine`

как обязательный runtime gate отдельно не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 44.14. AIEA evidence / trust integration

Канонический dynamic universe должен учитывать:

- AIEA evidence;
- AI trust level;
- strategy validation state.

Promotion / trust infrastructure существует.

Полная runtime интеграция этих данных непосредственно в opportunity ranking не доказана.

**Status:** `PARTIALLY VERIFIED`

## 44.15. RiskAgent boundary

После candidate / opportunity selection должен сохраняться:

`→ RiskAgent → ExecutionAgent → ExecutionBoundary`

Production execution boundary уже подтверждён.

**Status:** `VERIFIED`

**Evidence:**
- production execution chain;
- ExecutionBoundary;
- E10/E12.

## 44.16. Manual symbol list

Фиксированный symbol list может оставаться конфигурационным элементом, но не должен ограничивать полный market analysis.

Отдельный exhaustive proof того, что manual list полностью перестал быть universe ceiling, не проведён.

**Status:** `PARTIALLY VERIFIED`

## 44.17. Data quality

Dynamic universe должен исключать:

- invalid market data;
- incomplete symbols;
- unsupported contracts;
- unusable liquidity;
- invalid execution conditions.

Data quality infrastructure существует.

Полный universe-level fail-closed audit не завершён.

**Status:** `PARTIALLY VERIFIED`

## 44.18. Multi-symbol isolation

Backtest / comparison / research infrastructure уже поддерживает multi-symbol analysis.

**Status:** `TEST VERIFIED`

**Evidence:**
- BLOCK D multi-symbol;
- BLOCK F symbol alignment;
- B1 research slices.

## 44.19. Production safety

Dynamic Market Universe не должен предоставлять самостоятельный execution authority.

Final execution boundary остаётся:

`RiskAgent → ExecutionAgent → ExecutionBoundary`

**Status:** `VERIFIED`

## 44.20. Итог

Подтверждены:

- market/scanner infrastructure;
- market data infrastructure;
- regime infrastructure;
- multi-symbol research/validation;
- final Risk/Execution boundary.

Частично подтверждены:

- full exchange universe discovery;
- liquidity filtering;
- volume filtering;
- volatility filtering;
- regime integration;
- Strategy Engine integration;
- AIEA evidence/trust integration;
- manual-list non-limiting behaviour;
- universe-level data quality.

Не подтверждены полностью:

- spread/execution-quality filtering;
- session-aware universe policy;
- TOP-50 global ranking;
- Dynamic Opportunity Pool;
- полный end-to-end runtime:

`Full Universe → Scanner → Filters → TOP-50 → Opportunity Pool → Strategy → AIEA → Risk → Execution`.

**Remaining:** отдельный factual audit Dynamic Market Universe / Opportunity Discovery runtime pipeline.
## 45. PRODUCTION SAFETY

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

## 45.1. Каноническое назначение

Production Safety должен обеспечивать:

- невозможность прямого AI execution;
- обязательный RiskAgent;
- обязательный ExecutionAgent;
- ExecutionBoundary перед exchange;
- AI permission checks;
- promotion-stage checks;
- risk approval;
- protection validation;
- fail-safe;
- rollback;
- kill switch;
- production isolation;
- multi-user isolation.

## 45.2. ExecutionBoundary

Фактически существует:

`services/execution_boundary.py`

Он является канонической технической границей перед exchange execution.

**Status:** `VERIFIED`

**Evidence:**
- production execution audit;
- `BaseExchangeClient.place_order()` вызывается через boundary.

## 45.3. AIProductionSafetyService

Фактически существует:

`services/ai_production_safety.py`

Safety layer выполняется до exchange execution и не должен самостоятельно размещать orders.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10;
- E12.

## 45.4. Global trading kill-switch

Execution path проверяет:

`allow_new_order()`

до фактического exchange order.

**Status:** `VERIFIED`

## 45.5. RiskAgent boundary

Production flow требует:

`StrategyDecisionEngine → AIRiskAgent → ExecutionAgent`

AIEA не должен обходить RiskAgent.

**Status:** `TEST VERIFIED`

**Evidence:**
- section 18;
- E10;
- E12.

## 45.6. ExecutionAgent boundary

Production order проходит через `ExecutionAgent` перед `ExecutionBoundary`.

**Status:** `VERIFIED`

**Evidence:**
- `agents/execution_agent.py`;
- execution flow audit.

## 45.7. Promotion permission check

AI promotion execution должен соответствовать:

- valid promotion stage;
- valid permission;
- risk approval;
- valid identity;
- non-rolled-back strategy.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5;
- E6;
- E10;
- E12.

## 45.8. Production strategy isolation

AIEA не должен самостоятельно заменить production strategy.

Promotion is controlled mutation boundary.

**Status:** `TEST VERIFIED`

**Evidence:**
- E1;
- E6;
- E10;
- E12.

## 45.9. Protection validation

После открытия production position проверяются реальные активные SL/TP orders через `get_open_orders()`.

**Status:** `VERIFIED`

**Evidence:**
- production protection fail-safe audit.

## 45.10. Protection fail-safe

Если SL/TP не подтверждены, запускается market close с:

`close_reason="PROTECTION_FAILSAFE"`

**Status:** `VERIFIED`

## 45.11. Rollback

Rollback:

- использует genealogy;
- сохраняет parent;
- отзывает permissions;
- сохраняет history;
- создаёт audit.

**Status:** `TEST VERIFIED / DONE`

**Evidence:**
- E8;
- E9.

## 45.12. Multi-user production isolation

A8/E11 подтверждают cross-user isolation для AI identity/evidence/promotion chains.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8;
- E11.

## 45.13. Current live restrictions

Текущие состояния:

- `Strategy Decision Engine = SHADOW-ONLY`;
- `Advisory = OBSERVE_ONLY`;
- `Restricted Live = DISABLED`;
- `Full Live = DISABLED`.

**Status:** `VERIFIED`

## 45.14. AI direct exchange access

AIEA не должен иметь прямого execution access к BingX.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10;
- E12;
- ExecutionBoundary.

## 45.15. Production safety versus dedicated AI controls

Уже подтверждены общие production safety boundaries.

Не закрыты полностью dedicated AIEA controls:

- `AI_LIVE_KILL_SWITCH`;
- dedicated AI risk budget;
- dedicated Restricted Live exposure limits;
- complete AI Live activation state machine;
- live-stage runtime degradation triggers.

**Status:** `PARTIALLY VERIFIED`

## 45.16. Fail-closed principle

Небезопасное AI request должен останавливаться до `place_order()`.

E10 подтверждает:

- missing risk approval blocked;
- non-live stage blocked;
- rolled-back strategy blocked;
- permission escalation blocked;
- valid safety pass.

**Status:** `TEST VERIFIED`

## 45.17. Production safety audit coverage

Production safety покрывает основные currently active production boundaries.

Полный negative-path audit всех будущих AI Live paths невозможен до их controlled activation и поэтому остаётся отдельной future verification task.

**Status:** `PARTIALLY VERIFIED`

## 45.18. Итог

Подтверждены:

- ExecutionBoundary;
- AIProductionSafetyService;
- global kill-switch;
- RiskAgent boundary;
- ExecutionAgent boundary;
- promotion permission checks;
- protection validation;
- protection fail-safe;
- rollback safety;
- multi-user isolation;
- production isolation;
- current live-disabled state;
- fail-closed execution.

Не закрыты:

- dedicated AI live risk budget;
- dedicated AI kill switch;
- Restricted Live runtime;
- Full Live runtime;
- future live-stage degradation triggers.

**Remaining:** dedicated AIEA live-control factual audit before any live activation.
## 46. APPLICATION / PRODUCTION SECURITY

**Status:** `PARTIALLY VERIFIED`

## 46.1. Каноническое назначение

Application / Production Security должна обеспечивать:

- secrets protection;
- API credential protection;
- log redaction;
- authentication;
- authorization;
- multi-user isolation;
- AI-generated code isolation;
- production execution protection;
- audit logging;
- secure configuration;
- protection of production infrastructure.

## 46.2. Authentication infrastructure

В проекте существуют:

- `routers/auth.py`;
- `models/user.py`;
- authentication-related application logic;
- login / register templates.

FastAPI application содержит authentication routes.

**Status:** `VERIFIED` для существования authentication infrastructure.

**Remaining:** полноценный security audit authentication implementation.

## 46.3. Authorization

Production API должен различать уровни доступа и запрещать unauthorized mutations.

Promotion infrastructure имеет собственные permission policies.

Отдельная exhaustive authorization matrix всего приложения не проведена.

**Status:** `PARTIALLY VERIFIED`

## 46.4. Multi-user isolation

A8/E11 подтверждают AI identity isolation между users.

**Status:** `TEST VERIFIED` для AIEA identity / promotion scope.

Однако полная application-wide isolation для всех routers / database queries не подтверждена.

**Status:** `PARTIALLY VERIFIED` для общего application scope.

**Evidence:**
- A8;
- E11.

## 46.5. Secrets handling

В repository обнаружен:

`.env`

Наличие environment-based configuration не доказывает корректность secrets lifecycle.

Требуются:

- отсутствие credentials в source;
- отсутствие secrets в logs;
- безопасная runtime injection;
- отсутствие secrets в AI sandbox;
- rotation / revocation procedure.

**Status:** `NOT VERIFIED`

## 46.6. API credential protection

Exchange credentials должны быть недоступны AIEA research / sandbox components.

Production execution использует exchange client layer.

Однако отдельный exhaustive credential-isolation audit для всех services не завершён.

**Status:** `PARTIALLY VERIFIED`

## 46.7. Log redaction

Активные exchange credential leakage paths проверены и очищены.

Подтверждено отсутствие ранее найденных sensitive outputs в:

- `services/exchange_service.py`;
- `routers/exchanges.py`;
- `clients/bingx.py`.

**Status:** `TEST VERIFIED` для текущего exchange logging scope.

**Evidence:**

- `SECRET_REDACTION_COMPILE_OK`
- `SECRET_REDACTION_NEGATIVE_GREP_OK`
- `SECRET_REDACTION_CRYPTO_TEST_OK`

**Remaining:** application-wide exhaustive log-redaction audit вне текущего exchange scope.

## 46.8. Production execution protection

Production execution имеет:

- `ExecutionBoundary`;
- `AIProductionSafetyService`;
- RiskAgent;
- kill-switch;
- protection validation.

**Status:** `TEST VERIFIED`

**Evidence:**
- E10;
- E12;
- section 45.

## 46.9. AI-generated code isolation

Static validator существует, но runtime sandbox полностью не доказан.

**Status:** `PARTIALLY VERIFIED`

**Evidence:**
- section 30;
- D.1 static validation.

## 46.10. Database security

Database models и identity constraints существуют.

Однако полный security audit:

- credentials;
- least privilege;
- connection isolation;
- sandbox DB isolation;
- migration permissions;
- direct mutation paths

не завершён.

**Status:** `PARTIALLY VERIFIED`

## 46.11. Secure configuration

Production configuration должна предотвращать самостоятельное изменение AI:

- risk limits;
- promotion thresholds;
- live permissions;
- account settings;
- exchange credentials.

Promotion and safety services защищают значительную часть runtime policy.

Полная configuration mutation audit не завершена.

**Status:** `PARTIALLY VERIFIED`

## 46.12. AI permission containment

AIEA не должен самостоятельно:

- повышать trust;
- повышать promotion level;
- менять risk limits;
- менять account settings;
- bypass RiskAgent;
- bypass ExecutionAgent;
- directly call exchange execution.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5;
- E6;
- E10;
- E12;
- A8/E11.

## 46.13. Audit logging

AI audit infrastructure существует:

`models/ai_audit_log.py`

Promotion/rollback audit также реализованы.

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

Полное coverage всех application security events не доказано.

## 46.14. Dependency / supply-chain security

Production security должна учитывать:

- pinned/controlled dependencies;
- vulnerability scanning;
- trusted build process;
- image provenance;
- package update policy.

Отдельный dependency/image security audit в текущем проекте не выполнен.

**Status:** `NOT VERIFIED`

## 46.15. Container / host security

Docker infrastructure существует.

Полный audit:

- container privileges;
- filesystem mounts;
- host access;
- Docker socket;
- network isolation;
- secret exposure

не проведён.

**Status:** `NOT VERIFIED`

## 46.16. Network security

Production application должна быть защищена на network boundary.

В repository обнаружен `nginx/` и `nginx.conf`, но complete deployment/network-security audit отдельно не проведён.

**Status:** `PARTIALLY VERIFIED`

## 46.17. Security testing

Существуют application tests:

- `tests/test_auth.py`;
- `tests/test_crypto.py`;
- A8/E10/E11/E12 security/isolation tests.

**Status:** `TEST VERIFIED` для отдельных security scopes.

Complete application-wide security test suite отсутствует/не подтверждена.

## 46.18. Production secret leakage

Ранее найденные active exchange credential leakage paths устранены и проверены.

Проверены:

- decrypted API credential debug output;
- exchange request API-key prefix output;
- BingX request headers / signed URL debug output;
- BingX raw response debug output.

**Status:** `TEST VERIFIED` для текущего exchange credential logging scope.

**Evidence:**

- `SECRET_REDACTION_COMPILE_OK`
- `SECRET_REDACTION_NEGATIVE_GREP_OK`
- `SECRET_REDACTION_CRYPTO_TEST_OK`

Permanent requirement сохраняется: credentials, secrets, signatures и signed request material не должны сериализоваться в production logs.

## 46.19. Incident / key rotation readiness

Production security должна иметь controlled:

- credential revocation;
- key rotation;
- compromised-secret response;
- incident audit.

Полный operational procedure в текущем Audit не доказан.

**Status:** `NOT VERIFIED`

## 46.20. Итог

Подтверждены частично/локально:

- authentication infrastructure;
- AIEA identity isolation;
- production execution safety;
- AI permission containment;
- AI audit infrastructure;
- отдельные security tests.

Не подтверждены полностью:

- secrets lifecycle;
- exchange credential isolation;
- log redaction;
- full authorization matrix;
- dependency/supply-chain security;
- container security;
- network security;
- incident/key rotation procedures;
- application-wide security regression suite.

**Remaining:** полный Application / Production Security audit с negative-path проверками и отдельным evidence по каждому security control.
## 47. FULL DASHBOARD REWORK

**Status:** `PARTIALLY VERIFIED`

## 47.1. Каноническое требование

Dashboard должен быть полностью переработан как единый observability/control surface NEXUS.

Он должен обеспечивать отдельное представление:

- Production;
- Grid;
- AIEA Research;
- Validation;
- Paper;
- Shadow;
- Advisory;
- Promotion;
- Restricted Live;
- Full Live;
- News/Event Intelligence;
- Dynamic Market Universe;
- Security / Audit.

Dashboard не должен смешивать experimental и production state.

## 47.2. Existing dashboard infrastructure

Фактически существуют:

- `routers/dashboard.py`;
- `templates/dashboard.html`;
- `static/js/dashboard.js`;
- dashboard-related API routes.

**Status:** `VERIFIED`

## 47.3. AI Evolution dashboard

Канонически требуется отдельный AI Evolution surface.

Он должен отображать:

- AI trust level;
- active model;
- experiments;
- strategy versions;
- hypotheses;
- lessons;
- validation;
- paper;
- shadow;
- comparison;
- promotion;
- rollback;
- News/Event;
- AI performance.

Полный dedicated AI Evolution UI не подтверждён.

**Status:** `NOT VERIFIED`

## 47.4. Production / Experimental separation

Dashboard должен явно разделять:

- production trades;
- Grid;
- AI Paper;
- AI Shadow;
- AI Live;
- Manual;
- comparison-only participants.

Backend trade_source/comparison separation существует.

Полное UI enforcement не доказано.

**Status:** `PARTIALLY VERIFIED`

## 47.5. Validation observability

Dashboard должен показывать:

- validation stage;
- dataset;
- strategy version;
- evidence;
- metrics;
- pass/fail;
- degradation;
- sufficiency.

Validation backend infrastructure существует.

UI mapping полного validation evidence не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 47.6. Promotion observability

Dashboard должен отображать:

- current promotion stage;
- promotion level;
- permissions;
- risk approval;
- evidence;
- approval metadata;
- rollback status.

Promotion backend реализован E.1–E.12.

Полный UI отображения не доказан.

**Status:** `PARTIALLY VERIFIED`

## 47.7. News/Event observability

Dashboard должен показывать:

- high-impact events;
- source;
- event timing;
- affected symbols;
- direction;
- impact;
- risk window;
- strategy response;
- outcome.

News/Event backend foundation существует.

Полный dashboard presentation не подтверждён.

**Status:** `NOT VERIFIED`

## 47.8. Dynamic Market Universe observability

Dashboard должен отображать:

- discovered universe;
- filters;
- ranking;
- TOP-50;
- opportunity pool;
- selected opportunities;
- rejected opportunities;
- reasons for rejection.

Dynamic Market Universe dashboard surface не подтверждён.

**Status:** `NOT VERIFIED`

## 47.9. Security / audit observability

Dashboard должен предоставлять controlled visibility into:

- AI audit;
- promotion audit;
- rollback audit;
- security events;
- kill-switch events;
- permission changes.

AI/promotion audit backend существует.

Полный secure audit UI не подтверждён.

**Status:** `PARTIALLY VERIFIED`

## 47.10. Multi-user dashboard isolation

Dashboard должен показывать только разрешённые данным пользователю objects.

A8/E11 underlying identity isolation подтверждена, но full dashboard-layer authorization отдельно не проверена.

**Status:** `PARTIALLY VERIFIED`

## 47.11. Mutation safety

Dashboard controls не должны обходить backend:

- RiskAgent;
- Promotion Gates;
- Risk Approval;
- Permission Service;
- Rollback Integrity;
- Kill Switch.

Backend controls существуют.

Полный UI negative-path test не выполнен.

**Status:** `PARTIALLY VERIFIED`

## 47.12. State consistency

Dashboard должен получать state из canonical backend sources, а не поддерживать собственную конкурирующую state machine.

Это особенно важно для:

- promotion stage;
- permission;
- strategy status;
- experiment status;
- AI trust level.

Архитектурное требование зафиксировано, но complete consistency audit не выполнен.

**Status:** `PARTIALLY VERIFIED`

## 47.13. Full rework scope

Полная переработка должна включать как минимум:

1. Information architecture;
2. AI Evolution section;
3. Validation monitoring;
4. Comparison analytics;
5. Promotion/rollback;
6. News/Event Intelligence;
7. Dynamic Market Universe;
8. Security/Audit;
9. Multi-user isolation;
10. source-separated PnL;
11. production safety state;
12. future Restricted Live / Full Live observability.

**Status:** `NOT VERIFIED`

## 47.14. Итог

Подтверждены:

- existing dashboard infrastructure;
- backend data sources;
- promotion/audit backend;
- comparison backend;
- validation backend.

Не подтверждены полностью:

- complete AI Evolution Dashboard;
- full source-separated observability;
- validation UI;
- promotion/rollback UI;
- News/Event UI;
- Dynamic Opportunity UI;
- Security/Audit UI;
- complete multi-user dashboard isolation;
- full UI mutation safety;
- full dashboard rework.

**Remaining:** отдельный full Dashboard audit + redesign + implementation + UI security verification.
## 48. MULTI-USER / ISOLATION

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

## 48.1. Каноническое требование

Все user-owned AI objects должны быть изолированы между пользователями:

- AI Agent;
- Knowledge Snapshot;
- Hypothesis;
- Strategy Version;
- Experiment;
- Validation Evidence;
- Memory / Lessons;
- Promotion state;
- Promotion audit;
- Rollback;
- Comparison data;
- News/Event research data.

Cross-user object substitution и mutation должны блокироваться.

## 48.2. A8 identity isolation

A8 является фактически подтверждённым foundation isolation layer.

Проверены:

- `A8_TWO_IDENTITY_CHAINS_CREATED_OK`;
- `A8_SAME_USER_CHAINS_OK`;
- `A8_CROSS_USER_SNAPSHOT_BLOCKED_OK`;
- `A8_CROSS_USER_EXPERIMENT_TAMPER_BLOCKED_OK`;
- `A8_CROSS_USER_EVIDENCE_BLOCKED_OK`;
- `A8_SAME_USER_EVIDENCE_OK`;
- `A8_IDENTITY_CHAINS_REMAIN_ISOLATED_OK`;
- `A8_PRODUCTION_ISOLATION_OK`;
- `A8_CLEANUP_OK`.

**Status:** `TEST VERIFIED`

## 48.3. Hypothesis isolation

Hypothesis должна принадлежать правильному user и не может использоваться cross-user.

**Status:** `TEST VERIFIED`

**Evidence:**
- A8;
- E11 identity chain tests.

## 48.4. Strategy Version isolation

Strategy Version должна быть связана с корректным user / hypothesis / experiment.

Cross-user Strategy Version substitution блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `E11_CROSS_USER_VERSION_BLOCKED_OK`.

## 48.5. Experiment isolation

Experiment должен принадлежать правильной identity chain.

Cross-user experiment tampering блокируется.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A8_CROSS_USER_EXPERIMENT_TAMPER_BLOCKED_OK`;
- A8/E11.

## 48.6. Validation Evidence isolation

Evidence должна совпадать по:

- user;
- experiment;
- strategy version;
- hypothesis.

Cross-user evidence blocked.

**Status:** `TEST VERIFIED`

**Evidence:**
- `A8_CROSS_USER_EVIDENCE_BLOCKED_OK`;
- E4 evidence binding;
- E11.

## 48.7. Promotion isolation

Promotion должен использовать ту же identity chain.

Cross-user version / hypothesis / evidence substitution должна блокироваться.

**Status:** `TEST VERIFIED`

**Evidence:**
- E11 cross-user tests;
- E12 integration.

## 48.8. Risk Approval isolation

Risk approval должна быть связана с соответствующим:

- user;
- experiment;
- strategy version;
- hypothesis;
- target stage.

Cross-experiment / cross-identity approval должен блокироваться.

**Status:** `TEST VERIFIED`

**Evidence:**
- E5 cross-experiment guard;
- E11 identity isolation.

## 48.9. Memory isolation

AI Memory должна быть user-scoped.

**Status:** `TEST VERIFIED`

**Evidence:**
- `B4_USER_MEMORY_ISOLATION_OK`;
- `B4_EXPERIMENT_OWNERSHIP_OK`.

## 48.10. Audit isolation

Audit records должны соответствовать identity chain и не позволять cross-user mutation.

Promotion audit snapshots уже identity-bound.

**Status:** `TEST VERIFIED / PARTIALLY VERIFIED`

Полный application-wide audit isolation не проверен.

## 48.11. Comparison isolation

Comparison observations/results должны сохранять participant and identity semantics.

BLOCK F review подтверждает source/identity separation.

Полный cross-user comparison isolation отдельно не завершён.

**Status:** `PARTIALLY VERIFIED`

## 48.12. News/Event isolation

User-specific News/Event research data, если такая привязка используется, должна быть изолирована.

Полный user-scoped event research audit пока не проведён.

**Status:** `NOT VERIFIED`

## 48.13. API-layer isolation

Underlying database/service isolation подтверждена для A8/E11 scopes.

Однако полный HTTP/API audit всех user-facing routes не проведён.

**Status:** `PARTIALLY VERIFIED`

## 48.14. Dashboard isolation

Dashboard должен показывать только разрешённые текущему user objects.

A8 не доказывает автоматически dashboard-layer isolation.

**Status:** `PARTIALLY VERIFIED`

## 48.15. Database query isolation

Все user-scoped queries должны требовать корректный user identity context.

Отдельный exhaustive audit всех AI-related query paths не завершён.

**Status:** `PARTIALLY VERIFIED`

## 48.16. Cross-user mutation protection

Нельзя позволять:

- strategy substitution;
- experiment tampering;
- evidence substitution;
- permission escalation;
- promotion mutation;
- memory leakage.

A8/E11/E5/E6/E10 подтверждают соответствующие critical boundaries.

**Status:** `TEST VERIFIED`

## 48.17. Production isolation

Cross-user isolation должна сохраняться без влияния на production strategy / execution.

A8/E10/E11/E12 подтверждают production isolation.

**Status:** `TEST VERIFIED`

## 48.18. Итог

Полностью подтверждено тестами:

- A8 identity chains;
- cross-user snapshot protection;
- cross-user experiment protection;
- cross-user evidence protection;
- strategy version identity;
- promotion isolation;
- risk approval isolation;
- memory isolation;
- production isolation.

Частично подтверждено:

- audit isolation;
- comparison isolation;
- API isolation;
- Dashboard isolation;
- database query isolation.

Не подтверждено полностью:

- News/Event user-scoped isolation;
- application-wide exhaustive multi-user isolation.

**Remaining:** full application-wide multi-user isolation audit across all routers, services, models and user-scoped queries.
## 49. TECHNICAL DEBT / FOLLOW-UP

**Status:** `IN PROGRESS`

## 49.1. Назначение

Этот раздел содержит только те технические проблемы и follow-up items, которые:

- обнаружены фактическим аудитом;
- не являются отдельным обязательным архитектурным разделом;
- требуют отдельного технического решения;
- не должны быть потеряны между рабочими итерациями.

Архитектурные задачи должны оставаться в соответствующих разделах Audit.

## 49.2. Documentation debt

Необходимо поддерживать:

- единый `NEXUS_PROJECT_AUDIT.md` как живую canonical state point;
- актуальный evidence mapping;
- один primary NEXT STEP;
- отсутствие противоречий между status records.

**Status:** `IN PROGRESS`

## 49.3. Evidence mapping debt

Необходимо довести до завершения:

- per-item evidence mapping для всех архитектурных sections;
- explicit evidence для каждого `DONE`/`VERIFIED` пункта;
- distinction между code existence и behavioural proof.

**Status:** `IN PROGRESS`

## 49.4. Registry lifecycle debt

Остаётся:

- exhaustive status transition matrix;
- direct mutation negative-path audit;
- unified runtime registry authority.

**Status:** `OPEN`

## 49.5. Learning Loop debt

Остаётся:

- cycle identity;
- automatic lesson → modification feedback;
- automatic retest;
- full autonomous learning cycle audit.

**Status:** `OPEN`

## 49.6. News/Event debt

Остаётся:

- external source adapters;
- historical backfill;
- deduplication;
- event linkage;
- event/outcome analysis;
- validation integration;
- influence metrics.

Основная tracking section:

`43. NEWS & EVENT INTELLIGENCE`

**Status:** `OPEN`

## 49.7. Dynamic Universe debt

Остаётся:

- complete exchange universe discovery;
- normalized scanner input;
- spread/execution-quality filtering;
- session policy;
- TOP-50 ranking;
- dynamic opportunity pool;
- end-to-end runtime integration.

Основная tracking section:

`44. DYNAMIC MARKET UNIVERSE / OPPORTUNITY DISCOVERY`

**Status:** `OPEN`

## 49.8. Sandbox security debt

Остаётся:

- runtime sandbox;
- CPU/memory/time limits;
- network isolation;
- filesystem isolation;
- secret isolation;
- database isolation;
- Docker socket protection.

Основная tracking section:

`30. Безопасность AI-generated Code`

**Status:** `OPEN`

## 49.9. AI Live control debt

Остаётся:

- dedicated AI risk budget;
- Restricted Live limits;
- dedicated AI kill switch;
- AI Live activation state;
- live degradation triggers.

Основные tracking sections:

`17. Restricted Live`
`28. Kill Switch`
`45. PRODUCTION SAFETY`

**Status:** `OPEN`

## 49.10. API debt

Остаётся:

- complete AIEA API;
- authorization matrix;
- user isolation at HTTP layer;
- mutation audit coverage.

Основная tracking section:

`34. API`

**Status:** `OPEN`

## 49.11. Dashboard debt

Остаётся:

- full AI Evolution UI;
- source-separated observability;
- News/Event UI;
- Dynamic Universe UI;
- promotion/rollback UI;
- security controls;
- dashboard-layer isolation.

Основная tracking section:

`47. FULL DASHBOARD REWORK`

**Status:** `OPEN`

## 49.12. Application security debt

Остаётся:

- secrets lifecycle;
- log redaction audit;
- dependency/security audit;
- container/network audit;
- key rotation / incident procedure;
- application-wide security regression suite.

Основная tracking section:

`46. APPLICATION / PRODUCTION SECURITY`

**Status:** `OPEN`

## 49.13. Metadata propagation debt

Остаётся отдельная runtime verification для:

- `ai_experiment_id`;
- `ai_decision_id`;
- strategy version;
- trade_source

через соответствующие lifecycle paths.

Основная tracking section:

`32. Связь с существующей моделью NEXUS`

**Status:** `OPEN`

## 49.14. Time / timezone debt

Обнаружен общий follow-up:

- UTC normalization;
- explicit timeframe/timezone semantics;
- alignment consistency across analytics/comparison.

**Status:** `OPEN`

## 49.15. Statistical sufficiency debt

До использования research/comparison results для promotion должны существовать:

- minimum sample guards;
- insufficient-data handling;
- statistical significance checks;
- degradation checks;
- robustness checks.

Некоторые guards уже существуют, но общий cross-stage policy audit ещё не завершён.

**Status:** `PARTIALLY VERIFIED`

## 49.16. Source isolation debt

Должно оставаться запрещённым implicit aggregation между:

- REAL;
- GRID;
- TEST;
- AI_PAPER;
- AI_SHADOW;
- AI_LIVE;
- LEGACY.

**Status:** `TEST VERIFIED / CONTINUOUS REQUIREMENT`

## 49.17. Technical debt rule

Technical debt не должен автоматически становиться следующим implementation step.

Перед началом работы каждый item должен быть:

`FACT → CHECK → EVIDENCE → AUDIT → STATUS`

После чего выбирается один primary next step.

## 49.18. Итог

Главные открытые технические направления:

- Registry lifecycle;
- Learning Loop;
- News/Event;
- Dynamic Universe;
- Sandbox security;
- AI Live controls;
- API;
- Dashboard;
- Application Security;
- metadata propagation;
- timezone hardening;
- statistical sufficiency.

Архитектурные задачи уже закреплены в sections 1–48 и не должны дублироваться здесь как независимые планы.

**Remaining:** поддерживать этот раздел как индекс незакрытых технических долгов и удалять item отсюда только после его фактического закрытия в основном разделе.
## 50. VERIFIED EVIDENCE INDEX

**Status:** `VERIFIED`

Этот раздел является индексом уже полученного evidence. Он не заменяет подробные audit sections.

## 50.1. Foundation / Isolation

| Area | Evidence | Status |
|---|---|---|
| A8 | `A8_TWO_IDENTITY_CHAINS_CREATED_OK` | TEST VERIFIED |
| A8 | `A8_SAME_USER_CHAINS_OK` | TEST VERIFIED |
| A8 | `A8_CROSS_USER_SNAPSHOT_BLOCKED_OK` | TEST VERIFIED |
| A8 | `A8_CROSS_USER_EXPERIMENT_TAMPER_BLOCKED_OK` | TEST VERIFIED |
| A8 | `A8_CROSS_USER_EVIDENCE_BLOCKED_OK` | TEST VERIFIED |
| A8 | `A8_SAME_USER_EVIDENCE_OK` | TEST VERIFIED |
| A8 | `A8_IDENTITY_CHAINS_REMAIN_ISOLATED_OK` | TEST VERIFIED |
| A8 | `A8_PRODUCTION_ISOLATION_OK` | TEST VERIFIED |
| A8 | `A8_CLEANUP_OK` | TEST VERIFIED |

## 50.2. Research / Knowledge

| Area | Evidence | Status |
|---|---|---|
| B4 | `B4_AGENT_OK` | TEST VERIFIED |
| B4 | `B4_LESSON_RECORD_OK` | TEST VERIFIED |
| B4 | `B4_USER_MEMORY_ISOLATION_OK` | TEST VERIFIED |
| B4 | `B4_EXPERIMENT_OWNERSHIP_OK` | TEST VERIFIED |
| B4 | `B4_APPEND_ONLY_MEMORY_OK` | TEST VERIFIED |
| B4 | `B4_RESEARCH_MEMORY_ONLY_OK` | TEST VERIFIED |
| B4 | `B4_CLEANUP_OK` | TEST VERIFIED |
| B2 | `B2_REGIME_CONTRAST_OK` | TEST VERIFIED |
| B2 | `B2_HYPOTHESIS_STRUCTURE_OK` | TEST VERIFIED |
| B2 | `B2_VALIDATION_REQUIRED_OK` | TEST VERIFIED |

## 50.3. Validation

| Area | Evidence | Status |
|---|---|---|
| D | D.1–D.6.8 completed | DONE |
| D | `D6_8_BLOCK_D_FULL_COMPILE_OK` | TEST VERIFIED |

## 50.4. Promotion

| Area | Evidence | Status |
|---|---|---|
| E1 | `E1_READY_PROMOTION_OK` | TEST VERIFIED |
| E1 | `E1_PROMOTION_STATE_PERSISTED_OK` | TEST VERIFIED |
| E2 | `E2_VALID_FORWARD_TRANSITION_OK` | TEST VERIFIED |
| E2 | `E2_SKIP_STAGE_BLOCKED_OK` | TEST VERIFIED |
| E2 | `E2_BACKWARD_TRANSITION_BLOCKED_OK` | TEST VERIFIED |
| E3 | `E3_BACKTEST_PASS_OK` | TEST VERIFIED |
| E3 | `E3_OOS_PASS_OK` | TEST VERIFIED |
| E3 | `E3_OOS_INSUFFICIENT_DATA_BLOCKED_OK` | TEST VERIFIED |
| E3 | `E3_MISSING_RESULT_BLOCKED_OK` | TEST VERIFIED |
| E4 | `E4_EXACT_EVIDENCE_SET_BOUND_OK` | TEST VERIFIED |
| E5 | `E5_NOT_EVALUATED_BLOCKED_OK` | TEST VERIFIED |
| E5 | `E5_REJECT_BLOCKED_OK` | TEST VERIFIED |
| E5 | `E5_MANAGER_RISK_APPROVAL_PASS_OK` | TEST VERIFIED |
| E6 | `E6_ALL_STAGE_LEVELS_VALID_OK` | TEST VERIFIED |
| E6 | `E6_STAGE_LEVEL_MISMATCH_BLOCKED_OK` | TEST VERIFIED |
| E6 | `E6_UNKNOWN_STAGE_BLOCKED_OK` | TEST VERIFIED |
| E6 | `E6_PERMISSION_ESCALATION_BLOCKED_OK` | TEST VERIFIED |
| E7 | `E7_PROMOTION_AUDIT_SNAPSHOT_OK` | TEST VERIFIED |
| E7 | `E7_HISTORICAL_SNAPSHOT_STABLE_OK` | TEST VERIFIED |
| E8 | `E8_ROLLBACK_EXECUTED_OK` | TEST VERIFIED |
| E8 | `E8_PARENT_VERSION_PRESERVED_OK` | TEST VERIFIED |
| E8 | `E8_ROLLED_BACK_PERMISSION_REVOKED_OK` | TEST VERIFIED |
| E8 | `E8_HISTORY_PRESERVED_OK` | TEST VERIFIED |
| E9 | `E9_VALID_GENEALOGY_FIXTURE_OK` | TEST VERIFIED |
| E9 | `E9_PARENT_REQUIRED_BLOCKED_OK` | TEST VERIFIED |
| E9 | `E9_HYPOTHESIS_MISMATCH_BLOCKED_OK` | TEST VERIFIED |
| E9 | `E9_STAGE_LEVEL_MISMATCH_BLOCKED_OK` | TEST VERIFIED |
| E9 | `E9_PARENT_APPROVAL_REQUIRED_OK` | TEST VERIFIED |
| E9 | `E9_PARENT_STATUS_MISMATCH_BLOCKED_OK` | TEST VERIFIED |
| E9 | `E9_SECOND_ROLLBACK_BLOCKED_OK` | TEST VERIFIED |
| E10 | `E10_AI_NO_RISK_APPROVAL_BLOCKED_OK` | TEST VERIFIED |
| E10 | `E10_AI_NON_LIVE_BLOCKED_OK` | TEST VERIFIED |
| E10 | `E10_AI_ROLLED_BACK_BLOCKED_OK` | TEST VERIFIED |
| E10 | `E10_AI_PERMISSION_ESCALATION_BLOCKED_OK` | TEST VERIFIED |
| E10 | `E10_AI_VALID_SAFETY_PASS_OK` | TEST VERIFIED |
| E11 | `E11_CROSS_USER_VERSION_BLOCKED_OK` | TEST VERIFIED |
| E11 | `E11_CROSS_USER_HYPOTHESIS_BLOCKED_OK` | TEST VERIFIED |
| E11 | `E11_CROSS_USER_EVIDENCE_BLOCKED_OK` | TEST VERIFIED |
| E12 | `E12_READINESS_AND_FORMAL_GATE_OK` | TEST VERIFIED |
| E12 | `E12_RISK_GATE_CANNOT_BE_BYPASSED_OK` | TEST VERIFIED |
| E12 | `E12_PROMOTION_OK` | TEST VERIFIED |
| E12 | `E12_PERMISSION_AND_AUDIT_CHAIN_OK` | TEST VERIFIED |
| E12 | `E12_PRODUCTION_SAFETY_CHAIN_OK` | TEST VERIFIED |
| E12 | `E12_ROLLBACK_OK` | TEST VERIFIED |
| E12 | `E12_ROLLBACK_INTEGRITY_OK` | TEST VERIFIED |
| E12 | `E12_PRODUCTION_ISOLATION_OK` | TEST VERIFIED |
| E12 | `E12_CLEANUP_OK` | TEST VERIFIED |

## 50.5. Comparison

| Area | Evidence | Status |
|---|---|---|
| F | F.1–F.9 completed + reviewed | DONE + REVIEWED |
| F | F-REVIEW-1 | TEST VERIFIED |
| F | F-REVIEW-2 | TEST VERIFIED |
| F | F-REVIEW-3 | TEST VERIFIED |
| F | F-REVIEW-4 | TEST VERIFIED |
| F | F-REVIEW-5 | TEST VERIFIED |

## 50.6. Production Safety

| Area | Evidence | Status |
|---|---|---|
| Execution | ExecutionBoundary chain | VERIFIED |
| Protection | SL/TP verification | VERIFIED |
| Protection | `PROTECTION_FAILSAFE` | VERIFIED |
| AI Safety | E10 production safety | TEST VERIFIED |
| AI Safety | E12 production isolation | TEST VERIFIED |

## 50.7. Evidence integrity rule

Evidence listed here may only be used to mark a section as completed when the corresponding detailed section contains the scope and limitations of that evidence.

Presence of an evidence marker alone does not prove unrelated requirements.

**Remaining:** periodically extend this index whenever new evidence is created.
## 51. CURRENT BLOCKERS / OPEN ITEMS

**Status:** `OPEN`

Этот раздел содержит только фактически незавершённые либо ещё не полностью доказанные направления.

## 51.1. A9 — Foundation / Isolation

**Status:** `TEST VERIFIED / DONE`

A9 Foundation / Isolation scope фактически завершён и подтверждён end-to-end тестом.

Verified evidence:

- `A9_AGENT_OK`
- `A9_SNAPSHOT_OK`
- `A9_HYPOTHESIS_OK`
- `A9_EXPERIMENT_STRATEGY_VERSION_OK`
- `A9_VALIDATION_EVIDENCE_OK`
- `A9_AUDIT_OK`
- `A9_TRADE_SOURCE_INTEGRITY_OK`
- `A9_PRODUCTION_SAFETY_BLOCKED_OK`
- `A9_NO_PRODUCTION_MUTATION_OK`
- `A9_FOUNDATION_CHAIN_RELOADED_OK`
- `A9_FOUNDATION_E2E_OK`
- `A9_CLEANUP_OK`

A9 подтверждает:

- AI agent availability;
- Knowledge Snapshot creation;
- Snapshot → Hypothesis linkage;
- Hypothesis → Experiment linkage;
- Experiment → Strategy Version linkage;
- Validation Evidence creation and verification;
- Promotion audit linkage;
- trade-source integrity audit;
- production safety blocking;
- отсутствие production mutation;
- persistence/reload identity integrity;
- cleanup.

Следующий Foundation scope должен начинаться только после отдельного mapping следующего Master Plan item.

**Evidence:** `tests/aiea/test_a9_foundation_e2e.py`

**Test result:** `A9_FOUNDATION_E2E_OK`

**Note:** test emitted a non-fatal `DeprecationWarning` for `datetime.utcnow()`.

## 51.2. B.5 — News / Event Correlation

**Status:** `IN PROGRESS / RESEARCH-ONLY`

Продолжается:

- event → market;
- event → regime;
- event → strategy;
- event → outcome;
- evidence / linkage integrity.

B.5 не имеет production execution authority.

## 51.3. News & Event Intelligence

**Status:** `PARTIALLY VERIFIED`

Подтверждены:

- RSS/Atom external source adapter;
- canonical ingestion → persistence;
- deterministic deduplication;
- provider failure isolation;
- News/Event normalization/correlation;
- comparison context propagation.

Evidence:

- `B5_RSS_PROVIDER_E2E_OK`
- `B5_NEWS_INGESTION_E2E_OK`
- `B5_RSS_FAILURE_ISOLATION_E2E_OK`
- `B5_NEWS_CORRELATION_E2E_OK`

Открыты:

- historical backfill;
- event → market persistent linkage beyond comparison context;
- event → outcome lifecycle;
- news-aware validation;
- influence metrics;
- broader external source coverage if required.

Основная section: `43`.

## 51.4. Dynamic Market Universe

Открыты:

- full exchange universe discovery;
- complete filtering policy;
- spread/execution-quality checks;
- session policy;
- TOP-50 ranking;
- dynamic opportunity pool;
- end-to-end runtime integration.

Основная section: `44`.

## 51.5. Sandbox Security

Открыты:

- runtime isolation;
- resource limits;
- filesystem isolation;
- network isolation;
- secrets isolation;
- database isolation;
- Docker socket protection.

Основная section: `30`.

## 51.6. Application / Production Security

Открыты:

- secrets lifecycle;
- log redaction;
- full authorization matrix;
- dependency/supply-chain audit;
- container/network security;
- key rotation;
- incident response;
- application-wide regression testing.

Основная section: `46`.

## 51.7. Dedicated AI Live Controls

Открыты:

- dedicated AI risk budget;
- dedicated AI kill switch;
- Restricted Live limits;
- AI Live activation state machine;
- live degradation triggers.

Основные sections: `17`, `28`, `45`.

## 51.8. API

Открыты:

- complete AIEA API surface;
- API authorization matrix;
- HTTP-layer user isolation;
- complete mutation audit;
- dedicated kill-switch endpoint.

Основная section: `34`.

## 51.9. Dashboard

Открыты:

- complete AI Evolution UI;
- source-separated observability;
- validation UI;
- promotion/rollback UI;
- News/Event UI;
- Dynamic Universe UI;
- security/audit UI;
- dashboard-layer isolation.

Основные sections: `35`, `47`.

## 51.10. Strategy Generation / Modification

Открыты:

- autonomous Strategy Generator;
- autonomous Strategy Modifier;
- automatic Genome generation/mutation;
- generated-code sandbox lifecycle;
- automatic experiment creation;
- automatic validation orchestration;
- automatic retest/evaluation.

Основные sections: `24–26`, `37–38`.

## 51.11. Learning Loop

Открыты:

- cycle identity;
- lesson → modification feedback;
- automatic retest;
- full autonomous learning cycle;
- News/Event-aware learning.

Основная section: `22`.

## 51.12. Audit completeness

Открыты:

- exhaustive AI action audit;
- complete model/prompt version population;
- universal immutability proof;
- application-wide audit coverage.

Основная section: `29`.

## 51.13. Metadata propagation

Открыты:

- full runtime `ai_experiment_id` propagation;
- full runtime `ai_decision_id` propagation;
- complete AI Live traceability.

Основная section: `32`.

## 51.14. Statistical / temporal hardening

Открыты:

- complete statistical sufficiency matrix;
- universal degradation policy;
- UTC/timezone hardening;
- cross-stage significance rules.

Основная section: `49`.

## 51.15. Important constraint

Наличие open items не означает failure проекта.

Они должны оставаться открытыми до получения соответствующего:

`FACT → CHECK → EVIDENCE → AUDIT → STATUS`

и не могут быть закрыты только наличием кода.

## 51.16. Production blockers

Критические operational blockers до любого AI live activation:

- dedicated AI risk budget;
- dedicated AI kill switch;
- complete Restricted Live controls;
- runtime sandbox security;
- complete live-stage promotion gates;
- full production security proof.

**Status:** `OPEN`

**Production safety:** Restricted Live and Full Live remain disabled.

## 51.17. Production Protection Regression — 2026-08-28

### FACT

В период `2026-08-28 12:29:30–12:32:07 UTC` позиции `7131–7141` были успешно открыты, но остались без активных SL/TP на BingX.

### CHECK

Проверена цепочка:

`ExecutionAgent → set_stop_loss_take_profit() → BingX → Protection Fail-Safe → Emergency Close → PositionAgent Recovery`

Также проверена временная граница изменения `clients/bingx.py`.

### EVIDENCE

1. Protection patch изменил BingX SL/TP payload:

`quantity` был удалён и заменён на `closePosition=true`.

2. BingX для новых protection requests возвращал:

`109400 — parameter quantity or stopPrice is must`

3. `ExecutionAgent` корректно обнаруживал protection failure:

`[PROTECTION_FAILSAFE] ... closing unprotected position`

4. Emergency close через Hedge Mode передавал `reduceOnly=true`, и BingX возвращал:

`In the Hedge mode, the 'ReduceOnly' field can not be filled.`

5. После этого позиции оставались OPEN и переходили в `PROTECTION_RECOVERY`.

6. Recovery повторял невалидные protection requests, после чего BingX начал возвращать `109429` как следствие повторных `109400`.

7. Production contract smoke test после исправления пройден:

- `SL_CONTRACT_OK`
- `TP_CONTRACT_OK`
- `HEDGE_CLOSE_CONTRACT_OK`
- `PROTECTION_CONTRACT_SMOKE_OK`
- `PROTECTION_PATCH_COMPILE_OK`

### AUDIT

Доказано, что текущая авария была вызвана регрессией в protection/close contract, а не SMC strategy logic.

Исправления:

- SL/TP снова передают `quantity`;
- `closePosition=true` удалён из protection path;
- Hedge Mode emergency close переведён на `reduce_only=False`;
- `ExecutionAgent` больше не требует `closePosition=true` при protection verification.

### STATUS

`RUNTIME_VALIDATED_ON_BINGX_DEMO / PARTIAL_RECOVERY`


### RUNTIME EVIDENCE

Controlled runtime validation for existing `SOLUSDT #7131` completed successfully:

- BEFORE: `0` active protection orders on BingX;
- POST `STOP_MARKET`: BingX `code=0`, `status=NEW`, `quantity=22.93`;
- POST `TAKE_PROFIT_MARKET`: BingX `code=0`, `status=NEW`, `quantity=22.93`;
- AFTER: `2` active protection orders confirmed via `GET openOrders`;
- no bot trading cycle was enabled (`is_running=false`).

Current known state:

`BingX protection = VALID`

`DB protection order IDs = NOT YET SYNCHRONIZED`

### GAP

Не выполнен post-fix runtime validation на новой тестовой позиции с фактическим подтверждением:

`OPEN → SL ACTIVE → TP ACTIVE → CLOSE`

Необходимо также отдельно подтвердить emergency-close path реальным exchange response.

### NEXT STEP

До запуска production trading:

1. выполнить статический scan всех protection/close paths;
2. выполнить controlled runtime validation на BingX Demo;
3. подтвердить `PROTECTION_OK` и отсутствие `109400/109429`;
4. только после этого рассматривать восстановление обычного запуска.


## 52. NEXT STEP

**Status:** `VERIFIED`

### 52.1. Current completed state

**A9 — Foundation / Isolation**

Status:

`TEST VERIFIED / DONE`

Runtime evidence:

- `A9_FOUNDATION_E2E_OK`

**B.5 — News / Event Correlation**

Status:

`TEST VERIFIED / DONE`

Runtime evidence:

- `B5_NEWS_INGESTION_E2E_OK`
- `B5_RSS_FAILURE_ISOLATION_E2E_OK`
- `B5_NEWS_CORRELATION_E2E_OK`

A9 and B.5 are no longer active implementation items.

### 52.2. Production constraint

Current production safety state remains unchanged:

- Strategy Decision Engine = `SHADOW-ONLY`;
- Advisory = `OBSERVE_ONLY`;
- Restricted Live = `DISABLED`;
- Full Live = `DISABLED`;
- AI direct exchange access = `BLOCKED`;
- AIEA cannot bypass RiskAgent;
- AIEA cannot bypass ExecutionAgent.

### 52.3. Work-selection rule

No previously completed A9 or B.5 scope may be repeated without a new technical reason.

The next implementation item must be selected exclusively from unresolved items already recorded in `NEXUS_PROJECT_AUDIT.md`.

Before implementation:

`FACT → CHECK → EVIDENCE → AUDIT → STATUS → NEXT STEP`

### 52.4. Single primary next step

**PRIMARY NEXT STEP: factual mapping of the next uncompleted item in `NEXUS_PROJECT_AUDIT.md`.**

No implementation change is authorized until that item is identified from the live Audit and its existing code/tests/evidence are checked.

### 52.5. Canonical working point

`ONE PROJECT → ONE LIVE AUDIT → ONE CURRENT STATE → ONE NEXT STEP`

**A9: TEST VERIFIED / DONE**

**B.5: TEST VERIFIED / DONE**

**PRIMARY NEXT STEP: NEXT UNCOMPLETED AUDIT ITEM — FACTUAL MAPPING**

**PRODUCTION: SAFE / LIVE AI DISABLED**

## 51.18. Protection Regression Final Closeout — 2026-08-28

### FACT

Protection regression was reproduced, root-caused, corrected, and runtime-validated on BingX Demo.

Affected stale positions were handled explicitly:
- 1 position recovered with valid SL/TP;
- 3 additional positions recovered with valid SL/TP;
- 7 stale positions were closed via controlled market close.

### CHECK

Final reconciliation performed across:
- PostgreSQL OPEN positions;
- DB protection order IDs;
- live BingX positions;
- bot_settings.is_running.

### EVIDENCE

- corrected quantity-based SL/TP contract accepted by BingX with `code=0`;
- active SL/TP confirmed through `GET openOrders`;
- Hedge Mode market close succeeded with `reduce_only=False`;
- stale positions closed with exchange status `FILLED`;
- production trading remained disabled during recovery.

### AUDIT

The regression was caused by incompatible protection/close parameter changes:
- `quantity` was incorrectly replaced by `closePosition=true`;
- Hedge Mode close incorrectly used `reduceOnly=true`.

Both regressions were removed.

### STATUS

`PROTECTION_REGRESSION_FIXED_AND_RUNTIME_VALIDATED`

### GAP

Final DB ↔ BingX reconciliation must confirm zero unprotected regular OPEN positions.

GRID protection remains a separate policy and is not treated as a regular protection regression.

### NEXT STEP

Resume work from the canonical project plan only after final reconciliation.

Production trading remains disabled for this session.

## 51.19. B.5 News/Event Ingestion E2E — 2026-08-29

### FACT

B.5 News/Event ingestion path реализован и проверен end-to-end на deterministic research-only provider.

Цепочка:

`StaticTestNewsProvider → AINewsIngestionAdapter → AINewsEventService → PostgreSQL ai_news_events`

### CHECK

Проверено:

- provider item construction;
- provider → ingestion adapter conversion;
- canonical event creation;
- persistence в `ai_news_events`;
- повторное чтение persisted event;
- сохранение ключевых event fields;
- отсутствие production execution path.

### EVIDENCE

E2E test:

`tests/aiea/test_b5_news_ingestion_e2e.py`

Runtime evidence:

- `B5_PROVIDER_ITEM_OK`
- `B5_INGEST_COUNT_OK`
- `B5_EVENT_PERSISTED_OK`
- `B5_EVENT_FIELDS_OK`
- `B5_NEWS_INGESTION_E2E_OK`

### AUDIT

Подтвержден фактический ingestion → persistence lifecycle для canonical News/Event model.

Это закрывает техническую часть базового ingestion lifecycle для deterministic provider.

Это **не** подтверждает наличие production-grade external source adapters, historical backfill, deduplication или complete event correlation.

### STATUS

`TEST VERIFIED`

### GAP

Остаются:

- external source adapters;
- historical event backfill;
- deduplication;
- event → market persistent linkage;
- event → outcome linkage;
- event-aware validation;
- News/Event influence metrics.

### NEXT STEP

Следующий B.5 implementation step:

`43.6 External source adapters`

Требуется factual audit существующих provider integrations и, при отсутствии production-ready adapter, создание research-only adapter contract без execution authority.


## B5 — News / Event Correlation — COMPLETED

### FACT
B5 реализует изолированный News/Event аналитический контур для AIEA:
- RSS/news provider failure isolation;
- canonical News Event ingestion;
- deterministic normalization/deduplication;
- symbol/global market-scope correlation;
- impact classification;
- propagation of News/Event context into immutable comparison records.

Production-контур News/Event не имеет торговых side effects и не вызывает RiskAgent, ExecutionAgent или размещение ордеров.

### CHECK
1. RSS HTTP failure does not terminate ingestion of healthy feeds.
2. Malformed XML is isolated and does not terminate healthy feeds.
3. All-feed failure is handled safely.
4. Repeated failure remains deterministic and safe.
5. News/Event context validates required fields and impact score.
6. Event data is normalized deterministically.
7. Symbol-specific correlation works.
8. Global/CRYPTO scope correlation works for crypto symbols.
9. News context attaches only to affected comparison symbols.
10. News metadata propagates into the comparison record.
11. Existing comparison record remains immutable.
12. Impact classification works for HIGH / MEDIUM / LOW.
13. Symbol isolation works for symbol-specific events.

### EVIDENCE

#### B5 RSS Failure Isolation
Validated E2E test:
`tests/aiea/test_b5_rss_failure_path.py`

Evidence:
- `B5_RSS_FAILURE_TEST_FINAL_FIX_OK`
- `B5_RSS_HTTP_FAILURE_ISOLATED_OK`
- `B5_RSS_HEALTHY_FEED_SURVIVES_HTTP_FAILURE_OK`
- `B5_RSS_MALFORMED_XML_ISOLATED_OK`
- `B5_RSS_HEALTHY_FEED_SURVIVES_XML_FAILURE_OK`
- `B5_RSS_ALL_FEEDS_FAILURE_SAFE_OK`
- `B5_RSS_BAD_XML_ONLY_SAFE_OK`
- `B5_RSS_REPEAT_FAILURE_SAFE_OK`
- `B5_RSS_FAILURE_ISOLATION_E2E_OK`

#### B5 News/Event Correlation
Validated E2E test:
`tests/aiea/test_b5_news_correlation_e2e.py`

Evidence:
- `B5_CORRELATION_CONTEXT_VALID_OK`
- `B5_CORRELATION_NORMALIZATION_OK`
- `B5_CORRELATION_SYMBOL_MATCH_OK`
- `B5_CORRELATION_GLOBAL_SCOPE_OK`
- `B5_CORRELATION_ATTACH_OK`
- `B5_CORRELATION_METADATA_PROPAGATION_OK`
- `B5_CORRELATION_CONTEXT_PRESENT_OK`
- `B5_CORRELATION_IMPACT_CLASSIFICATION_OK`
- `B5_CORRELATION_SYMBOL_ISOLATION_OK`
- `B5_CORRELATION_IMMUTABILITY_OK`
- `B5_NEWS_CORRELATION_E2E_OK`

### STATUS
**B5 — COMPLETED / E2E VALIDATED**

RSS failure isolation and News/Event correlation are both positively validated.

No production trading permission was changed.
No Strategy Decision Engine promotion occurred.
No RiskAgent/ExecutionAgent integration was introduced by this validation.

### GAP
The validated B5 scope proves the analytical News/Event context and its failure-safe ingestion/correlation behavior.

Remaining work, if required by the canonical Master Plan, is limited to broader integration/coverage of News/Event evidence with downstream AIEA research/validation analytics. This must not introduce direct trading authority.

### NEXT STEP
Proceed to the next uncompleted item in the canonical `NEXUS_MASTER_PLAN.md`.

Before implementing the next item:
1. identify the exact Master Plan section;
2. inspect existing production implementation;
3. identify existing tests/evidence;
4. avoid duplicating already validated B5 functionality;
5. record the next FACT → CHECK → EVIDENCE → STATUS → GAP → NEXT STEP cycle in this audit.


---
### Блок A9: Foundation E2E
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-29 10:54
- **Evidence Tag**: A9_FOUNDATION_E2E_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python tests/aiea/test_a9_foundation_e2e.py
- **Result**: All 12/12 foundation checks passed. Production safety isolation confirmed.

---
### Блок B.5: News / Event Correlation
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 09:00
- **Evidence Tag**: B5_NEWS_EVENT_CORRELATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_ai_news_ingestion.py -v
- **Result**: All 3/3 news ingestion and correlation domain checks passed. Duplicate event isolation confirmed.

---
### Execution Boundary: Force Reduce-Only Verification
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:04
- **Evidence Tag**: EXECUTION_BOUNDARY_REDUCE_ONLY_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/ -v
- **Result**: All 10/10 unit tests passed. Enforced reduce_only=True on close_position verified.

---
### Execution Boundary: Force Reduce-Only Verification
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:07
- **Evidence Tag**: EXECUTION_BOUNDARY_REDUCE_ONLY_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/ -v
- **Result**: All 10/10 unit tests passed. Enforced reduce_only=True on close_position verified.

---
### Execution Boundary: Force Reduce-Only Verification
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:36
- **Evidence Tag**: EXECUTION_BOUNDARY_REDUCE_ONLY_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/ -v
- **Result**: All 10/10 unit tests passed. Enforced reduce_only=True on close_position verified.

---
### Block B.5: News Ingestion and Event Correlation
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:38
- **Evidence Tag**: B5_NEWS_INGESTION_CORRELATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_ai_news_ingestion.py -v
- **Result**: All 3/3 news ingestion and domain correlation tests passed.

---
### Block C: Strategy Generation & Candidate Pipeline
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:44
- **Evidence Tag**: C_STRATEGY_GENERATION_CANDIDATES_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/aiea/test_c1_candidate_generator.py -v
- **Result**: CandidateGenerator and CandidateScorer verified without side-effects.

---
### Block C: Strategy Generation & Candidate Pipeline (Re-verified)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:45
- **Evidence Tag**: C_STRATEGY_GENERATION_CANDIDATES_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_c1_candidate_generator.py -v
- **Result**: CandidateGenerator and CandidateScorer unit tests passed 2/2.

---
### Stage 1: Static Validation (Block D)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:49
- **Evidence Tag**: D1_STATIC_VALIDATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_d1_static_validation.py -v
- **Result**: Forbidden keywords and static validator integrity verified.

---
### Stage 3: Out-of-Sample / Walk-Forward Validation (Block D)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:52
- **Evidence Tag**: D3_OUT_OF_SAMPLE_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_d3_out_of_sample.py -v
- **Result**: AIWalkForwardValidator and AIShadowWalkForwardValidator structure verified.

---
### Stage 4: Walk-Forward & Shadow Evaluation (Block D)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:53
- **Evidence Tag**: D4_WALK_FORWARD_PAPER_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_d4_walk_forward_paper.py -v
- **Result**: Walk-forward, paper evaluation, quality, and stability services verified.

---
### Stage 5: Paper Trading Validation (Block D)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:55
- **Evidence Tag**: D5_PAPER_VALIDATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_d5_paper_validation.py -v
- **Result**: AIPaperTradingService and AIPaperResultAggregationService structure verified.

---
### Блок D / Общий тест репозитория
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 10:55
- **Evidence Tag**: FULL_SUITE_10_PASSED_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/ -v
- **Result**: All 10 core validation and execution tests passed successfully.

---
### Блок B.5: News & Event Ingestion
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 11:00
- **Evidence Tag**: B5_NEWS_INGESTION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_ai_news_ingestion.py -v
- **Result**: All 3 news ingestion and duplicate-handling tests passed successfully.

---
### AI Governance & Core Modules (Sections 16-22)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 11:22
- **Evidence Tag**: AI_GOVERNANCE_MODULES_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_f_ai_governance.py -v
- **Result**: Core AI services presence verified successfully.

---
### Comparison Engine & Contract (Block 23)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 11:25
- **Evidence Tag**: AI_COMPARISON_CONTRACT_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_ai_comparison_contract.py -v
- **Result**: All 7 comparison contract and validation tests passed successfully.

---
### Comparison Engine Complete Integration (Section 23)
- **Status**: TEST VERIFIED / DONE
- **Date**: 2026-08-30 11:31
- **Evidence Tag**: AI_COMPARISON_INTEGRATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/test_ai_comparison_integration.py -v
- **Result**: All 9 core comparison submodules and classes verified successfully.

---
### AI Discovery & Hypothesis Engine Complete (Section 24)
- **Status**: VERIFIED / DONE
- **Date**: 2026-08-30 11:35
- **Evidence Tag**: B2_AI_DISCOVERY_HYPOTHESIS_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python tests/aiea/test_b2_hypothesis_research.py
- **Result**: All checks passed (Regime contrast, structure, validation, no-strategy mutation, research e2e).

---
### AI-Generated Strategies & Evaluation Complete (Section 25)
- **Status**: VERIFIED / DONE
- **Date**: 2026-08-30 11:37
- **Evidence Tag**: B3_STRATEGY_EVALUATION_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python tests/aiea/test_b3_strategy_evaluation.py
- **Result**: All checks passed (Canonical metrics, version source binding, required slices, research-only mode, strategy evaluation).

---
### Strategy Modifications & AI Memory Complete (Section 26)
- **Status**: VERIFIED / DONE
- **Date**: 2026-08-30 11:41
- **Evidence Tag**: B4_RESEARCH_MEMORY_ONLY_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python tests/aiea/test_b4_ai_memory.py
- **Result**: All checks passed (Agent, lesson record, user memory isolation, experiment ownership, append-only memory, research memory only, cleanup).

---
### Candidate Generator & Scorer Complete (Block C)
- **Status**: VERIFIED / DONE
- **Date**: 2026-08-30 12:33
- **Evidence Tag**: C1_CANDIDATE_GENERATOR_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python -m pytest tests/aiea/test_c1_candidate_generator.py -v
- **Result**: All checks passed (Candidate generator structure, candidate scorer initialization).

---
### Foundation E2E Complete (Block A9)
- **Status**: VERIFIED / DONE
- **Date**: 2026-08-30 12:50
- **Evidence Tag**: A9_FOUNDATION_E2E_OK
- **Command**: docker compose exec -e PYTHONPATH=/app app python tests/aiea/test_a9_foundation_e2e.py
- **Result**: All checks passed (Agent, snapshot, hypothesis, experiment, validation evidence, promotion audit, trade source integrity, production safety blocked, no production mutation, chain reloaded, cleanup).

## 43.8.1. Historical News Source Architecture Decision — 2026-08-30

**Decision:** APPROVED

Canonical historical News/Event source:

`Event Registry API`

Role:

`RESEARCH-ONLY historical backfill source`

Allowed path:

`Event Registry → HistoricalNewsProvider → AINewsIngestionAdapter → AINewsEvent → research / comparison`

Forbidden boundaries:

- no RiskAgent bypass;
- no direct ExecutionAgent access;
- no exchange execution;
- no live permissions;
- no production risk mutation.

Existing `AINewsProvider` / `AINewsIngestionAdapter` architecture remains canonical.

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

**Evidence:** explicit user architecture approval on 2026-08-30.


### 43.8.2. Event Registry HistoricalNewsProvider — 2026-08-30

**Status:** `TEST VERIFIED / PARTIAL IMPLEMENTATION`

Implemented:

- `services/ai_news_event_registry_provider.py`
- `HistoricalNewsProvider(AINewsProvider)`
- Event Registry article → `AINewsProviderItem` mapping
- deterministic `event_id`
- `since / until / symbols / limit`
- research-only provider boundary

Evidence:

- `EVENT_REGISTRY_PROVIDER_COMPILE_OK`
- `EVENT_REGISTRY_PROVIDER_CONTAINER_OK`
- `EVENT_REGISTRY_MAPPING_OK`
- `EVENT_REGISTRY_DETERMINISTIC_ID_OK`
- `EVENT_REGISTRY_RESEARCH_PROVIDER_OK`
- `EVENT_REGISTRY_MOCK_FETCH_OK`
- `2 passed`

Not yet verified:

- multi-page pagination;
- full historical range traversal;
- checkpoint / resume;
- real Event Registry API integration;
- historical backfill E2E.


### 43.8.3. Event Registry Pagination — 2026-08-30

**Status:** `TEST VERIFIED`

Verified:

- multi-page Event Registry article retrieval;
- `articlesPage` traversal;
- aggregation across pages;
- stop at final reported page;
- provider mapping preserved across pagination.

Evidence:

- `EVENT_REGISTRY_PAGINATION_WRITE_OK`
- `EVENT_REGISTRY_PAGINATION_COMPILE_OK`
- `EVENT_REGISTRY_PAGINATION_TWO_PAGE_OK`
- `3 passed`

Remaining for full Historical Event Backfill:

- full historical range traversal across time windows;
- checkpoint / resume;
- real Event Registry API integration;
- historical backfill E2E.


### 43.8.4. Historical Backfill Window Traversal — 2026-08-30

**Status:** `TEST VERIFIED`

Implemented:

- `services/ai_news_historical_backfill_service.py`
- bounded historical date-range traversal;
- configurable `window_days`;
- final partial-window handling;
- reuse of canonical `AINewsIngestionAdapter`;
- research-only orchestration boundary.

Evidence:

- `NEWS_HISTORICAL_BACKFILL_COMPILE_OK`
- `NEWS_HISTORICAL_BACKFILL_WINDOWS_OK`
- `1 passed`

Verified example:

`2026-08-01 → 2026-08-08 → 2026-08-15 → 2026-08-16`

Remaining for full Historical Event Backfill:

- checkpoint / resume;
- real Event Registry API integration;
- historical backfill E2E against external source.


### 43.8.5. Historical Backfill Checkpoint Audit — 2026-08-30

**Status:** `NOT IMPLEMENTED / FACTUALLY VERIFIED`

Проведён поиск persistent checkpoint/resume mechanisms в:

- `models/`
- `services/`
- `migrations/`
- `tests/`

Existing reusable patterns для:

- checkpoint;
- resume;
- persistent cursor;
- processed-until watermark;
- high-water mark;
- progress state

не обнаружены.

Следовательно, текущий `HistoricalNewsBackfillService` после process restart не имеет persistent state для продолжения с последнего успешно завершённого historical window.

**Evidence:** repository-wide checkpoint/resume search returned no matches.

**Next required capability:** dedicated RESEARCH-ONLY persistent backfill checkpoint state.


### 43.8.6. Historical Backfill Persistent Job Architecture — 2026-08-30

**Decision:** `APPROVED`

Canonical persistent entity:

`AIHistoricalNewsBackfillJob`

Role:

`RESEARCH-ONLY historical News/Event backfill job state`

Core fields:

- id;
- user_id;
- job_key;
- provider;
- provider_version;
- source_config_hash;
- symbols;
- market_scope;
- requested_start;
- requested_end;
- window_days;
- limit_per_window;
- processed_until;
- current_window_start;
- current_window_end;
- current_page;
- resume_token;
- windows_completed;
- items_fetched;
- items_persisted;
- duplicates_skipped;
- status;
- attempt_count;
- max_attempts;
- retry_after;
- last_error_code;
- last_error_message;
- scope_hash;
- checkpoint_version;
- metadata;
- created_at;
- updated_at;
- started_at;
- last_progress_at;
- completed_at;
- failed_at.

Canonical statuses:

- `CREATED`
- `RUNNING`
- `PAUSED`
- `RETRY_PENDING`
- `FAILED`
- `COMPLETED`
- `CANCELLED`

Canonical resume semantics:

1. `processed_until` advances only after a historical window is successfully completed.
2. `current_page` / `resume_token` may track progress inside the current window.
3. If an in-progress window fails, `processed_until` must not advance.
4. Safe fallback after restart is replay of the incomplete window.
5. Existing News/Event deduplication remains the idempotency protection for replay.
6. `scope_hash` prevents resuming a job with a materially different requested scope/configuration.
7. Terminal `COMPLETED` state must not silently resume as a new job.

Allowed path:

`AIHistoricalNewsBackfillJob`
→ `HistoricalNewsBackfillService`
→ `HistoricalNewsProvider`
→ `AINewsIngestionAdapter`
→ `AINewsEvent`
→ research / comparison

Forbidden:

- no RiskAgent bypass;
- no ExecutionAgent access;
- no direct exchange access;
- no live permission mutation;
- no production risk mutation.

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

**Evidence:** explicit user architecture approval on 2026-08-30.


### 43.8.7. Alembic Branch Conflict Root Cause — 2026-08-30

**Status:** `FACTUALLY VERIFIED / RECONCILIATION NOT IMPLEMENTED`

Alembic has two heads:

- `d41e7c92b5f0`
- `b5f1e2d3c4a5`

Branch structure:

`b9bcf06be00e`
→ `c2d8e4f1a607`
→ `d41e7c92b5f0`

and separately:

`b9bcf06be00e`
→ `b5f1e2d3c4a5`

Runtime PostgreSQL schema for `ai_news_events` matches the
`c2d8e4f1a607 -> d41e7c92b5f0` branch.

Evidence:

- `source` is `varchar(120)`;
- `title` is `text`;
- `metadata` exists;
- `summary` exists;
- `raw_payload` exists;
- `normalized_payload` exists;
- `event_id` is unique.

Therefore `b5f1e2d3c4a5` is a duplicate/alternate historical branch
and must not be executed against the current database because it would
attempt to recreate `ai_news_events`.

No Alembic merge/stamp/rewrite has been performed.


### 43.8.8. Alembic Branch Reconciliation — 2026-08-30

**Status:** `TEST VERIFIED / DONE`

Duplicate B5 News/Event Alembic branch was reconciled without executing
the duplicate `ai_news_events` DDL.

Previous heads:

- `d41e7c92b5f0`
- `b5f1e2d3c4a5`

Verified runtime DB schema matched canonical branch:

`b9bcf06be00e`
→ `c2d8e4f1a607`
→ `d41e7c92b5f0`

Reconciliation:

1. Created empty merge revision:
   `448779a2137c`
2. Merge parents:
   - `d41e7c92b5f0`
   - `b5f1e2d3c4a5`
3. `upgrade()` and `downgrade()` contain no DDL.
4. Duplicate branch revision was marked metadata-only in `alembic_version`.
5. Empty merge revision was applied.

Final Alembic state:

- `alembic current` → `448779a2137c (head) (mergepoint)`
- `alembic heads` → `448779a2137c (head)`

No duplicate `ai_news_events` migration DDL was executed.

Evidence tags:

- `ALEMBIC_DUPLICATE_BRANCH_ROOT_CAUSE_OK`
- `ALEMBIC_METADATA_RECONCILIATION_OK`
- `ALEMBIC_EMPTY_MERGE_OK`
- `ALEMBIC_SINGLE_HEAD_OK`


### 43.8.9. Historical News Backfill Persistent Job — 2026-08-30

**Status:** `TEST VERIFIED / DONE`

Implemented persistent RESEARCH-ONLY historical News/Event backfill job state:

`AIHistoricalNewsBackfillJob`

Table:

`ai_historical_news_backfill_jobs`

Verified capabilities:

- persistent job identity;
- user-scoped research state;
- provider/config identity;
- requested historical range;
- symbols / market scope;
- window configuration;
- `processed_until` checkpoint;
- current window state;
- provider page / resume token fields;
- lifecycle status;
- retry/failure state;
- progress counters;
- scope/config integrity hashes;
- checkpoint versioning;
- lifecycle timestamps;
- metadata JSONB mapping.

ORM reserved-name issue was discovered and corrected:

Python ORM attribute:

`job_metadata`

maps to PostgreSQL column:

`metadata`

Alembic history was preserved:

`448779a2137c`
→ `4ae2c29f0b1b` (applied empty migration)
→ `f81e68355381` (corrective table creation migration)

No applied migration history was rewritten.

PostgreSQL table existence, columns, defaults, indexes and unique constraints were verified.

Runtime ORM round-trip was verified inside a transaction and rolled back after validation.

Evidence:

- `HISTORICAL_BACKFILL_JOB_MODEL_COMPILE_OK`
- `HISTORICAL_BACKFILL_JOB_MODEL_CONTAINER_OK`
- `HISTORICAL_BACKFILL_JOB_METADATA_MAPPING_COMPILE_OK`
- `HISTORICAL_BACKFILL_JOB_MODEL_IMPORT_OK`
- `HISTORICAL_BACKFILL_CORRECTIVE_DDL_WRITE_OK`
- `HISTORICAL_BACKFILL_CORRECTIVE_CONTAINER_PARITY_OK`
- `HISTORICAL_BACKFILL_JOB_ORM_INSERT_OK`
- `HISTORICAL_BACKFILL_JOB_ORM_SELECT_OK`
- `HISTORICAL_BACKFILL_JOB_METADATA_MAPPING_OK`
- `HISTORICAL_BACKFILL_JOB_DEFAULTS_OK`
- `HISTORICAL_BACKFILL_JOB_ROLLBACK_OK`

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

No RiskAgent bypass, ExecutionAgent access, exchange access, or live permission mutation was introduced.


### 43.8.10. Historical Backfill Transaction Ownership — 2026-08-30

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

Canonical transaction owner for historical News/Event backfill:

`HistoricalNewsBackfillService`

Transaction boundary:

`ONE HISTORICAL WINDOW = ONE DATABASE TRANSACTION`

Canonical success flow:

`BEGIN`
→ set `current_window_start`
→ set `current_window_end`
→ ingest News/Event rows
→ update progress counters
→ set `processed_until = effective_end`
→ increment `windows_completed`
→ `COMMIT`

Canonical failure flow:

provider/ingestion/persistence failure
→ `ROLLBACK`
→ News/Event rows from failed window are not committed
→ `processed_until` does not advance
→ incomplete window is safe to replay after restart

Canonical resume rule:

`resume cursor = processed_until`

If `processed_until` is NULL:

`resume cursor = requested_start`

Atomicity invariant:

News/Event rows for a completed historical window and the corresponding
`processed_until` checkpoint advance must become durable together.

Forbidden state:

`processed_until` MUST NOT advance if the corresponding window's News/Event
rows are not durably persisted.

Failure/retry lifecycle state may be persisted after rollback in a separate
transaction, but it must not advance `processed_until`.

Existing `AINewsIngestionAdapter` and `AINewsEventService` remain non-owning
with respect to transaction commit:

- `AINewsEventService.create()` may flush;
- `AINewsIngestionAdapter.ingest()` may orchestrate ingestion;
- neither owns the historical backfill window commit boundary.

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

No RiskAgent, ExecutionAgent, exchange execution, or live permission path is introduced.


### 43.8.11. Structured News Ingestion Result Contract — 2026-08-30

**Status:** `TEST VERIFIED / DONE`

`AINewsIngestionAdapter.ingest()` now returns structured:

`AINewsIngestionResult`

Fields:

- `fetched`
- `persisted`
- `duplicates_skipped`

Canonical semantics:

- provider item observed → `fetched += 1`
- newly persisted News/Event row → `persisted += 1`
- duplicate `event_id` skipped → `duplicates_skipped += 1`

Verified invariant for current ingestion path:

`fetched = persisted + duplicates_skipped`

Transaction ownership remains unchanged:

- `AINewsEventService.create()` may `flush`;
- `AINewsIngestionAdapter.ingest()` does not commit;
- caller owns transaction boundary.

Regression evidence:

- historical backfill window traversal:
  `1 passed`
- `B5_PROVIDER_ITEM_OK`
- `B5_INGEST_COUNT_OK`
- `B5_EVENT_PERSISTED_OK`
- `B5_EVENT_FIELDS_OK`
- `B5_NEWS_INGESTION_E2E_OK`
- `B5_DEDUP_CLEAN_OK`
- `B5_DEDUP_FIRST_INGEST_OK`
- `B5_DEDUP_SINGLE_ROW_OK`
- `B5_DEDUP_SECOND_INGEST_NO_DUPLICATE_OK`
- `B5_DEDUP_UNIQUE_EVENT_ID_OK`

Container runtime import of `AINewsIngestionResult` was also verified.

Production safety boundaries remain unchanged.


### 43.8.12. Historical Backfill Persistent Lifecycle Verification — 2026-08-31

**Status:** `TEST VERIFIED / DONE`

This verification completes the implementation evidence for the transaction
architecture approved in section `43.8.10`.

Canonical runtime path verified:

`AIHistoricalNewsBackfillJob`
→ `HistoricalNewsBackfillService`
→ `AINewsIngestionAdapter`
→ `AINewsEvent`
→ persistent checkpoint/counters

Verified transaction invariant:

- one historical window = one database transaction;
- successful window commits News/Event writes, counters, and checkpoint together;
- `processed_until` advances only after successful window completion;
- failed window is rolled back;
- failed window does not advance `processed_until`;
- last successfully committed window remains the resume boundary;
- recoverable failure persists `RETRY_PENDING` in a separate transaction;
- `attempt_count` and error state are persisted after rollback.

Verified persistent counters:

- `windows_completed`
- `items_fetched`
- `items_persisted`
- `duplicates_skipped`

Runtime evidence:

- `NEWS_HISTORICAL_BACKFILL_PERSISTENT_SUCCESS_OK`
- `NEWS_HISTORICAL_BACKFILL_CHECKPOINT_ADVANCE_OK`
- `NEWS_HISTORICAL_BACKFILL_ROLLBACK_OK`
- `NEWS_HISTORICAL_BACKFILL_CHECKPOINT_NOT_ADVANCED_OK`
- `NEWS_HISTORICAL_BACKFILL_RETRY_STATE_OK`
- pytest result: `2 passed in 1.02s`

Test infrastructure note:

- async SQLAlchemy engine pool is disposed between pytest event loops;
- this prevents asyncpg pooled connections from being reused across different
  pytest event loops;
- this change is test isolation only and does not alter production behavior.

Known non-blocking technical debt:

- `datetime.utcnow()` currently emits Python 3.12 deprecation warnings;
- timezone-aware datetime migration is NOT part of this verification and has
  not been marked DONE.

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

No RiskAgent, ExecutionAgent, BingX execution, or live permission path is
introduced.

Evidence tag:

`HISTORICAL_BACKFILL_PERSISTENT_LIFECYCLE_E2E_OK`


### 43.8.13. Historical Backfill Restart/Resume Verification — 2026-08-31

**Status:** `TEST VERIFIED / DONE`

Persistent restart/resume behavior was verified with a new database session
and a new `HistoricalNewsBackfillService` instance.

Verified invariant:

- first successful window is committed;
- next window fails;
- failed window does not advance `processed_until`;
- a subsequent run reloads the persistent job from PostgreSQL;
- resume starts exactly from saved `processed_until`;
- already committed windows are not replayed;
- processing continues to `requested_end`;
- final job state becomes `COMPLETED`.

Runtime evidence:

- `NEWS_HISTORICAL_BACKFILL_PERSISTENT_SUCCESS_OK`
- `NEWS_HISTORICAL_BACKFILL_CHECKPOINT_ADVANCE_OK`
- `NEWS_HISTORICAL_BACKFILL_ROLLBACK_OK`
- `NEWS_HISTORICAL_BACKFILL_CHECKPOINT_NOT_ADVANCED_OK`
- `NEWS_HISTORICAL_BACKFILL_RETRY_STATE_OK`
- `NEWS_HISTORICAL_BACKFILL_RESTART_RESUME_OK`
- `NEWS_HISTORICAL_BACKFILL_NO_COMMITTED_WINDOW_REPLAY_OK`
- pytest result: `3 passed in 1.20s`

Known non-blocking technical debt:

- Python 3.12 emits `datetime.utcnow()` deprecation warnings;
- timezone-aware datetime migration remains NOT VERIFIED and is not part of
  this completion evidence.

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

No RiskAgent, ExecutionAgent, BingX execution, or live permission path is
introduced.

Evidence tag:

`HISTORICAL_BACKFILL_RESTART_RESUME_E2E_OK`


### 43.8.14. Event Registry Real API Integration Security Contract — 2026-08-31

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

Explicit architecture approval received for canonical RESEARCH-ONLY wiring:

`EVENT_REGISTRY_API_KEY`
→ `Settings`
→ `HistoricalNewsProvider factory`
→ `HistoricalNewsProvider`
→ `HistoricalNewsBackfillService`

Approved security boundaries:

- `EVENT_REGISTRY_API_KEY` is loaded only through canonical application
  configuration / environment handling;
- API secret must not be committed to git;
- API secret must not be written to Audit;
- API secret must not be printed or logged;
- provider factory is passive and must not start historical backfill;
- Event Registry provider remains HTTP read-only;
- Event Registry endpoint remains fixed in provider code;
- external payload is treated as untrusted data;
- no RiskAgent access;
- no ExecutionAgent access;
- no exchange-service / BingX execution access;
- no Restricted Live or Full Live permission path;
- historical backfill remains RESEARCH-ONLY.

Required implementation evidence:

- `EVENT_REGISTRY_SETTINGS_WIRING_OK`
- `EVENT_REGISTRY_FACTORY_FAIL_CLOSED_OK`
- `EVENT_REGISTRY_FACTORY_PROVIDER_OK`
- `EVENT_REGISTRY_SECRET_NOT_LOGGED_OK`
- `EVENT_REGISTRY_FIXED_ENDPOINT_OK`
- `EVENT_REGISTRY_NO_AUTO_START_OK`
- `EVENT_REGISTRY_NO_EXECUTION_IMPORT_PATH_OK`
- `EVENT_REGISTRY_RESEARCH_ONLY_BOUNDARY_OK`

Real Event Registry API smoke verification is a separate later step and must
not expose the API key in logs or evidence.

Production safety state remains unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED


### 43.8.15. Event Registry Config/Factory Security Verification — 2026-08-31

**Status:** `TEST VERIFIED / DONE`

Implemented and verified canonical RESEARCH-ONLY configuration wiring:

`EVENT_REGISTRY_API_KEY`
→ `Settings.event_registry_api_key`
→ `create_event_registry_historical_provider(...)`
→ `HistoricalNewsProvider`

Verified behavior:

- canonical application Settings owns environment loading;
- provider factory is passive;
- factory does not start historical backfill;
- missing/blank API key fails closed;
- provider construction succeeds with configured key;
- factory does not read environment directly;
- Event Registry endpoint remains fixed in provider code;
- provider/factory contain no execution/trading import path;
- no RiskAgent access;
- no ExecutionAgent access;
- no exchange-service / BingX execution access;
- Event Registry API key is not printed or logged by current provider/factory path.

Regression evidence:

- `EVENT_REGISTRY_MAPPING_OK`
- `EVENT_REGISTRY_DETERMINISTIC_ID_OK`
- `EVENT_REGISTRY_RESEARCH_PROVIDER_OK`
- `EVENT_REGISTRY_MOCK_FETCH_OK`
- `EVENT_REGISTRY_PAGINATION_TWO_PAGE_OK`
- `EVENT_REGISTRY_FACTORY_PROVIDER_OK`
- `EVENT_REGISTRY_FACTORY_FAIL_CLOSED_OK`
- `EVENT_REGISTRY_NO_EXECUTION_IMPORT_PATH_OK`
- `EVENT_REGISTRY_RESEARCH_ONLY_BOUNDARY_OK`
- `EVENT_REGISTRY_NO_AUTO_START_OK`
- `EVENT_REGISTRY_FIXED_ENDPOINT_OK`
- `EVENT_REGISTRY_SECRET_NOT_LOGGED_OK`
- pytest result: `7 passed in 1.39s`

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

Real Event Registry API integration is still NOT VERIFIED and requires a separate
smoke test with a real credential. The credential itself must not be exposed in
logs, tests, Audit, or terminal evidence.

Evidence tag:

`EVENT_REGISTRY_CONFIG_FACTORY_SECURITY_E2E_OK`


### 43.8.16. Event Registry Real API Credential Availability — 2026-08-31

**Status:** `BLOCKED / NOT VERIFIED`

Real Event Registry API smoke verification is currently blocked because
`EVENT_REGISTRY_API_KEY` is not available.

Verified state:

- `.env` is protected by `.gitignore`;
- Event Registry config/factory/security wiring is TEST VERIFIED;
- no real Event Registry API request has been executed;
- no credential value has been exposed in logs, Audit, or chat;
- real API integration must remain NOT VERIFIED until a valid credential is
  provisioned.

Production safety boundaries remain unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

Evidence tag:

`EVENT_REGISTRY_REAL_API_BLOCKED_NO_CREDENTIAL`


### 43.10. Whale / On-chain / Exchange Flow Intelligence Architecture — 2026-08-31

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

NEXUS requires a dedicated Whale / On-chain / Exchange Flow Intelligence
layer as a separate canonical market-intelligence capability.

This capability MUST NOT be merged into:

- News/Event Intelligence;
- Dynamic Market Universe / Opportunity Discovery;
- RiskAgent;
- ExecutionAgent.

Canonical responsibility:

`Whale / On-chain Sources`
→ `Normalization`
→ `WhaleFlowEvent`
→ `Correlation with Market State`
→ `Research / Validation`
→ `Market Context`

Primary analytical scope:

- large crypto transfers;
- exchange inflows;
- exchange outflows;
- wallet accumulation / distribution;
- stablecoin flows;
- known exchange / entity wallet context;
- whale concentration / movement;
- correlation with price / volume;
- correlation with open interest;
- correlation with funding;
- correlation with liquidations;
- temporal outcome analysis after whale-flow events.

Canonical principle:

A whale/on-chain event is an analytical feature and MUST NOT be treated as a
direct BUY / SELL instruction.

Example analytical chain:

`WhaleFlowEvent`
+ `Market State`
+ `Derivatives Context`
+ `News/Event Context`
→ `Research Evidence`
→ `Strategy Decision Context`

Production authority is explicitly forbidden for this layer.

The Whale / On-chain Intelligence layer:

- MUST remain RESEARCH-ONLY during implementation and validation;
- MUST NOT call RiskAgent directly;
- MUST NOT call ExecutionAgent directly;
- MUST NOT place exchange orders;
- MUST NOT change leverage;
- MUST NOT modify positions;
- MUST NOT enable Restricted Live;
- MUST NOT enable Full Live;
- MUST NOT provide AI direct exchange access.

Canonical production safety remains:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

Initial implementation requirements:

1. choose a free or openly accessible canonical data source;
2. define provider interface and normalized `WhaleFlowEvent` contract;
3. preserve deterministic event identity / deduplication;
4. support historical research where source data allows;
5. support realtime / near-realtime ingestion where source data allows;
6. correlate whale-flow events with market state and later outcomes;
7. validate signal usefulness statistically before any downstream strategy use;
8. fail closed on malformed / incomplete external data;
9. no direct execution or trading authority.

No external provider is approved yet.

No provider implementation is VERIFIED yet.

No whale/on-chain signal effectiveness claim is VERIFIED yet.

Evidence tag:

`WHALE_ONCHAIN_INTELLIGENCE_ARCHITECTURE_APPROVED`


### 43.10.1. Open-Source / GitHub Reference-First Engineering Policy — 2026-08-31

**Status:** `ARCHITECTURE / ENGINEERING POLICY APPROVED`

For every new NEXUS capability or significant subsystem, the canonical
engineering workflow MUST include a GitHub / open-source reference review
before implementation where relevant mature solutions exist.

Canonical workflow:

`New Capability`
→ `GitHub / Open-Source Research`
→ `Compare Candidate Implementations`
→ `License / Security / Maintenance Audit`
→ `Extract Proven Architectural Patterns`
→ `Adapt to NEXUS Boundaries`
→ `Implement Clean NEXUS-Native Version`
→ `Tests / Runtime Evidence`
→ `Audit`

Rules:

- do not copy external repositories blindly;
- do not import foreign architecture wholesale;
- prefer proven patterns over unnecessary reinvention;
- inspect project maintenance activity and maturity;
- inspect license compatibility before reuse;
- inspect dependencies and supply-chain risk;
- inspect security implications;
- preserve NEXUS canonical boundaries;
- preserve NEXUS data models and transaction ownership;
- preserve multi-user isolation;
- preserve fail-closed behavior;
- preserve production execution boundaries;
- external code or design does not become VERIFIED merely because it exists
  on GitHub;
- every adapted component requires independent NEXUS tests and evidence.

When multiple solutions exist, compare them against:

- architectural fit;
- data quality;
- reliability;
- performance;
- maintenance activity;
- test coverage;
- security model;
- license;
- dependency footprint;
- operational complexity;
- ability to operate with free/open data where required.

Current production safety remains unchanged:

- Strategy Decision Engine: SHADOW-ONLY
- Advisory: OBSERVE_ONLY
- Restricted Live: DISABLED
- Full Live: DISABLED
- AI direct exchange access: BLOCKED

Evidence tag:

`GITHUB_REFERENCE_FIRST_ENGINEERING_POLICY_APPROVED`


## 52. STRATEGY MODERNIZATION / GITHUB BENCHMARK

**Date:** 2026-08-31

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

### 52.1. Canonical objective

NEXUS Strategy Layer должен быть системно модернизирован на основе лучших
проверенных open-source / GitHub implementations и research patterns,
БЕЗ замены основной архитектуры NEXUS.

NEXUS не заменяется сторонним торговым framework.

GitHub / open-source используются как:

- architecture references;
- algorithm references;
- feature-engineering references;
- validation references;
- backtesting methodology references;
- reliability references.

Все полезные решения должны быть адаптированы как NEXUS-native components.

Canonical workflow:

`Current NEXUS Strategy`
→ `GitHub / Open-Source Research`
→ `Candidate Comparison`
→ `License / Security / Maintenance Review`
→ `Extract Proven Patterns`
→ `NEXUS-native Adaptation`
→ `Backtest`
→ `OOS`
→ `Walk-Forward`
→ `Shadow`
→ `Audit Evidence`

### 52.2. Current Strategy Registry scope

Текущий Strategy Registry содержит:

1. `trend_pullback`
2. `smc`
3. `ema_cross`
4. `scalping`
5. `bollinger_squeeze`
6. `mean_reversion`
7. `trend_following_chop`
8. `statistical_arbitrage`
9. `breakout`
10. `range_trading`
11. `liquidity_sweep`
12. `order_block`
13. `fair_value_gap`
14. `volume_profile`
15. `funding_oi`
16. `volatility_expansion`
17. `grid_combo`

Ни одна стратегия не удаляется автоматически.

### 52.3. Mandatory Strategy Benchmark Matrix

Для каждой стратегии необходимо сравнить:

`NEXUS current implementation`
vs
`best GitHub reference`
vs
`second-best relevant reference`

По единым критериям:

- signal logic;
- market structure;
- regime awareness;
- multi-timeframe support;
- volatility adaptation;
- volume confirmation;
- entry quality;
- stop-loss model;
- take-profit model;
- position-management logic;
- risk/reward;
- lookahead safety;
- repaint risk;
- overfitting risk;
- fees/slippage awareness;
- tests;
- maintainability;
- license;
- dependency footprint;
- runtime complexity;
- crypto perpetual suitability;
- NEXUS architectural compatibility.

Итоговый research status каждой стратегии:

- `KEEP`
- `IMPROVE`
- `MERGE INTO FAMILY`
- `REPLACE LOGIC`
- `RESEARCH ONLY`
- `REMOVE FROM DIRECT COMPETITION`

Эти статусы являются research recommendations и НЕ являются автоматически
разрешёнными production changes.

### 52.4. Strategy family research

Разрешено исследовать logical family organization:

#### SMC FAMILY

- SMC
- Liquidity
- Liquidity Sweep
- BOS / CHoCH
- Order Block
- Fair Value Gap
- market structure

#### TREND FAMILY

- EMA Cross
- Trend Pullback
- Breakout
- Trend Following / Chop
- Volatility Expansion

#### RANGE FAMILY

- Mean Reversion
- Range Trading
- Bollinger Squeeze
- Volume Profile

#### DERIVATIVES FAMILY

- Funding
- Open Interest

#### STATISTICAL FAMILY

- Statistical Arbitrage

#### GRID

Grid остаётся отдельным specialized contour и не должен автоматически
возвращаться в общий StrategyDecisionEngine.

Любое фактическое изменение family architecture требует отдельного
architecture approval после evidence.

### 52.5. Current SMC architecture finding

Фактически обнаружено:

- unified `SMCStrategy` существует;
- `SMCStrategy` зарегистрирована;
- SMC имеет отдельный DecisionEngine scorer;
- `liquidity_sweep`;
- `order_block`;
- `fair_value_gap`

одновременно существуют как independent strategy candidates.

Decision Engine выбирает highest-scoring eligible candidate.

В исследованной недавней trade sample unified `smc` не наблюдалась
как selected real-trade strategy, при этом отдельные SMC-derived strategies
участвовали в реальных сделках.

Требуется исследовать:

`SMC`
vs
`Liquidity Sweep / OB / FVG as independent strategies`

и проверить, должны ли отдельные SMC concepts стать evidence/features
внутри SMC family вместо прямой конкуренции.

**Status:** `ROOT-CAUSE CANDIDATE / NOT YET IMPLEMENTATION APPROVED`

### 52.6. SMC scoring review requirement

SMC evidence необходимо проверить как группы:

`Structure = BOS OR CHoCH`

`POI = Order Block OR FVG`

а не автоматически считать альтернативные события независимыми
обязательными confirmations.

Требуется factual comparison actual DecisionEngine scores до изменения кода.

### 52.7. Regime Detector review

Текущий Strategy-layer RegimeDetector использует:

- `TREND_UP`
- `TREND_DOWN`
- `SIDEWAYS`
- `VOLATILE`

Current implementation проверяет high volatility до trend classification.

Trading audit показал, что `VOLATILE` был наиболее убыточным regime
в исследованной recent sample.

Требуется GitHub/research comparison regime models, включая:

- ATR percentile;
- realized volatility;
- ADX / +DI / -DI;
- Choppiness;
- EMA structure;
- trend strength;
- directional regime × volatility regime.

Не менять RegimeDetector без отдельного evidence / architecture approval.

### 52.8. Current trading evidence

Recent real trade sample показал отрицательный aggregate result.

Особенно проблемными в исследованной выборке выглядели:

- `volatility_expansion`;
- `fair_value_gap`;
- `liquidity_sweep`;
- `order_block`;
- `trend_pullback`.

`mean_reversion` показал положительный результат в небольшой выборке,
но sample недостаточен для VERIFIED edge.

Также обнаружены observability gaps:

- commission values frequently `0`;
- funding values frequently `0`;
- `strategy_version` frequently empty;
- `ai_experiment_id` empty;
- `ai_decision_id` empty.

Эти gaps должны учитываться до серьёзных выводов о strategy edge.

### 52.9. Validation requirements

Ни одна модернизированная стратегия не считается улучшенной только
по historical total PnL.

Минимальный validation lifecycle:

`Unit Tests`
→ `Deterministic Backtest`
→ `Lookahead Safety`
→ `OOS`
→ `Walk-Forward`
→ `Regime / Symbol / Side Breakdown`
→ `Shadow`
→ `Comparison`
→ `Audit`

Минимальные metrics:

- trades;
- win rate;
- gross PnL;
- net PnL;
- profit factor;
- expectancy;
- average win;
- average loss;
- average R;
- max drawdown;
- consecutive losses;
- regime performance;
- symbol performance;
- LONG/SHORT performance;
- fees;
- funding;
- slippage.

Недостаточный sample:

`NOT VERIFIED`

### 52.10. GitHub / source safety

Для каждого reference фиксировать:

- repository;
- commit/tag where relevant;
- license;
- maintenance activity;
- test coverage;
- implementation language;
- dependencies;
- copied code: YES/NO;
- adapted concept: YES/NO.

Запрещено blindly copy external repositories.

License compatibility должна проверяться до переноса кода.

### 52.11. Production boundaries

Strategy modernization НЕ изменяет текущий production safety state:

- Strategy Decision Engine: `SHADOW-ONLY`
- Advisory: `OBSERVE_ONLY`
- Restricted Live: `DISABLED`
- Full Live: `DISABLED`
- AI direct exchange access: `BLOCKED`

Запрещено в рамках этого track:

- bypass RiskAgent;
- bypass ExecutionAgent;
- direct BingX execution;
- automatic live activation;
- automatic permission escalation.

### 52.12. First deliverable

Первый deliverable данного track:

`NEXUS_STRATEGY_GITHUB_BENCHMARK`

Он должен содержать все 17 стратегий и минимум:

| Strategy | Current NEXUS Logic | Best Reference | Second Reference | Main Gap | Proposed Status | Evidence |

Также:

- Top architectural findings;
- Highest-risk current strategies;
- Best GitHub-derived improvements;
- Strategies where NEXUS is already stronger;
- Validation gaps;
- ONE recommended first implementation target.

На этом этапе массовые strategy patches запрещены.

### 52.13. Implementation order

После benchmark выбрать только ОДИН первый implementation target по:

1. current loss contribution;
2. architectural impact;
3. quality of external reference;
4. objective validation feasibility;
5. regression risk.

После изменения:

`CHECK`
→ `CODE`
→ `TEST`
→ `BACKTEST`
→ `OOS / WALK-FORWARD`
→ `SHADOW`
→ `AUDIT`

### 52.14. Evidence tag

`STRATEGY_MODERNIZATION_GITHUB_BENCHMARK_ARCH_APPROVED`

### 52.15. Current status

**Status:** `ARCHITECTURE APPROVED / IMPLEMENTATION NOT VERIFIED`

No strategy modernization implementation is considered VERIFIED yet.

### 52.16. Primary next step

Create factual:

`NEXUS_STRATEGY_GITHUB_BENCHMARK`

for all 17 current StrategyRegistry strategies before any strategy code changes.


### 52.x. Statistical Arbitrage V2 — Statistical Runtime Foundation — 2026-08-31

#### FACT

For the approved Statistical Arbitrage modernization track, the current NEXUS runtime previously contained only NumPy/Pandas and did not contain the statistical libraries required for mature cointegration/stationarity analysis.

Canonical Docker dependency source:

- `requirements.txt`
- Docker service: `app`
- Runtime container: `nexus-app`
- Python: `3.12.14`

#### IMPLEMENTATION

Added pinned dependencies:

- `scipy==1.14.1`
- `statsmodels==0.14.4`

No additional Kalman/scikit-learn dependency was introduced.

#### EVIDENCE

Dependency edit scope was verified against the pre-change backup and contained only:

- `+scipy==1.14.1`
- `+statsmodels==0.14.4`

Docker application image rebuild completed successfully:

- `BUILD_RC=0`

Runtime versions verified:

- NumPy `1.26.4`
- Pandas `2.2.2`
- SciPy `1.14.1`
- statsmodels `0.14.4`

Required statistical primitives imported successfully:

- Engle-Granger (`coint`) — OK
- ADF (`adfuller`) — OK
- KPSS (`kpss`) — OK
- Johansen (`coint_johansen`) — OK

Post-rebuild application state:

- `nexus-app` — `running healthy`

Evidence tag:

`STAT_ARB_V2_STATISTICAL_RUNTIME_FOUNDATION_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage establishes the statistical runtime foundation only.

It does NOT yet implement:

- pair screening;
- cointegration policy;
- stationarity gating;
- half-life estimation;
- FDR correction;
- dynamic Kalman hedge ratio;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and test the first isolated Statistical Arbitrage V2 analytical core:

`cointegration + stationarity + half-life`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Cointegration / Stationarity Core — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 analytical package:

- `strategies/stat_arb/__init__.py`
- `strategies/stat_arb/diagnostics.py`
- `tests/test_stat_arb_v2_diagnostics.py`

Implemented analytical diagnostics:

- OLS hedge relation;
- residual spread construction;
- Engle-Granger cointegration test;
- ADF stationarity test;
- KPSS stationarity confirmation;
- mean-reversion half-life estimation;
- fail-closed input and statistical validation.

No integration with StrategyDecisionEngine, RiskAgent, ExecutionAgent, or live execution was introduced.

#### EVIDENCE

Compilation:

- core `py_compile` — PASS
- test file `py_compile` — PASS

Lint:

- `flake8 strategies/stat_arb` — PASS

Targeted deterministic tests:

- cointegrated synthetic pair — PASS
- independent random walks — PASS
- non-finite input fail-closed — PASS
- insufficient samples fail-closed — PASS
- constant series fail-closed — PASS

Pytest result:

- `5 passed`
- `PYTEST_RC=0`

Known non-failing observation:

- statsmodels KPSS may emit `InterpolationWarning` when the statistic lies outside its tabulated p-value range.
- This warning did not affect test correctness or fail-closed behavior.

Evidence tag:

`STAT_ARB_V2_COINTEGRATION_STATIONARITY_CORE_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- Johansen confirmation;
- multiple-pair screening;
- FDR correction;
- dynamic Kalman hedge ratio;
- causal entry/exit signals;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and test isolated StatArb V2 pair-screening layer:

`Johansen confirmation + multiple-testing FDR correction`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Johansen / FDR Screening — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 screening layer:

- `strategies/stat_arb/screening.py`
- `tests/test_stat_arb_v2_screening.py`

Implemented:

- Johansen cointegration confirmation;
- cointegration rank evaluation;
- fail-closed Johansen validation;
- Benjamini-Hochberg FDR correction across multiple hypotheses;
- order-preserving adjusted p-values;
- fail-closed invalid p-value / alpha handling.

No integration with StrategyDecisionEngine, RiskAgent, ExecutionAgent, or live execution was introduced.

#### EVIDENCE

Compilation:

- `py_compile` — PASS
- `COMPILE_RC=0`

Lint:

- `flake8 strategies/stat_arb/screening.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

- Johansen confirms synthetic cointegrated pair — PASS
- Johansen rejects independent random walks — PASS
- Johansen non-finite input fail-closed — PASS
- BH-FDR significant hypothesis selection — PASS
- BH-FDR order preservation — PASS
- BH-FDR invalid values fail-closed — PASS
- BH-FDR invalid alpha fail-closed — PASS

Pytest result:

- `7 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_JOHANSEN_FDR_SCREENING_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- dynamic Kalman hedge ratio;
- hedge-ratio stability controls;
- causal z-score signal generation;
- transaction cost model;
- circuit breakers;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and test isolated Statistical Arbitrage V2 dynamic hedge estimation:

`NumPy-native Kalman alpha/beta hedge ratio`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Dynamic Kalman Hedge Ratio — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 dynamic hedge estimation:

- `strategies/stat_arb/kalman.py`
- `tests/test_stat_arb_v2_kalman.py`

Implemented:

- NumPy-native two-state Kalman filter;
- dynamic intercept `alpha_t`;
- dynamic hedge ratio `beta_t`;
- causal sequential updates;
- residual calculation;
- innovation variance tracking;
- fail-closed validation for invalid inputs and covariance state.

No external Kalman dependency was introduced.

No integration with StrategyDecisionEngine, RiskAgent, ExecutionAgent, or live execution was introduced.

#### EVIDENCE

Compilation:

- `py_compile` — PASS
- `COMPILE_RC=0`

Lint:

- `flake8 strategies/stat_arb/kalman.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

- constant known beta recovery — PASS
- slowly changing beta tracking — PASS
- causal / no-lookahead prefix equivalence — PASS
- finite covariance/output path — PASS
- non-finite input fail-closed — PASS
- insufficient samples fail-closed — PASS
- invalid variance fail-closed — PASS

Pytest result:

- `7 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_DYNAMIC_KALMAN_HEDGE_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- hedge-ratio stability gating;
- causal rolling residual z-score signals;
- transaction cost model;
- circuit breakers;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and test isolated StatArb V2:

`hedge-ratio stability + causal residual z-score signal layer`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Hedge Stability / Causal Signal Layer — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 signal layer:

- `strategies/stat_arb/signals.py`
- `tests/test_stat_arb_v2_signals.py`

Implemented:

- causal hedge-ratio stability evaluation;
- rolling residual z-score using prior history only;
- deterministic pair signals:
  - `LONG_SPREAD`
  - `SHORT_SPREAD`
  - `EXIT`
  - `HOLD`
- unstable hedge relation gates trade candidates to `HOLD`;
- zero-variance residual history fails closed to `HOLD`;
- non-finite input fails closed.

No integration with StrategyDecisionEngine, RiskAgent, ExecutionAgent, or live execution was introduced.

#### EVIDENCE

Compilation:

- signal module / tests `py_compile` — PASS

Lint:

- `flake8 strategies/stat_arb/signals.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

- stable beta path accepted — PASS
- abrupt beta instability rejected — PASS
- z-score uses prior history only — PASS
- future shocks do not alter past signals — PASS
- deterministic entry / exit signals — PASS
- unstable beta gates valid z-score to HOLD — PASS
- zero-variance history fails closed to HOLD — PASS
- non-finite input fails closed — PASS

Pytest result:

- `8 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_CAUSAL_SIGNAL_STABILITY_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- transaction-cost model;
- funding / commission / slippage economics;
- circuit breakers;
- pair-level capital sizing;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and test isolated StatArb V2:

`transaction-cost model + circuit breaker`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Pair Economics / Local Guard — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 pair economics and local analytical guard:

- `strategies/stat_arb/economics.py`
- `strategies/stat_arb/guards.py`
- `tests/test_stat_arb_v2_economics.py`
- `tests/test_stat_arb_v2_guards.py`

Implemented pair economics using existing NEXUS cost conventions:

- one-side commission as decimal;
- adverse slippage in basis points;
- signed funding semantics:
  - positive rate: LONG pays / SHORT receives;
  - negative rate: SHORT pays / LONG receives;
- both pair legs included;
- unequal notionals supported;
- aggregated fees / slippage / funding / total pair cost.

Implemented local StatArb analytical guard:

- `MODEL_INVALID`
- `RELATION_BREAKDOWN`
- `HEDGE_UNSTABLE`
- `RESIDUAL_EXTREME`
- `COST_EXCEEDS_EDGE`
- incomplete / invalid economics fail-closed.

This guard is local to StatArb pair eligibility only.

It does NOT replace, bypass, or modify the canonical global execution kill-switch in `ExecutionBoundary`.

No integration with StrategyDecisionEngine, RiskAgent, ExecutionAgent, or live execution was introduced.

#### EVIDENCE

Lint:

- `flake8 economics.py guards.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

Pair economics:

- both legs / both trade sides cost aggregation — PASS
- positive funding LONG pays / SHORT receives — PASS
- negative funding LONG receives / SHORT pays — PASS
- unequal notionals preserve signed funding — PASS
- invalid input fail-closed — PASS

Local guard:

- valid pair allowed — PASS
- unstable hedge blocked — PASS
- relation breakdown blocked — PASS
- extreme residual blocked — PASS
- cost destroying expected edge blocked — PASS
- material edge over cost allowed — PASS
- incomplete economics fail-closed — PASS

Pytest result:

- `12 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_COSTS_LOCAL_GUARD_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- integrated StatArb V2 research pipeline;
- pair-level expected-edge estimator;
- orchestration across screening / diagnostics / Kalman / signals / economics / guards;
- StrategyDecisionEngine integration;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Assemble and test one isolated StatArb V2 research pipeline that composes the already verified components:

`screening -> diagnostics -> Kalman -> causal signals -> economics -> local guard`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Integrated Research Pipeline — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 research orchestration layer:

- `strategies/stat_arb/pipeline.py`
- `tests/test_stat_arb_v2_pipeline.py`

Pipeline composes already verified components:

- universe-level FDR screening result input;
- Johansen confirmation;
- Engle-Granger / ADF / KPSS / half-life diagnostics;
- dynamic Kalman hedge estimation;
- causal residual z-score and hedge stability;
- pair economics on actual entry candidates;
- local analytical guard.

Important architecture boundary:

BH-FDR remains a universe-level screening procedure.
The single-pair research pipeline consumes `fdr_selected` and does not incorrectly run FDR on one isolated pair.

No StrategyDecisionEngine, RiskAgent, ExecutionAgent, ExecutionBoundary, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/pipeline.py` — PASS
- `FLAKE8_RC=0`

Targeted integration tests:

- FDR-rejected pair rejected before downstream analysis — PASS
- non-cointegrated pair rejected — PASS
- valid pair reaches Johansen / diagnostics / Kalman / signal layer — PASS
- invalid input fails closed — PASS
- no entry candidate does not invoke economics / guard — PASS

Pytest result:

- `5 passed`
- `PYTEST_RC=0`

Observed warnings:

- 2 `statsmodels` KPSS `InterpolationWarning`
- non-failing;
- known statistical lookup-table boundary behavior;
- no test failure caused.

Evidence tag:

`STAT_ARB_V2_RESEARCH_PIPELINE_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- pair-level expected-edge estimator;
- hedge-ratio-based pair sizing;
- walk-forward / out-of-sample research validation of the complete V2 pipeline;
- legacy `statistical_arbitrage.py` replacement;
- StrategyDecisionEngine integration;
- pair-position execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Design and verify the next isolated StatArb V2 research capability before any strategy-engine integration.

Primary candidate:

`causal expected-edge estimator`

It must provide an economic edge estimate in the same quote-currency units used by pair economics and must be validated without future-data leakage.

### 52.x. Statistical Arbitrage V2 — Causal Expected-Edge Estimator — 2026-09-01

#### IMPLEMENTED

Added isolated causal expected-edge estimator:

- `strategies/stat_arb/edge.py`
- `tests/test_stat_arb_v2_edge.py`

Implemented:

- causal equilibrium using prior residual history only;
- OU / AR(1)-style half-life decay;
- expected spread convergence forecast;
- conversion from spread price units to quote-currency gross edge using leg-A quantity;
- hedge-ratio / pair-notional consistency validation;
- fail-closed handling for invalid beta, non-finite inputs, insufficient history, and invalid economics inputs.

Dimensional contract:

`spread convergence [price A] * quantity A = expected gross edge [quote currency]`

This matches the quote-currency units used by `PairCostResult.total_cost`.

No StrategyDecisionEngine, RiskAgent, ExecutionAgent, ExecutionBoundary, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/edge.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

- one half-life forecasts half convergence — PASS
- expected edge returned in quote currency — PASS
- default horizon equals one half-life — PASS
- equilibrium uses prior history only — PASS
- future values do not change prefix estimate — PASS
- hedge-notional mismatch fails closed — PASS
- non-positive beta fails closed — PASS
- non-finite input fails closed — PASS

Pytest result:

- `8 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_CAUSAL_EXPECTED_EDGE_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- integration of the estimator into the research pipeline;
- automatic hedge-ratio-based pair sizing;
- walk-forward / out-of-sample validation of complete StatArb V2;
- StrategyDecisionEngine integration;
- pair execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Integrate the verified causal expected-edge estimator into the isolated StatArb V2 research pipeline and verify that entry candidates are evaluated as:

`expected gross edge -> pair costs -> local guard`

without modifying DecisionEngine, RiskAgent, ExecutionAgent, or live execution boundaries.

### 52.x. Statistical Arbitrage V2 — Expected Edge Pipeline Integration — 2026-09-01

#### IMPLEMENTED

Integrated the verified causal expected-edge estimator into the isolated StatArb V2 research pipeline.

Updated:

- `strategies/stat_arb/pipeline.py`
- `tests/test_stat_arb_v2_pipeline.py`

The pipeline now evaluates entry candidates as:

`signal -> causal expected gross edge -> pair costs -> local analytical guard`

Changes include:

- external `expected_edge` pipeline input removed;
- `CausalEdgeResult` added to research result;
- expected gross edge derived from current Kalman residual / beta and diagnostics half-life;
- edge expressed in quote currency;
- edge-invalid / hedge-notional mismatch fails closed to `HOLD`;
- pair economics runs only after valid edge estimation;
- local guard receives `edge.expected_gross_edge`;
- excessive costs block entry with `COST_EXCEEDS_EDGE`.

No StrategyDecisionEngine, RiskAgent, ExecutionAgent, ExecutionBoundary, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/pipeline.py` — PASS
- `FLAKE8_RC=0`

Targeted integration tests:

- FDR-rejected pair rejected early — PASS
- non-cointegrated pair rejected — PASS
- valid pair reaches signal layer — PASS
- invalid input fails closed — PASS
- no entry candidate skips economics / guard — PASS
- valid entry runs edge -> costs -> guard and becomes eligible — PASS
- costs destroying edge produce `COST_EXCEEDS_EDGE` and `HOLD` — PASS
- hedge-notional mismatch produces `EDGE_INVALID` and `HOLD` — PASS

Pytest result:

- `8 passed`
- `PYTEST_RC=0`

Observed warnings:

- 5 `statsmodels` KPSS `InterpolationWarning`
- non-failing;
- known lookup-table boundary behavior;
- no test failure caused.

Evidence tag:

`STAT_ARB_V2_EDGE_PIPELINE_INTEGRATION_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- automatic hedge-ratio-based pair sizing;
- walk-forward / out-of-sample validation of the complete StatArb V2 pipeline;
- legacy `statistical_arbitrage.py` replacement;
- StrategyDecisionEngine integration;
- pair-position execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and verify isolated hedge-ratio-based pair sizing for StatArb V2 so that leg notionals are generated consistently from current Kalman beta rather than supplied manually.

No DecisionEngine / RiskAgent / ExecutionAgent / live integration.

### 52.x. Statistical Arbitrage V2 — Hedge-Ratio Pair Sizing — 2026-09-01

#### IMPLEMENTED

Added isolated hedge-ratio-based pair sizing:

- `strategies/stat_arb/sizing.py`
- `tests/test_stat_arb_v2_sizing.py`

Sizing contract for the current raw-price Kalman model:

`spread = A - alpha - beta * B`

Pair quantities satisfy:

`quantity_B = beta * quantity_A`

while total gross quote-currency exposure is constrained by:

`notional_A + notional_B = gross_notional`

Implemented sizing therefore generates both pair leg notionals from:

- current price A;
- current price B;
- current positive Kalman hedge ratio;
- requested gross pair notional.

No account balance lookup, risk-percent sizing, leverage sizing, exchange rounding, portfolio allocation, DecisionEngine, RiskAgent, ExecutionAgent, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/sizing.py` — PASS
- `FLAKE8_RC=0`

Targeted deterministic tests:

- quantity hedge ratio preserved — PASS
- exact gross-notional budget preserved — PASS
- edge-estimator notional contract matched — PASS
- sizing scales linearly with gross notional — PASS
- large raw-price beta preserves budget — PASS
- non-positive beta fails closed — PASS
- non-positive gross notional fails closed — PASS
- invalid price fails closed — PASS
- non-finite input fails closed — PASS

Pytest result:

- `9 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_HEDGE_RATIO_PAIR_SIZING_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- sizing integration into the research pipeline;
- walk-forward / out-of-sample validation;
- legacy statistical-arbitrage strategy replacement;
- StrategyDecisionEngine integration;
- pair-position execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Integrate verified hedge-ratio pair sizing into the isolated StatArb V2 research pipeline so that `notional_b` is generated from current Kalman beta instead of supplied manually.

No DecisionEngine / RiskAgent / ExecutionAgent / live integration.

### 52.x. Statistical Arbitrage V2 — Sizing Pipeline Integration — 2026-09-01

#### IMPLEMENTED

Integrated verified hedge-ratio-based pair sizing into the isolated StatArb V2 research pipeline.

Updated:

- `strategies/stat_arb/pipeline.py`
- `tests/test_stat_arb_v2_pipeline.py`

The pipeline now evaluates entry candidates as:

`signal -> current Kalman beta -> automatic pair sizing -> causal expected gross edge -> pair costs -> local analytical guard`

Changes include:

- removed manual `notional_a` / `notional_b` pipeline inputs;
- added `gross_notional` as the single pair capital budget input;
- added `PairSizingResult` to research output;
- leg notionals generated from current prices and current Kalman hedge ratio;
- edge estimator consumes generated sizing;
- pair economics consumes the same generated sizing;
- invalid sizing fails closed with `SIZING_INVALID`;
- edge / economics / guard are not executed after invalid sizing.

No DecisionEngine, RiskAgent, ExecutionAgent, ExecutionBoundary, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/pipeline.py` — PASS
- `FLAKE8_RC=0`

Targeted integration tests:

- FDR rejection — PASS
- non-cointegrated pair rejection — PASS
- valid pair reaches signal layer — PASS
- invalid input fails closed — PASS
- no-entry candidate skips economics / guard — PASS
- valid entry runs sizing -> edge -> costs -> guard — PASS
- excessive costs produce `COST_EXCEEDS_EDGE` and `HOLD` — PASS
- invalid gross notional produces `SIZING_INVALID` and `HOLD` — PASS

Pytest result:

- `8 passed`
- `PYTEST_RC=0`

Observed warnings:

- 5 `statsmodels` KPSS `InterpolationWarning`
- non-failing;
- known lookup-table boundary behavior.

Evidence tag:

`STAT_ARB_V2_SIZING_PIPELINE_INTEGRATION_OK`

#### STATUS

`TEST VERIFIED / DONE`

This stage does NOT yet implement:

- walk-forward / out-of-sample validation of complete StatArb V2;
- legacy `statistical_arbitrage.py` replacement;
- StrategyDecisionEngine integration;
- pair-position execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement and verify walk-forward / out-of-sample validation for the complete StatArb V2 research pipeline before any strategy-engine integration.

No DecisionEngine / RiskAgent / ExecutionAgent / live integration.

### 52.x. Statistical Arbitrage V2 — Walk-Forward / OOS Validation — 2026-09-01

#### IMPLEMENTED

Added isolated candle/pair-level walk-forward OOS research validation:

- `strategies/stat_arb/walk_forward.py`
- `tests/test_stat_arb_v2_walk_forward.py`

This validator is separate from existing:

- `AIWalkForwardValidator`
- `AIShadowWalkForwardValidator`

because those validate already-recorded TradeHistory / shadow outcomes and are not candle-level StatArb research simulators.

Implemented:

- rolling train/test folds;
- non-overlapping TEST windows;
- causal expanding TEST prefixes;
- no future-data access for prior OOS decisions;
- structural train validation;
- OOS valid-rate gating;
- per-fold action / block summaries;
- cross-fold pass-rate aggregation;
- fail-closed invalid input handling.

No realized PnL / Sharpe / profit-factor claims are made by this layer because the current StatArb V2 research pipeline does not yet implement a full entry-to-exit trade lifecycle simulator.

No DecisionEngine, RiskAgent, ExecutionAgent, ExecutionBoundary, or exchange integration was introduced.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/walk_forward.py` — PASS
- `FLAKE8_RC=0`

Targeted OOS tests:

- non-overlapping walk-forward test folds — PASS
- cointegrated pair produces causal OOS points — PASS
- future shock does not alter prior fold decisions — PASS
- non-cointegrated pair fails structural windows — PASS
- invalid input fails closed — PASS

Pytest result:

- `5 passed`
- `PYTEST_RC=0`

Observed warnings:

- `117 statsmodels KPSS InterpolationWarning`
- non-failing;
- caused by KPSS lookup-table boundary behavior across repeated causal fold evaluations;
- recorded as known statistical warning noise;
- does not invalidate the test results.

Evidence tag:

`STAT_ARB_V2_WALK_FORWARD_OOS_OK`

#### STATUS

`TEST VERIFIED / DONE`

Current StatArb V2 research stack now includes:

- Engle-Granger diagnostics
- ADF / KPSS
- half-life
- Johansen confirmation
- BH-FDR screening
- dynamic Kalman hedge ratio
- hedge stability
- causal residual z-score
- pair economics
- local analytical guard
- causal expected-edge estimator
- hedge-ratio pair sizing
- integrated research pipeline
- walk-forward / OOS structural validation

This stage does NOT yet implement:

- realized entry-to-exit trade lifecycle evaluation;
- Sharpe / realized OOS PnL / drawdown metrics for StatArb V2;
- legacy `statistical_arbitrage.py` adapter/replacement;
- StrategyDecisionEngine integration;
- pair-position execution semantics.

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Decide whether a dedicated StatArb V2 research trade-lifecycle evaluator is required before SHADOW-ONLY strategy adapter integration, or whether the current structural/OOS evidence is sufficient to proceed to adapter integration.

No production boundary changes.

### 52.x. Statistical Arbitrage V2 — Trade Lifecycle State Contract — 2026-09-01

#### ARCHITECTURE DECISION

Approved research-only StatArb V2 trade lifecycle semantics:

- maximum one open pair position;
- signal observed on bar N;
- entry executes on bar N+1 OPEN;
- repeated same-direction signal while position is open is ignored;
- EXIT closes both legs on bar N+1 OPEN;
- opposite spread signal closes the current pair on bar N+1 OPEN;
- opposite signal does NOT immediately reverse into a new pair;
- no pyramiding;
- no overlapping pair trades;
- entry quantities remain frozen for the lifetime of the trade;
- if the dataset ends with an open pair, both legs close at final CLOSE;
- realized pair trade results must use canonical NEXUS cost semantics;
- finalized trades must be compatible with `BacktestTradeResult`;
- performance metrics must use `AIBacktestMetricsService`.

This contract applies only to isolated research/backtest evaluation.

It does NOT authorize or modify:

- StrategyDecisionEngine execution semantics;
- RiskAgent;
- ExecutionAgent;
- ExecutionBoundary;
- BingX/exchange access;
- Restricted Live;
- Full Live.

Evidence tag:

`STAT_ARB_V2_TRADE_LIFECYCLE_STATE_CONTRACT_APPROVED`

#### STATUS

`ARCHITECTURE APPROVED`

Production boundaries remain unchanged:

- Strategy Decision Engine — `SHADOW-ONLY`
- Advisory — `OBSERVE_ONLY`
- Restricted Live — `DISABLED`
- Full Live — `DISABLED`
- AI direct exchange access — `BLOCKED`

#### NEXT STEP

Implement isolated StatArb V2 research trade-lifecycle evaluator and standalone tests using the approved state contract and canonical NEXUS backtest metrics.

### 52.x. Statistical Arbitrage V2 — Realized Trade Lifecycle — 2026-09-01

#### IMPLEMENTED

Added isolated StatArb V2 realized pair trade lifecycle evaluator:

- `strategies/stat_arb/trade_lifecycle.py`
- `tests/test_stat_arb_v2_trade_lifecycle.py`

Approved lifecycle contract implemented:

- maximum one open pair;
- signal observed on bar N;
- entry executes on bar N+1 OPEN;
- EXIT executes on bar N+1 OPEN;
- repeated same-direction signals do not pyramid;
- opposite spread signal closes the current pair only;
- no immediate reversal;
- entry sizing is frozen for the lifetime of the pair;
- open pair at end of dataset closes at final CLOSE.

Realized pair PnL includes both legs.

Existing NEXUS components are reused:

- `size_pair_from_hedge_ratio`
- `estimate_pair_costs`
- `BacktestTradeResult`
- `AIBacktestMetricsService`

Canonical accounting:

`market pair gross PnL - slippage = BacktestTradeResult.gross_pnl`

`net_pnl = gross_pnl - fees - funding`

No Registry, DecisionEngine, RiskAgent, ExecutionAgent,
ExecutionBoundary, or BingX integration was changed.

#### EVIDENCE

Lint:

- `flake8 strategies/stat_arb/trade_lifecycle.py` — PASS
- `FLAKE8_RC=0`

Targeted tests:

- next-open entry/exit pair PnL — PASS
- repeated same-direction signal does not pyramid — PASS
- opposite signal closes without immediate reversal — PASS
- open pair closes at final CLOSE — PASS
- canonical fees/slippage/funding integrity — PASS
- invalid series fails closed — PASS

Pytest:

- `6 passed`
- `PYTEST_RC=0`

Evidence tag:

`STAT_ARB_V2_TRADE_LIFECYCLE_OK`

#### STATUS

`TEST VERIFIED / DONE`

StatArb V2 research stack now includes:

- cointegration/stationarity diagnostics;
- Johansen + BH-FDR screening;
- dynamic Kalman hedge ratio;
- causal signals and hedge stability;
- hedge-ratio pair sizing;
- expected-edge estimation;
- pair costs/funding/slippage;
- local analytical guard;
- integrated research pipeline;
- walk-forward/OOS structural validation;
- realized pair entry/exit lifecycle;
- canonical NEXUS backtest metrics integration.

This does NOT yet replace the legacy
`statistical_arbitrage` strategy.

Production execution path remains unchanged.

#### NEXT STEP

Design and verify the compatibility/replacement adapter that makes
StatArb V2 the canonical `statistical_arbitrage` implementation while
preserving the existing StrategyRegistry / DecisionEngine contract.

Do not enable or modify production execution in this step.

## 53. NEXUS TRADING CORE V2 / SYSTEM MODERNIZATION ROADMAP — 2026-09-01

### 53.1. FACT — Current verified state

The current NEXUS system contains two architectural generations:

1. A mature research / validation / AI governance layer.
2. A legacy production trading path centered on single-symbol
   BUY / SELL strategy outputs and single-leg execution semantics.

The Statistical Arbitrage V2 research program exposed a material
architectural mismatch.

StatArb V2 is pair-native:

- LONG_SPREAD / SHORT_SPREAD / EXIT / HOLD;
- two coordinated legs;
- Kalman hedge ratio;
- hedge-ratio-based pair sizing;
- pair economics;
- pair lifecycle;
- pair-level realized PnL.

The current StrategyResult / ExecutionAgent production contract is
primarily single-leg:

- one symbol;
- BUY / SELL;
- entry price;
- stop loss;
- take profit;
- one execution request.

Therefore, forcing StatArb V2 through the legacy single-leg contract
is NOT an acceptable production architecture.

The direct compatibility-adapter-only approach is superseded by
NEXUS Trading Core V2.

### 53.2. Canonical modernization objective

Target runtime architecture:

Market Data
→ Market Intelligence
→ Strategy
→ TradeIntent
→ Portfolio Target
→ Risk Engine
→ ExecutionPlan
→ ExecutionCoordinator
→ ExecutionBoundary
→ Exchange
→ Order / Fill Events
→ Reconciliation
→ Position / Order Ledger
→ PnL / Scorecard / AIEA Feedback

Existing single-leg strategies remain supported through compatibility
adapters.

Pair and basket strategies become first-class capabilities.

### 53.3. GitHub / open-source reference set

TRADING CORE REFERENCES:

- NautilusTrader
  - event-driven execution;
  - order / position lifecycle;
  - reconciliation;
  - ledger concepts;
  - backtest / live parity.

- Hummingbot
  - Executor pattern;
  - pair / multi-leg execution;
  - leg tracking;
  - recovery state machines.

- vn.py / VeighNa
  - Spread as first-class trading object;
  - spread position ownership;
  - multi-contract strategy patterns.

- QuantConnect LEAN
  - Strategy / Alpha;
  - Portfolio Target;
  - Risk;
  - Execution separation.

RESEARCH / AIEA REFERENCES:

- Kronos Gauntlet
  - locked hypotheses;
  - falsification;
  - cost-wall discipline;
  - PASS / FAIL research gates.

- Freqtrade / FreqAI
  - lookahead analysis;
  - recursive indicator analysis;
  - dynamic pair universe;
  - adaptive model lifecycle.

- VectorBT
  - large-scale parameter / scenario research.

MARKET INTELLIGENCE REFERENCES:

- causal regime / change-point detection;
- HMM / GARCH / Kalman ensemble research patterns.

No external project becomes a runtime dependency merely because it is
used as an architectural reference.

### 53.4. Production boundaries

Current production permissions are unchanged.

This roadmap does NOT authorize:

- new pair-native live execution;
- Restricted Live;
- Full Live;
- AI direct exchange access.

The existing ordinary STRATEGY_ENGINE execution route remains a
separate legacy production path and must be migrated explicitly.

### 53.5. Phase 0 — Current-state reconciliation

Objective:

Create one canonical current state before architectural changes.

Required:

- preserve all VERIFIED / DONE work;
- identify OPEN / PARTIALLY VERIFIED debts;
- map each debt to one modernization phase;
- mark superseded architecture as historical, not deleted.

Evidence gate:

`NEXUS_CURRENT_STATE_RECONCILED_OK`

### 53.6. Phase 1 — TradeIntent contracts

Objective:

Introduce a canonical strategy-to-runtime intent layer.

Required contracts:

- TradeIntent;
- SingleLegTradeIntent;
- PairTradeIntent;
- future BasketTradeIntent;
- ExitIntent;
- immutable intent ID;
- strategy name/version;
- user ownership;
- execution source;
- leg definitions;
- sides;
- quantities / notionals;
- hedge ratio where applicable;
- metadata / evidence linkage.

Rules:

- intent describes desired trading state;
- intent never calls ExecutionAgent;
- intent never accesses the exchange;
- invalid intent fails closed;
- legacy StrategyResult remains supported through adapter logic.

Evidence gate:

`TRADING_CORE_V2_TRADE_INTENT_CONTRACT_OK`

### 53.7. Phase 2 — Order / Position Ledger V2

Objective:

Make ownership and state explicit.

Required:

- trade_intent_id;
- execution_plan_id;
- strategy version lineage;
- pair_trade_id;
- per-leg order IDs;
- per-leg fill state;
- exchange order IDs;
- local / exchange state;
- lifecycle timestamps;
- recovery state;
- immutable historical event trail.

Required properties:

- restart-safe;
- idempotent;
- auditable;
- multi-user isolated.

Evidence gate:

`TRADING_CORE_V2_LEDGER_OK`

### 53.8. Phase 3 — Exchange Reconciliation Engine

Objective:

Reconcile local state against actual exchange state.

Required:

- active positions;
- open orders;
- fill matching;
- missing local fill detection;
- stale local position detection;
- unknown exchange order detection;
- restart recovery;
- deterministic repeated reconciliation;
- discrepancy reporting.

No automatic destructive correction without an approved policy.

Evidence gate:

`TRADING_CORE_V2_RECONCILIATION_OK`

### 53.9. Phase 4 — Execution Coordinator V2

Canonical states:

- PENDING;
- OPENING;
- OPEN;
- CLOSING;
- RECOVERY;
- CLOSED;
- FAILED.

Required coordinators:

- SingleLegExecutionCoordinator;
- PairExecutionCoordinator;
- future BasketExecutionCoordinator.

Required behavior:

- submit orders;
- track fills;
- handle partial fills;
- handle rejects;
- timeout;
- retry;
- recovery;
- deterministic state transitions.

Evidence gate:

`TRADING_CORE_V2_EXECUTION_COORDINATOR_OK`

### 53.10. Phase 5 — Pair-native execution

Objective:

Provide real two-leg execution semantics.

Required:

- coordinated leg A / B open;
- coordinated close;
- frozen entry sizing;
- hedge-ratio integrity;
- hedge mismatch tolerance;
- gross / net pair exposure;
- partial-leg failure recovery;
- no uncontrolled naked exposure;
- pair-level PnL;
- pair ownership in ledger.

Evidence gate:

`TRADING_CORE_V2_PAIR_EXECUTION_OK`

### 53.11. Phase 6 — Portfolio / Risk Engine V2

Objective:

Move from isolated signal risk to portfolio-aware risk.

Required controls:

- gross exposure;
- net exposure;
- per-strategy exposure;
- per-symbol exposure;
- pair exposure;
- hedge mismatch;
- concentration;
- correlated exposure;
- margin usage;
- leverage;
- daily loss;
- drawdown;
- liquidity-aware sizing;
- proportional pair scaling.

Pair risk scaling must preserve hedge ratios.

Evidence gate:

`TRADING_CORE_V2_PORTFOLIO_RISK_OK`

### 53.12. Phase 7 — Strategy Contract V2

Objective:

Separate strategy reasoning from order/exchange implementation.

Requirements:

- strategy produces intent / target;
- strategy never places exchange orders directly;
- strategy capability declaration;
- single-leg capability;
- pair capability;
- future basket capability;
- EXIT becomes first-class intent;
- legacy StrategyResult remains supported through adapter logic.

Evidence gate:

`TRADING_CORE_V2_STRATEGY_CONTRACT_OK`

### 53.13. Phase 8 — Orchestrator refactor

Objective:

Reduce direct execution-lifecycle ownership in the monolithic
Orchestrator.

Orchestrator responsibilities:

- coordinate services;
- request decisions;
- route intents;
- trigger risk;
- trigger execution coordinator;
- receive results;
- persist cycle outcomes.

Execution, recovery, reconciliation and position ownership must move to
dedicated components.

Evidence gate:

`TRADING_CORE_V2_ORCHESTRATOR_REFACTOR_OK`

### 53.14. Phase 9 — Backtest / live contract parity

Objective:

Use the same intent and lifecycle semantics in research and runtime
where technically possible.

Required verification:

- no lookahead;
- deterministic replay;
- same sizing contract;
- same cost contract;
- same pair-intent semantics;
- same lifecycle state semantics;
- explicit documented differences between simulation and live.

Evidence gate:

`TRADING_CORE_V2_BACKTEST_LIVE_PARITY_OK`

### 53.15. Phase 10 — StatArb V2 canonical integration

Objective:

Replace the legacy ratio-zscore
`statistical_arbitrage` implementation with pair-native StatArb V2.

Requirements:

- canonical registry name remains `statistical_arbitrage`;
- legacy ratio-zscore logic is no longer active after cutover;
- V2 produces PairTradeIntent;
- DecisionEngine scoring is updated for V2 features;
- pair risk is mandatory;
- PairExecutionCoordinator is mandatory;
- single-leg fallback must NEVER execute a V2 pair entry;
- EXIT closes both legs;
- pair PnL linked to strategy version;
- old implementation preserved historically, not auto-deleted.

Evidence gate:

`STAT_ARB_V2_CANONICAL_INTEGRATION_OK`

### 53.16. Phase 11 — StatArb V2 BingX DEMO E2E

Objective:

Verify the complete pair-native lifecycle against BingX DEMO / VST.

This phase requires separate explicit user authorization before any
new pair-native exchange execution is enabled.

Required verification:

- open both legs;
- verify fills;
- verify pair ledger ownership;
- verify hedge ratio;
- verify actual exchange positions;
- close both legs;
- verify reconciliation;
- verify partial-fill recovery;
- verify restart recovery;
- verify realized pair PnL attribution.

Evidence gate:

`STAT_ARB_V2_BINGX_DEMO_PAIR_E2E_OK`

### 53.17. Phase 12 — Research Gate V2

Objective:

Prevent a strategy from being classified as strong based on one
favorable backtest.

Reference methodology:

- Kronos Gauntlet;
- existing NEXUS validation framework;
- cross-dataset robustness patterns.

Required gates:

- locked hypothesis;
- locked dataset definition;
- cost wall;
- minimum trade count;
- cross-dataset evaluation;
- regime slices;
- OOS;
- walk-forward;
- degradation analysis;
- catastrophic-fold limit;
- pass-rate qualification;
- explicit PASS / FAIL result.

A failed hypothesis remains FAIL.

No silent threshold relaxation is allowed after results are known.

Evidence gate:

`NEXUS_RESEARCH_GATE_V2_OK`

### 53.18. Phase 13 — Lookahead / recursive hardening

Objective:

Add dedicated anti-bias validation inspired by mature Freqtrade
research tooling.

Required checks:

- future-data perturbation;
- lookahead differential analysis;
- recursive indicator stability;
- startup-history sensitivity;
- deterministic repeated execution.

Evidence gate:

`NEXUS_LOOKAHEAD_RECURSIVE_VALIDATION_OK`

### 53.19. Phase 14 — Dynamic Market Universe V2

Objective:

Build a robust strategy-aware market candidate universe.

Candidate filters:

- exchange availability;
- market age;
- delisting risk;
- quote volume;
- liquidity;
- effective spread;
- volatility;
- market regime;
- optional reliable market-cap data;
- strategy-specific eligibility.

Required behavior:

- deterministic ranking;
- TOP-N selection;
- caching;
- failure isolation;
- per-strategy universe support.

Reference patterns:

- Freqtrade dynamic pairlists;
- liquidity / spread filtering patterns.

Evidence gate:

`NEXUS_DYNAMIC_MARKET_UNIVERSE_V2_OK`

### 53.20. Phase 15 — Market Intelligence V2

Objective:

Move from a single coarse regime label to multi-dimensional
market-state intelligence.

Target state:

- classical trend regime;
- volatility regime;
- liquidity regime;
- transition / change-point risk;
- optional forecast probabilities.

The Market Intelligence layer must inform Strategy and Risk but must
not directly authorize execution.

Evidence gate:

`NEXUS_MARKET_INTELLIGENCE_V2_OK`

### 53.21. Phase 16 — Advanced regime research

Research candidates:

- causal change-point detection;
- TDA-based regime-transition detection;
- HMM regime probabilities;
- GARCH volatility forecasting;
- Kalman state / trend estimation;
- ensemble regime confidence.

Rules:

- research-only until benchmarked;
- strict causal evaluation;
- future-perturbation tests;
- false-alarm analysis;
- must beat current regime baseline before integration.

Evidence gate:

`NEXUS_ADVANCED_REGIME_RESEARCH_OK`

### 53.22. Phase 17 — Research acceleration

Objective:

Support large-scale deterministic strategy and parameter research.

Reference:

VectorBT-style vectorized evaluation patterns.

Required capabilities:

- parameter matrices;
- dataset matrices;
- regime matrices;
- cost scenarios;
- robustness ranking;
- reproducible experiment IDs;
- CPU / memory limits;
- timeout controls;
- deterministic reruns.

Evidence gate:

`NEXUS_RESEARCH_ACCELERATION_OK`

### 53.23. Phase 18 — Adaptive ML / FreqAI patterns

Objective:

Improve AIEA only after Trading Core V2 and Research Gate V2 are
verified.

Candidate capabilities:

- rolling retraining;
- feature-age control;
- model expiration;
- concept-drift detection;
- adaptive prediction;
- model lineage;
- deterministic promotion requirements.

No adaptive model may bypass Research Gate V2.

Evidence gate:

`NEXUS_ADAPTIVE_ML_V2_OK`

### 53.24. Phase 19 — Forecast foundation-model research

Candidate references:

- Kronos;
- future financial time-series foundation models.

Rules:

- research-only;
- forecasting accuracy does not imply trading edge;
- cost-aware evaluation mandatory;
- must beat baseline after costs;
- failed hypotheses remain failed;
- no automatic production authority.

Evidence gate:

`NEXUS_FORECAST_MODEL_RESEARCH_OK`

### 53.25. Phase 20 — Existing strategy modernization

Current strategy registry remains canonical until individual
modernization evidence exists.

Each strategy must undergo:

- GitHub-reference-first benchmark;
- architecture comparison;
- license / maintenance / security review;
- NEXUS gap classification.

Gap categories:

- NONE;
- LOW;
- MEDIUM;
- HIGH;
- VERY HIGH.

Replacement or major rewrite occurs only for:

- HIGH;
- VERY HIGH.

Statistical Arbitrage V2 is the first strategy with a VERIFIED
VERY HIGH legacy gap.

Each modernization receives its own evidence tag.

### 53.26. Phase 21 — Funding / basis arbitrage

Prerequisites:

- PairTradeIntent;
- PairExecutionCoordinator;
- Portfolio Risk;
- Market Intelligence;
- Research Gate V2.

Candidate capabilities:

- funding-rate carry;
- basis spread;
- delta-neutral structures;
- spot/perp where supported;
- perp/perp where appropriate;
- funding-aware lifecycle;
- transaction-cost-aware entry.

No implementation before prerequisites are verified.

### 53.27. Phase 22 — Generalized spread / basket strategies

Prerequisites:

- Pair / Basket intent capability;
- Portfolio Risk;
- Execution Coordinator.

Candidate capabilities:

- static spread weights;
- dynamic hedge ratios;
- multi-asset cointegration;
- market-neutral baskets;
- hedge integrity monitoring;
- basket-level PnL attribution.

### 53.28. Phase 23 — Microstructure / Liquidity V2

Reference patterns:

Hummingbot order-book / execution architecture.

Candidate capabilities:

- order-book depth;
- effective spread;
- top-of-book quality;
- slippage forecasting;
- maker / taker economics;
- order-book imbalance;
- execution-quality scoring.

This layer should improve both:

- Dynamic Market Universe;
- Execution Coordinator.

Evidence gate:

`NEXUS_MICROSTRUCTURE_V2_OK`

### 53.29. Phase 24 — AIEA Strategy Generation V2

Objective:

Permit generated strategies only through an isolated research sandbox.

Requirements:

- immutable parent strategy version;
- explicit capability declaration;
- static security validation;
- no direct exchange dependency;
- no direct ExecutionAgent access;
- no RiskAgent bypass;
- locked experiment definition;
- mandatory Research Gate V2;
- complete strategy genealogy;
- deterministic artifact persistence.

Evidence gate:

`AIEA_STRATEGY_GENERATION_V2_OK`

### 53.30. Phase 25 — Learning Loop V2

Objective:

Use realized evidence for controlled improvement.

Required capabilities:

- trade / pair PnL attribution;
- regime attribution;
- dataset attribution;
- parent / child comparison;
- degradation tracking;
- rejected hypothesis memory;
- rollback evidence;
- no uncontrolled self-modification.

Evidence gate:

`AIEA_LEARNING_LOOP_V2_OK`

### 53.31. Phase 26 — Strategy Registry Lifecycle V2

Required states:

- DRAFT;
- RESEARCH;
- VERIFIED;
- ACTIVE;
- DEPRECATED;
- REPLACED;
- ROLLED_BACK.

Required ownership:

- strategy version;
- parent version;
- evidence links;
- capability type;
- active implementation uniqueness;
- historical preservation.

Evidence gate:

`NEXUS_STRATEGY_REGISTRY_LIFECYCLE_V2_OK`

### 53.32. Phase 27 — Unified Production Safety V2

Objective:

Use one explicit production permission model for all execution sources.

Execution sources:

- STRATEGY_ENGINE;
- AI_PROMOTION;
- PAIR_ENGINE;
- GRID;
- future execution sources.

Required controls:

- source-specific permission;
- strategy allow-list;
- strategy-version permission;
- pair-engine permission;
- risk approval;
- rollback status;
- global kill switch;
- no hidden execution bypass.

Evidence gate:

`NEXUS_PRODUCTION_SAFETY_V2_OK`

### 53.33. Phase 28 — Application / Infrastructure Security

Required review:

- secrets;
- credential storage;
- key rotation;
- log redaction;
- dependency security;
- container privileges;
- network exposure;
- PostgreSQL exposure;
- Redis exposure;
- filesystem permissions;
- backup security.

Evidence gate:

`NEXUS_APPLICATION_SECURITY_CLOSEOUT_OK`

### 53.34. Phase 29 — Multi-user hardening

Required negative verification:

- user A cannot view user B orders;
- user A cannot view user B positions;
- user A cannot view user B pair ledger;
- user A cannot mutate user B intents;
- user A cannot view user B research evidence;
- user A cannot access user B exchange credentials.

Evidence gate:

`NEXUS_MULTI_USER_HARDENING_OK`

### 53.35. Phase 30 — API V2

Expose controlled interfaces for:

- TradeIntents;
- ExecutionPlans;
- PairTrades;
- Order / Position Ledger;
- reconciliation state;
- portfolio exposure;
- strategy versions;
- research evidence.

Requirements:

- authorization;
- ownership checks;
- immutable historical evidence;
- mutation safety;
- no direct exchange bypass.

Evidence gate:

`NEXUS_API_V2_OK`

### 53.36. Phase 31 — Dashboard V2

Priority:

Operational observability before cosmetic UI.

Required views:

- portfolio exposure;
- gross / net risk;
- pair trades;
- pair leg state;
- hedge error;
- open orders;
- fills;
- recovery state;
- reconciliation drift;
- strategy PnL;
- research gate status.

Evidence gate:

`NEXUS_DASHBOARD_V2_OK`

### 53.37. Phase 32 — Observability / SRE

Required telemetry:

- decision latency;
- risk latency;
- order latency;
- fill latency;
- rejection rate;
- partial-fill rate;
- realized vs estimated slippage;
- recovery events;
- reconciliation discrepancies;
- strategy PnL attribution;
- pair hedge error.

Evidence gate:

`NEXUS_OBSERVABILITY_SRE_OK`

### 53.38. Phase 33 — CI / CD Quality Gate

Mandatory CI scope:

- py_compile;
- flake8;
- mypy where applicable;
- unit tests;
- integration tests;
- DB migration tests;
- deterministic replay;
- no-lookahead suite;
- reconciliation tests;
- pair partial-failure tests;
- security tests.

No significant feature may be marked DONE without green evidence.

Evidence gate:

`NEXUS_CICD_QUALITY_GATE_OK`

### 53.39. Phase 34 — Audit / Evidence Closeout

Objective:

Reconcile all historical OPEN / PARTIALLY VERIFIED items against actual
evidence.

Rules:

- DONE only with evidence;
- historical records are preserved;
- superseded architecture is marked superseded, not deleted;
- duplicate work is prohibited;
- every remaining gap maps to one current modernization phase.

Evidence gate:

`NEXUS_AUDIT_CLOSEOUT_OK`

### 53.40. Phase 35 — Restricted Live Architecture Review

This phase is NOT authorized by this roadmap.

Separate requirements:

- architecture review;
- security review;
- risk limits;
- strategy allow-list;
- rollback plan;
- monitoring;
- explicit user approval.

### 53.41. Phase 36 — Restricted Live

DISABLED.

Separate explicit user authorization required.

### 53.42. Phase 37 — Full Live

DISABLED.

Separate explicit user authorization required.

### 53.43. Major milestones

M1 — TRADING CORE V2 FOUNDATION

- TradeIntent;
- Ledger;
- Reconciliation;
- ExecutionCoordinator;
- Portfolio Risk.

M2 — FIRST PAIR-NATIVE STRATEGY

- StatArb V2 canonical integration;
- pair-native BingX DEMO E2E.

M3 — RESEARCH / AIEA V2

- Research Gate V2;
- lookahead / recursive hardening;
- research acceleration.

M4 — MARKET INTELLIGENCE V2

- Dynamic Universe;
- Liquidity;
- Regime;
- Transition detection;
- Forecast candidates.

M5 — PRODUCTION READINESS

- unified production safety;
- security;
- multi-user hardening;
- API;
- Dashboard;
- Observability;
- CI/CD.

### 53.44. Work-selection rule

Strict execution order:

FACT
→ CHECK
→ EVIDENCE
→ AUDIT
→ STATUS
→ ONE NEXT STEP.

Only one primary implementation step may be active at a time.

Existing VERIFIED / DONE work must not be repeated without a new
technical reason.

### 53.45. CURRENT STATUS

`NEXUS_SYSTEM_MODERNIZATION_ROADMAP — ARCHITECTURE DEFINED`

`NEXUS_TRADING_CORE_V2 — NOT IMPLEMENTED`

`STAT_ARB_V2_RESEARCH_STACK — TEST VERIFIED / DONE`

`STAT_ARB_V2_PRODUCTION_REPLACEMENT — NOT YET IMPLEMENTED`

`PAIR_NATIVE_EXECUTION — NOT IMPLEMENTED`

`NEXUS_RESEARCH_GATE_V2 — PLANNED`

`NEXUS_MARKET_INTELLIGENCE_V2 — PLANNED`

`NEXUS_ADAPTIVE_ML_V2 — PLANNED`

Production permissions remain unchanged.

### 53.46. PRIMARY NEXT STEP

Perform a focused Trading Core V2 gap audit of the current:

- Position model;
- RiskAgent;
- ExecutionAgent;
- Orchestrator;
- ExecutionBoundary.

The gap audit must identify:

- components that can remain unchanged;
- components requiring extension;
- components requiring replacement;
- current ownership / state boundaries;
- minimal migration order;
- persistence / migration requirements;
- production safety implications;
- compatibility requirements for existing single-leg strategies;
- requirements for pair-native StatArb V2.

Do not implement Trading Core V2 code until this gap audit is complete.

Target evidence tag:

`TRADING_CORE_V2_GAP_AUDIT_OK`

## 54. NEXUS FRONTEND / CONTROL PLANE V2 — 2026-09-01

### 54.1. Canonical objective

Frontend is a first-class operational component of NEXUS.

It must NOT be postponed until backend modernization is complete.

Every major Trading Core V2 capability must be developed together with:

- backend contract;
- API / transport contract;
- frontend observability contract;
- frontend control contract where mutation is permitted;
- authorization / ownership rules;
- tests;
- Audit evidence.

Canonical rule:

BACKEND CONTRACT
→ API CONTRACT
→ FRONTEND CONTRACT
→ EVIDENCE
→ AUDIT

Frontend and backend evolve in the same modernization phase.

Only one primary implementation step remains active at a time.

### 54.2. Frontend role

The NEXUS frontend becomes an operational Control Plane rather than a
read-only cosmetic dashboard.

It must provide visibility into:

- strategies;
- strategy versions;
- TradeIntents;
- ExecutionPlans;
- pair trades;
- order legs;
- fills;
- positions;
- portfolio exposure;
- risk decisions;
- recovery state;
- reconciliation state;
- PnL;
- Market Intelligence;
- Research Gate evidence;
- production permissions;
- Audit status.

### 54.3. Frontend foundation

Required foundation:

- application shell;
- routing;
- authentication / session handling;
- typed API client;
- WebSocket / event client where required;
- shared DTO contracts;
- loading / error states;
- authorization-aware controls;
- user ownership isolation;
- deterministic frontend state handling.

Evidence gate:

`NEXUS_CONTROL_PLANE_FOUNDATION_OK`

### 54.4. Trading Command Center

Required views:

- exchange/account state;
- balances;
- portfolio exposure;
- open positions;
- active orders;
- active strategies;
- current execution state;
- current production permissions;
- kill-switch status visibility;
- reconciliation status.

Evidence gate:

`NEXUS_TRADING_COMMAND_CENTER_OK`

### 54.5. Strategy Center

Required capabilities:

- strategy registry;
- strategy versions;
- lifecycle status;
- ACTIVE / RESEARCH / REPLACED visibility;
- capability type:
  - SINGLE_LEG;
  - PAIR;
  - future BASKET;
- configuration;
- evidence links;
- parent / child lineage;
- strategy performance.

Evidence gate:

`NEXUS_STRATEGY_CENTER_V2_OK`

### 54.6. Intent / Execution Monitor

Required views:

- TradeIntent;
- ExecutionPlan;
- execution state;
- PENDING;
- OPENING;
- OPEN;
- CLOSING;
- RECOVERY;
- CLOSED;
- FAILED;
- order legs;
- partial fills;
- rejected legs;
- retry / recovery state.

Evidence gate:

`NEXUS_EXECUTION_MONITOR_V2_OK`

### 54.7. Pair Trading Operations UI

Required for StatArb V2 and future pair strategies:

- pair definition;
- symbol A / symbol B;
- side A / side B;
- quantity A / quantity B;
- hedge ratio;
- gross pair exposure;
- net pair exposure;
- hedge mismatch;
- leg fill state;
- pair lifecycle state;
- pair PnL;
- pair recovery state.

Evidence gate:

`NEXUS_PAIR_TRADING_UI_OK`

### 54.8. Portfolio / Risk UI

Required views:

- gross exposure;
- net exposure;
- per-strategy exposure;
- per-symbol exposure;
- pair exposure;
- concentration;
- correlated exposure where available;
- margin usage;
- drawdown;
- daily loss;
- risk rejection reasons;
- hedge mismatch.

Evidence gate:

`NEXUS_PORTFOLIO_RISK_UI_OK`

### 54.9. Reconciliation / Operations Console

Required views:

- local vs exchange positions;
- local vs exchange orders;
- missing fills;
- stale local positions;
- unknown exchange orders;
- reconciliation drift;
- recovery incidents;
- last reconciliation timestamp;
- reconciliation result.

No destructive correction control may exist without separately approved
backend policy and authorization.

Evidence gate:

`NEXUS_RECONCILIATION_CONSOLE_OK`

### 54.10. Co-development rule

Trading Core V2 phases must include frontend/API work as follows:

Phase 1 TradeIntent
→ Intent API / DTO
→ frontend intent visibility

Phase 2 Ledger
→ ledger API
→ order / position ownership UI

Phase 3 Reconciliation
→ reconciliation API
→ operations console

Phase 4 ExecutionCoordinator
→ execution event API
→ execution state monitor

Phase 5 PairExecution
→ pair API
→ pair trading operations UI

Phase 6 PortfolioRisk
→ risk API
→ portfolio / risk UI

Phase 7 StrategyContract
→ strategy capability API
→ Strategy Center

Phase 8 Orchestrator
→ runtime health API
→ trading command center

Phase 9 Backtest / Live parity
→ comparison API
→ research/runtime comparison UI

Phase 10 StatArb V2 integration
→ StatArb V2 pair UI enabled

This rule prevents backend and frontend architecture from diverging.

### 54.11. Existing roadmap correction

Existing:

- Phase 30 API V2;
- Phase 31 Dashboard V2;

remain valid as final productization / closeout phases.

They are NOT the first time API or frontend work begins.

API and frontend contracts are mandatory throughout Trading Core V2.

### 54.12. Major frontend milestones

M1A — CONTROL PLANE FOUNDATION

- frontend architecture;
- auth/session;
- typed contracts;
- trading command center;
- basic intent / execution visibility.

M2A — PAIR OPERATIONS

- StatArb pair lifecycle;
- pair legs;
- hedge ratio;
- pair fills;
- recovery;
- pair PnL.

M3A — RESEARCH / INTELLIGENCE

- Research Gate;
- OOS / walk-forward;
- strategy evidence;
- Dynamic Universe;
- Market Intelligence.

M4A — PRODUCTION OPERATIONS

- reconciliation;
- production permissions;
- risk;
- incidents;
- audit / evidence visibility.

### 54.13. CURRENT STATUS

`NEXUS_FRONTEND_CONTROL_PLANE_V2 — ARCHITECTURE DEFINED`

`NEXUS_CONTROL_PLANE_FOUNDATION — NOT IMPLEMENTED`

`NEXUS_PAIR_TRADING_UI — NOT IMPLEMENTED`

`NEXUS_RECONCILIATION_CONSOLE — NOT IMPLEMENTED`

Frontend development is now a mandatory companion of Trading Core V2.

### 54.14. PRIMARY NEXT STEP

Expand the Trading Core V2 gap audit to include:

- current backend API endpoints;
- current frontend project structure;
- current frontend trading screens;
- current realtime / WebSocket transport;
- current authentication / authorization flow.

The gap audit must classify backend, API and frontend components as:

- KEEP;
- EXTEND;
- REPLACE.

Target evidence tag:

`TRADING_CORE_V2_FULLSTACK_GAP_AUDIT_OK`

## 55. NEXUS VENUE / INSTRUMENT ABSTRACTION V2 — 2026-09-01

### 55.1. Canonical objective

NEXUS must be multi-venue and multi-asset by design.

The Trading Core V2 must NOT depend directly on:

- BingX-specific types;
- crypto-only symbol semantics;
- USDT-only assumptions;
- perpetual-only order semantics.

The target architecture must support current crypto trading and future
extension to:

- multiple crypto exchanges;
- equities;
- ETFs;
- forex;
- commodities;
- futures;
- options;
- indices;
- CFDs;
- other broker / venue integrations.

No new live venue is authorized by this architecture decision alone.

### 55.2. Canonical venue architecture

Target execution path:

Strategy
→ TradeIntent
→ InstrumentId
→ VenueId / AccountId
→ Portfolio Risk
→ ExecutionPlan
→ ExecutionCoordinator
→ VenueAdapter
→ External Venue / Broker

Venue-specific logic must remain behind adapter boundaries.

Trading Core components must consume canonical NEXUS contracts rather
than direct BingX client response structures.

### 55.3. Canonical Instrument model

NEXUS requires a first-class Instrument domain model.

Candidate canonical fields:

- instrument_id;
- symbol;
- venue_id;
- asset_class;
- instrument_type;
- base_asset;
- quote_asset;
- settlement_currency;
- tick_size;
- lot_size;
- quantity_precision;
- price_precision;
- contract_multiplier;
- margin model;
- leverage constraints;
- trading hours;
- settlement model;
- expiration where applicable;
- instrument metadata.

Candidate asset classes:

- CRYPTO;
- EQUITY;
- ETF;
- FOREX;
- COMMODITY;
- FUTURE;
- OPTION;
- BOND;
- INDEX;
- CFD.

Candidate instrument types:

- SPOT;
- PERPETUAL;
- FUTURE;
- OPTION;
- STOCK;
- ETF;
- FX_PAIR;
- CFD.

The exact schema is NOT yet approved and must be based on the current
model / exchange gap audit.

### 55.4. Canonical VenueAdapter contract

Each external venue must implement a canonical NEXUS adapter contract.

Candidate capabilities:

- discover instruments;
- market metadata;
- balances;
- accounts;
- positions;
- open orders;
- historical orders;
- fills;
- place order;
- cancel order;
- modify order where supported;
- order status;
- market data;
- reconciliation.

The exact adapter interface is NOT yet implemented.

### 55.5. Venue capabilities

Venue differences must be explicit rather than handled by scattered
venue-specific conditionals.

Candidate capability flags include:

- spot support;
- margin support;
- futures support;
- options support;
- short selling;
- reduce-only;
- post-only;
- native stop orders;
- client order IDs;
- order modification;
- fractional quantities;
- WebSocket support;
- extended trading hours;
- settlement behavior.

Unsupported capabilities must fail closed.

### 55.6. Multi-venue execution requirement

Trading Core V2 must permit an ExecutionPlan to reference different
venues where the strategy requires it.

Future examples include:

- same crypto instrument across two exchanges;
- spot / perpetual basis structures;
- perp / perp funding structures;
- cross-venue arbitrage;
- future multi-asset hedge structures.

Pair and basket execution must therefore not assume that all legs share
the same exchange.

Multi-venue pair execution is NOT authorized for live trading by this
roadmap alone.

### 55.7. Crypto exchange integration strategy

Existing BingX integration must be evaluated for preservation behind
the new VenueAdapter boundary.

Potential future crypto venue integrations may use:

- native exchange adapters;
- shared external adapter libraries where technically appropriate.

External libraries such as CCXT may be evaluated as implementation
references or adapter infrastructure.

NEXUS canonical domain contracts must remain independent from any
single external library.

### 55.8. Multi-asset risk implications

Portfolio Risk V2 must eventually normalize exposure across:

- venues;
- accounts;
- currencies;
- asset classes;
- instrument types.

Required future risk dimensions include:

- gross notional;
- net notional;
- venue exposure;
- asset-class exposure;
- currency exposure;
- margin;
- leverage;
- liquidity;
- concentration;
- hedge relationships;
- correlated exposure.

Asset-specific risk extensions may be required for:

- futures multipliers;
- options Greeks;
- settlement;
- expiry;
- borrow / short constraints.

These extensions must not be approximated silently.

### 55.9. Market Data abstraction

Market Intelligence and strategies must not depend directly on
venue-specific market-data response formats.

Future canonical market-data contracts may include:

- trades;
- candles;
- top of book;
- order-book depth;
- funding;
- open interest;
- mark price;
- index price;
- corporate-action data where applicable;
- session / trading-hours state.

Venue-specific normalization must occur before data enters canonical
strategy / intelligence layers.

### 55.10. Frontend / Control Plane integration

Control Plane V2 must represent:

- venue;
- account;
- asset class;
- instrument type;
- canonical instrument;
- exchange / broker position;
- execution venue per order leg.

Frontend must NOT hardcode:

- BingX as the only venue;
- USDT as the only quote / settlement currency;
- crypto as the only asset class.

Pair / basket UI must support different venue IDs for different legs.

### 55.11. Trading Core V2 roadmap correction

Trading Core V2 implementation order is extended to include:

TradeIntent
→ Instrument Model
→ VenueAdapter Contract
→ Ledger
→ Reconciliation
→ ExecutionCoordinator
→ Pair / MultiVenue Execution
→ Portfolio Risk
→ Strategy Contract
→ Orchestrator
→ Backtest / Live Parity
→ StatArb V2 integration

Existing roadmap phases remain historically valid.

This section establishes the additional dependency that Instrument and
Venue contracts must be defined before new ledger / execution schemas
are finalized.

### 55.12. Gap audit expansion

The upcoming full-stack Trading Core V2 gap audit must additionally
inspect:

- current exchange models;
- current exchange account ownership;
- current BingX client boundary;
- symbol representation;
- market metadata representation;
- order request / response contracts;
- fill representation;
- position representation;
- current market-data normalization;
- frontend venue assumptions;
- API venue assumptions.

Each component must be classified as:

- KEEP;
- EXTEND;
- WRAP;
- REPLACE.

### 55.13. Architecture principles

Mandatory principles:

1. NEXUS is multi-venue by design.
2. NEXUS is multi-asset by design.
3. Trading Core does not depend directly on BingX-specific types.
4. Venue-specific behavior remains behind canonical adapters.
5. Instrument identity is separate from display ticker.
6. Venue capabilities are explicit.
7. Unsupported capabilities fail closed.
8. Cross-venue strategies use canonical TradeIntent / ExecutionPlan.
9. Existing single-venue strategies remain backward compatible.
10. No new venue receives live permission automatically.

### 55.14. Production safety

Current production permissions remain unchanged.

This architecture decision does NOT authorize:

- new exchange credentials;
- new broker credentials;
- live orders on additional venues;
- multi-venue live execution;
- Restricted Live;
- Full Live;
- AI direct venue access.

Every future venue integration requires separate:

- adapter verification;
- authentication / secret review;
- sandbox / demo verification where available;
- execution semantics verification;
- reconciliation verification;
- security review;
- Audit evidence.

### 55.15. CURRENT STATUS

`NEXUS_VENUE_INSTRUMENT_ABSTRACTION_V2 — ARCHITECTURE DEFINED`

`MULTI_VENUE_EXECUTION — NOT IMPLEMENTED`

`MULTI_ASSET_TRADING — NOT IMPLEMENTED`

`CANONICAL_INSTRUMENT_MODEL — NOT IMPLEMENTED`

`CANONICAL_VENUE_ADAPTER — NOT IMPLEMENTED`

Existing BingX runtime remains unchanged.

### 55.16. PRIMARY NEXT STEP

Expand the current Trading Core V2 full-stack gap audit to include the
Venue / Instrument layer.

The audit scope is now:

- Position / ownership;
- RiskAgent;
- ExecutionAgent;
- Orchestrator;
- ExecutionBoundary;
- exchange / venue models;
- BingX client boundary;
- instrument / symbol semantics;
- market data contracts;
- API;
- authentication / authorization;
- frontend structure;
- realtime transport.

Do not implement Instrument or VenueAdapter code before this audit is
complete.

Target evidence tag:

`TRADING_CORE_V2_MULTI_VENUE_FULLSTACK_GAP_AUDIT_OK`

## 56. Trading Core V2 Multi-Venue Full-Stack Gap Audit — 2026-09-01

### 56.1. FACT

A focused source/runtime architecture audit was completed for:

- Venue / exchange layer;
- Instrument / symbol model;
- Position ownership;
- RiskAgent;
- ExecutionAgent;
- ExecutionBoundary;
- SentOrder;
- GridOrder;
- TradeHistory;
- Orchestrator;
- API;
- WebSocket;
- Frontend;
- Position reconciliation / recovery.

### 56.2. Core finding

NEXUS does not require a clean-sheet rewrite.

Multiple production-grade behaviors already exist, but they are
distributed across legacy agents and strategy-specific persistence
models rather than one canonical trading lifecycle.

Current architecture contains:

- multi-crypto BaseExchangeClient foundation;
- BingX / Binance / Bybit / OKX clients;
- production ExecutionBoundary;
- SentOrder idempotency;
- GridOrder partial lifecycle semantics;
- live Position projection;
- PositionAgent reconciliation / protection recovery;
- AIRiskAgent single-leg risk logic;
- ExecutionAgent single-leg execution / protection behavior;
- TradeHistory realized attribution;
- FastAPI REST/WebSocket foundation.

Missing canonical capabilities include:

- universal Instrument model;
- universal VenueAdapter;
- TradeIntent;
- PortfolioRiskEngine;
- ExecutionPlan;
- persistent ExecutionCoordinator state;
- canonical Order ledger;
- canonical Fill ledger;
- PositionGroup / PositionLeg ownership;
- pair / basket ownership;
- pair execution;
- multi-venue execution;
- canonical reconciliation state;
- authenticated execution event stream;
- Frontend Control Plane.

### 56.3. Component classification

KEEP / WRAP:

- BaseExchangeClient as crypto-client layer;
- existing crypto clients;
- ExecutionBoundary concept;
- TradeHistory realized-attribution role;
- GridOrder as Grid-specific lifecycle;
- SentOrder as legacy idempotency/history;
- FastAPI foundation.

KEEP / EXTEND:

- ExchangeService;
- Exchange model;
- Position;
- API routers.

REFACTOR:

- PositionAgent;
- AIRiskAgent role;
- ExecutionAgent;
- Orchestrator;
- WebSocket protocol;
- TradingSymbol canonical role.

NEW:

- Instrument;
- VenueAdapter;
- TradeIntent;
- PortfolioRiskEngine;
- ExecutionPlan;
- ExecutionOrder;
- ExecutionFill;
- PositionGroup;
- PositionLeg;
- ExecutionCoordinator;
- PairExecutionCoordinator;
- ReconciliationEngine;
- canonical event stream;
- Frontend Control Plane.

### 56.4. Reconciliation finding

PositionAgent already provides proven reconciliation behaviors:

- exchange-to-DB position synchronization;
- hedge-mode symbol+side identity;
- orphaned local-position closure;
- SL/TP close-reason recovery;
- restart protection recovery;
- protection duplicate cleanup;
- create-new-before-remove-old protection semantics.

These behaviors must be preserved and extracted into the future
Reconciliation Engine.

Current BingX-specific response semantics must move behind VenueAdapter.

Exchange-unavailable fallback must become explicit degraded/stale
reconciliation state rather than silently equivalent to reconciled
state.

### 56.5. Canonical migration order

The minimum correct migration order is:

1. Canonical domain contracts:
   - TradeIntent;
   - Instrument;
   - Venue;
   - Account.

2. Canonical persistence contracts:
   - ExecutionPlan;
   - ExecutionOrder;
   - ExecutionFill;
   - PositionGroup;
   - PositionLeg.

3. VenueAdapter layer:
   - existing crypto clients remain below adapter boundary;
   - BingX-specific response semantics move out of core components.

4. Reconciliation Engine:
   - extract proven PositionAgent synchronization/recovery behavior;
   - introduce explicit reconciliation states.

5. PortfolioRiskEngine:
   - preserve deterministic AIRiskAgent logic as single-leg policy;
   - move portfolio limits above strategy-specific sizing.

6. ExecutionCoordinator:
   - decompose current ExecutionAgent responsibilities;
   - preserve idempotency, protection fail-safe and close behavior.

7. PairExecutionCoordinator:
   - coordinated pair open/close;
   - partial-fill recovery;
   - hedge integrity;
   - pair ownership.

8. Orchestrator migration:
   - retain cycle coordination;
   - remove direct trading lifecycle ownership;
   - remove duplicated execution paths.

9. API / event contracts:
   - canonical REST DTOs;
   - authenticated realtime execution events;
   - multi-user ownership.

10. Frontend Control Plane:
    - intent / execution visibility;
    - pair state;
    - risk;
    - reconciliation;
    - venue/account/instrument visibility.

11. StatArb V2 canonical integration:
    - PairTradeIntent;
    - PortfolioRisk;
    - PairExecutionCoordinator;
    - canonical ledger;
    - BingX DEMO verification.

### 56.6. Persistence decision

Existing persistence models must be preserved for backward
compatibility:

- SentOrder;
- GridOrder;
- Position;
- TradeHistory.

They are NOT deleted or rewritten in place as the first migration step.

Canonical Core V2 persistence is added incrementally.

SentOrder remains legacy idempotency/history.

GridOrder remains Grid-specific lifecycle persistence.

Position remains the current single-leg/live projection until
migration is verified.

TradeHistory remains realized PnL / attribution persistence.

Canonical Core V2 requires new ownership entities for:

- ExecutionPlan;
- ExecutionOrder;
- ExecutionFill;
- PositionGroup;
- PositionLeg.

### 56.7. Risk decision

AIRiskAgent is not discarded.

Its deterministic single-leg sizing / leverage / ATR / regime / volume
logic is retained and later extracted behind a SingleLegRiskPolicy.

The following responsibilities must move out of canonical AIRiskAgent
ownership:

- portfolio exposure limits;
- pair risk;
- venue/account exposure;
- cross-asset exposure;
- Research Gate / OOS eligibility.

PortfolioRiskEngine becomes the canonical portfolio-level risk owner.

### 56.8. Execution decision

ExecutionAgent is retained as the source of proven legacy behavior but
must not remain the canonical Trading Core V2 coordinator.

Preserve:

- idempotency behavior;
- ExecutionBoundary usage;
- protection fail-safe;
- protection verification;
- emergency close;
- close protection cleanup.

Move out:

- persistence ownership;
- TradeHistory creation;
- venue-specific response parsing;
- USDT-notional conversion;
- universal SL/TP assumption;
- fee/funding accounting ownership.

### 56.9. ExecutionBoundary decision

ExecutionBoundary concept is retained.

Canonical invariant:

NEW exposure
→ production permission
→ global kill switch
→ VenueAdapter

Risk-reducing close/reduce operations must remain available when the
global new-order kill switch is active.

BingX hedge-mode specifics must move below the boundary into the
BingX venue adapter.

### 56.10. Orchestrator decision

Orchestrator remains the runtime cycle coordinator.

It must stop owning:

- direct position-slot risk logic;
- direct RiskAgent-to-ExecutionAgent coupling;
- local manual position-list mutation;
- duplicated deferred execution logic;
- future pair/recovery lifecycle.

Target orchestration:

Market Context
→ Strategy
→ TradeIntent
→ TradingCoreService
→ ExecutionOutcome

### 56.11. API / Frontend decision

Canonical runtime application:

`app_fastapi:create_app`

The separate `main.py` FastAPI application is not the current Docker
runtime entrypoint and must not receive new canonical Trading Core V2
features unless separately justified.

Existing REST/FastAPI infrastructure is preserved.

Current `/ws/metrics` transport is not sufficient as the final Control
Plane event contract because it:

- is snapshot/poll driven;
- is not proven user-scoped;
- contains USDT-specific balance semantics;
- does not expose canonical execution lifecycle events.

Control Plane V2 requires:

- authenticated user-scoped event delivery;
- REST initial snapshots;
- typed execution / risk / reconciliation events;
- venue/account/instrument aware DTOs.

Frontend application was not found in the current project/home scan
and is therefore treated as NOT IMPLEMENTED until contrary evidence is
found.

### 56.12. Multi-venue / multi-asset decision

Existing BaseExchangeClient and crypto venue clients are retained as a
crypto implementation layer.

They are NOT promoted directly into the universal VenueAdapter
contract.

Canonical Trading Core V2 must remain independent from:

- BingX types;
- crypto-only symbol identity;
- USDT-only assumptions;
- perpetual-only semantics.

TradingSymbol is insufficient as the canonical Instrument model
because ticker identity alone cannot represent venue-specific and
multi-asset instruments.

### 56.13. Production implications

This gap audit authorizes architecture planning only.

It does NOT authorize:

- new live venue connections;
- new broker credentials;
- pair-native live execution;
- multi-venue live execution;
- Restricted Live;
- Full Live;
- AI direct exchange/broker access.

Current execution permissions remain unchanged.

### 56.14. STATUS

`TRADING_CORE_V2_MULTI_VENUE_FULLSTACK_GAP_AUDIT — TEST/ARCHITECTURE VERIFIED`

The audit establishes that NEXUS should evolve incrementally rather
than through a clean-sheet rewrite.

The highest-priority architectural gap is the absence of canonical
domain and ownership contracts connecting strategy intent to
execution, fills, positions, reconciliation and frontend state.

Evidence tag:

`TRADING_CORE_V2_MULTI_VENUE_FULLSTACK_GAP_AUDIT_OK`

### 56.15. PRIMARY NEXT STEP

Begin Trading Core V2 Phase 1 with canonical domain-contract design.

First implementation scope:

- TradeIntent;
- Instrument identity;
- Venue identity;
- Account identity.

Before implementation:

- inspect current project package structure;
- inspect existing enums / DTO / schema patterns;
- inspect current Exchange and TradingSymbol migrations;
- define the minimal non-breaking file placement and dependency graph.

Do not implement persistence or ExecutionCoordinator in the same step.

Target evidence tag:

`TRADING_CORE_V2_CANONICAL_DOMAIN_CONTRACT_DESIGN_OK`

## 57. Trading Core V2 — Canonical Domain Contract Design — 2026-09-01

### 57.1. CHECK

Current NEXUS contract conventions were reviewed.

Verified runtime-contract pattern:

- pure Python dataclasses;
- `@dataclass(frozen=True)` for immutable contracts;
- explicit `validate()` methods;
- explicit serialization where required;
- no SQLAlchemy dependency in analytical/runtime contracts.

No canonical `domain/`, `schemas/`, or `dto/` package currently exists.

`models/` is used for SQLAlchemy persistence.

### 57.2. Architecture decision

Create a dedicated pure-Python package:

`trading_core/`

Initial files:

- `trading_core/__init__.py`
- `trading_core/identities.py`
- `trading_core/intents.py`

Trading Core domain contracts must NOT import:

- SQLAlchemy;
- database;
- FastAPI;
- routers;
- BingXClient;
- BaseExchangeClient;
- RiskAgent;
- ExecutionAgent.

Dependency direction:

Strategies / Risk / Execution / API adapters
→ trading_core domain

trading_core domain
→ no infrastructure dependencies.

### 57.3. Identity contracts

`identities.py` initial scope:

- AssetClass;
- InstrumentType;
- VenueId;
- AccountId;
- InstrumentId.

VenueId:

- immutable;
- non-empty;
- normalized canonical value.

AccountId:

- immutable;
- positive connection/account identity;
- venue-aware.

InstrumentId:

- immutable;
- venue-aware;
- includes native symbol;
- includes instrument type;
- includes asset class.

Ticker alone is NOT canonical instrument identity.

The same native ticker on different venues must represent different
InstrumentId values.

Initial AssetClass values:

- CRYPTO;
- EQUITY;
- ETF;
- FOREX;
- COMMODITY;
- FUTURE;
- OPTION;
- BOND;
- INDEX;
- CFD.

Initial InstrumentType values:

- SPOT;
- PERPETUAL;
- FUTURE;
- OPTION;
- STOCK;
- ETF;
- FX_PAIR;
- CFD.

Detailed derivative contract metadata such as expiry, strike, option
right and contract multiplier is intentionally deferred until the
Instrument persistence / metadata phase.

### 57.4. TradeIntent contracts

`intents.py` initial scope:

- TradeIntentKind;
- TradeIntentShape;
- TradeSide;
- TradeLegIntent;
- TradeIntent.

Initial TradeIntentKind values:

- OPEN;
- CLOSE;
- REDUCE;
- REBALANCE.

Initial TradeIntentShape values:

- SINGLE_LEG;
- PAIR;
- BASKET.

TradeSide values:

- BUY;
- SELL.

TradeLegIntent initial fields:

- leg_id;
- instrument_id;
- account_id;
- side;
- optional quantity.

Quantity is intentionally optional because strategy intent is not the
final execution order.

Portfolio / Risk layers may determine or scale final executable
quantities later.

TradeIntent initial fields:

- intent_id;
- user_id;
- strategy;
- strategy_version;
- source;
- kind;
- shape;
- legs;
- created_at;
- metadata.

### 57.5. Validation invariants

Mandatory:

- intent_id is non-empty;
- user_id is positive;
- strategy is non-empty;
- source is non-empty;
- each leg validates;
- leg IDs are unique;
- quantity is None or positive.

Shape rules:

- SINGLE_LEG requires exactly 1 leg;
- PAIR requires exactly 2 legs;
- BASKET requires at least 2 legs.

All invalid structures fail closed with ValueError.

### 57.6. Architectural boundary

TradeIntent represents desired trading state.

TradeIntent is NOT:

- an exchange order;
- a RiskResult;
- an ExecutionPlan;
- a persisted exchange fill;
- a production permission.

Creating a valid TradeIntent grants no execution authority.

### 57.7. Implementation scope

Phase 1 implementation is limited to:

- `trading_core/__init__.py`;
- `trading_core/identities.py`;
- `trading_core/intents.py`;
- identity unit tests;
- intent unit tests.

This phase must NOT modify:

- SQLAlchemy models;
- migrations;
- AIRiskAgent;
- ExecutionAgent;
- ExecutionBoundary;
- Orchestrator;
- exchange clients;
- production permissions.

### 57.8. STATUS

`TRADING_CORE_V2_CANONICAL_DOMAIN_CONTRACT_DESIGN — ARCHITECTURE APPROVED`

Evidence tag:

`TRADING_CORE_V2_CANONICAL_DOMAIN_CONTRACT_DESIGN_OK`

### 57.9. PRIMARY NEXT STEP

Implement and verify `trading_core/identities.py` first.

Required evidence:

- file content verification;
- python compile;
- flake8;
- focused pytest;
- immutable / validation behavior;
- cross-venue ticker identity test.

Do not implement TradeIntent in the same step.

Target evidence tag:

`TRADING_CORE_V2_IDENTITY_CONTRACTS_OK`

## 59. Trading Core V2 — TradeIntent Contracts — 2026-09-01

### 59.1. IMPLEMENTED

Created canonical immutable TradeIntent domain contracts:

- `trading_core/intents.py`
- `tests/test_trading_core_intents.py`

Implemented:

- `TradeIntentKind`;
- `TradeIntentShape`;
- `TradeSide`;
- `TradeLegIntent`;
- `TradeIntent`.

### 59.2. VERIFIED BEHAVIOR

Verified:

- SINGLE_LEG requires exactly one leg;
- PAIR requires exactly two legs;
- BASKET requires at least two legs;
- leg IDs must be unique;
- optional quantity is allowed;
- provided quantity must be positive;
- account venue must match instrument venue;
- TradeIntent is immutable;
- empty intent ID fails closed;
- cross-venue pair structure remains possible through per-leg venue ownership.

### 59.3. TIMESTAMP TEST CLEANUP

Focused tests originally used deprecated `datetime.utcnow()`.

Tests were updated to:

`datetime.now(UTC)`

This was a test-only cleanup and did not change TradeIntent domain
semantics.

### 59.4. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused test scope:

- `tests/test_trading_core_identities.py`
- `tests/test_trading_core_intents.py`

Result:

`19 passed in 0.09s`

`pytest_exit=0`

No warnings remained in the final verification run.

### 59.5. STATUS

`TRADING_CORE_V2_TRADE_INTENT_CONTRACTS — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_TRADE_INTENT_CONTRACTS_OK`

### 59.6. PRIMARY NEXT STEP

Begin canonical VenueAdapter contract design.

Before implementation:

- inspect existing `BaseExchangeClient` method surface;
- inspect BingX/Binance/Bybit/OKX method compatibility;
- identify the minimal canonical venue capability set;
- separate generic venue operations from crypto/perpetual-specific operations;
- define fail-closed capability semantics.

Do not modify exchange clients or execution path yet.

Target evidence tag:

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACT_DESIGN_OK`

## 60. Trading Core V2 — VenueAdapter Contract Design — 2026-09-01

### 60.1. CHECK

Method surfaces were reviewed for:

- BaseExchangeClient;
- BingXClient;
- BinanceClient;
- BybitClient;
- OKXClient.

BaseExchangeClient defines a crypto-oriented common subset.

BingXClient currently provides the richest execution/reconciliation
surface, including order query, open-order query, leverage,
protections and income/funding history.

Binance, Bybit and OKX clients currently expose a narrower subset.

### 60.2. Architecture decision

Trading Core V2 will introduce a canonical VenueAdapter boundary above
existing exchange clients.

Target layering:

Trading Core
→ VenueAdapter
→ CryptoVenueAdapter
→ BaseExchangeClient
→ venue client

Existing exchange clients are preserved.

VenueAdapter must not directly expose BingX or perpetual-specific
payload semantics.

### 60.3. Canonical operations

Canonical venue concepts:

- capability discovery;
- instrument resolution;
- account state;
- position state;
- order submission;
- order cancellation;
- order query;
- open-order query.

Canonical contracts must replace raw exchange dictionaries over time.

Planned contracts include:

- VenueCapabilities;
- VenueOrderRequest;
- VenueOrderResult;
- VenueOrderState;
- VenuePosition;
- VenueAccountState.

### 60.4. Optional capabilities

Venue-specific capabilities must be declared explicitly and fail
closed when unsupported.

Initial capability categories include:

- market data;
- historical candles;
- leverage configuration;
- hedge mode;
- native stop-loss;
- native take-profit;
- funding / income history;
- order query;
- open-order query;
- bulk instrument/ticker discovery.

Unsupported required capability must block the corresponding operation
before execution.

### 60.5. Venue-specific implementation details

The following remain below VenueAdapter:

- request signing;
- base URLs;
- transport/request helpers;
- native symbol normalization;
- BingX response parsing;
- positionSide semantics;
- venue-specific reduceOnly behavior;
- venue-specific leverage payloads;
- venue-specific protection payloads.

### 60.6. Close semantics

Canonical Trading Core does not require a universal
`close_position()` venue method.

Closing or reducing exposure is expressed through canonical order
semantics, including reduce-only intent where supported.

VenueAdapter translates that intent into the venue-specific mechanism.

This preserves the existing safety invariant that risk-reducing
operations remain distinct from new-exposure permissions.

### 60.7. STATUS

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACT_DESIGN — ARCHITECTURE APPROVED`

Evidence tag:

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACT_DESIGN_OK`

### 60.8. PRIMARY NEXT STEP

Implement the pure-Python VenueAdapter contract layer only.

Initial implementation scope:

- VenueCapabilities;
- VenueOrderRequest;
- VenueOrderResult;
- VenueOrderState;
- abstract VenueAdapter interface;
- focused unit tests.

Do not modify existing exchange clients or production execution path.

Target evidence tag:

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACTS_OK`

## 61. Trading Core V2 — VenueAdapter Contracts — 2026-09-01

### 61.1. IMPLEMENTED

Created canonical pure-Python venue execution contracts:

- `trading_core/venue.py`
- `tests/test_trading_core_venue.py`

Implemented:

- `VenueCapabilities`;
- `VenueOrderState`;
- `VenueOrderSide`;
- `VenueOrderType`;
- `VenueOrderRequest`;
- `VenueOrderResult`;
- abstract `VenueAdapter`.

### 61.2. VERIFIED BEHAVIOR

Verified:

- supported capability requirement passes;
- unsupported capability fails closed;
- unknown capability fails closed;
- MARKET order validation;
- LIMIT order requires positive limit price;
- MARKET order rejects limit price;
- account venue must match instrument venue;
- order request immutability;
- partial fill result support;
- FILLED state requires full requested quantity;
- REJECTED state requires rejection reason.

Existing identity and TradeIntent tests remained green.

### 61.3. ARCHITECTURAL BOUNDARY

The new VenueAdapter contract layer is pure Python.

It does NOT import or modify:

- BaseExchangeClient;
- BingXClient;
- BinanceClient;
- BybitClient;
- OKXClient;
- ExecutionBoundary;
- ExecutionAgent;
- Orchestrator;
- SQLAlchemy;
- FastAPI.

No production execution path was changed.

### 61.4. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused test scope:

- `tests/test_trading_core_identities.py`
- `tests/test_trading_core_intents.py`
- `tests/test_trading_core_venue.py`

Result:

`30 passed in 0.20s`

`pytest_exit=0`

### 61.5. STATUS

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACTS — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACTS_OK`

### 61.6. PRIMARY NEXT STEP

Design canonical execution persistence contracts.

Scope:

- ExecutionPlan;
- ExecutionOrder;
- ExecutionFill;
- PositionGroup;
- PositionLeg;
- ownership and lineage rules;
- lifecycle state model;
- idempotency ownership.

Before implementation:

- inspect current SQLAlchemy conventions;
- inspect migrations around sent_orders / positions / grid_orders;
- inspect uniqueness/index patterns;
- define non-breaking migration strategy.

Do not create DB migrations in the same step.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_CONTRACT_DESIGN_OK`

## 62. Trading Core V2 — Execution Persistence Contract Design — 2026-09-01

### 62.1. CHECK

Current persistence conventions were reviewed for:

- Position;
- GridOrder;
- SentOrder;
- related SQLAlchemy models;
- Alembic index / uniqueness conventions.

Verified legacy roles:

- Position = current single-leg live projection;
- SentOrder = legacy idempotency / submit history;
- GridOrder = Grid-specific richer order lifecycle.

These tables remain backward-compatible legacy persistence and are not
rewritten in place as Core V2 tables.

Newer migrations demonstrate named UniqueConstraint and explicit index
patterns suitable for Core V2 persistence.

### 62.2. Canonical persistence entities

Trading Core V2 introduces separate canonical tables:

- execution_plans;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills.

Canonical ownership chain:

TradeIntent
→ ExecutionPlan
→ PositionGroup
→ PositionLeg
→ ExecutionOrder
→ ExecutionFill

TradeIntent remains a pure domain contract in the current phase and is
referenced through immutable `intent_id` lineage.

### 62.3. ExecutionPlan

ExecutionPlan owns one approved/planned execution lifecycle.

Initial canonical fields:

- internal database ID;
- globally unique plan_id;
- intent_id;
- user_id;
- lifecycle status;
- created_at;
- updated_at.

Indexes:

- plan_id unique;
- intent_id indexed;
- user_id indexed;
- status indexed.

ExecutionPlan does not contain venue-specific response payloads.

### 62.4. PositionGroup

PositionGroup owns one logical trading position lifecycle.

It supports:

- SINGLE_LEG;
- PAIR;
- BASKET.

Initial lineage:

- unique group_id;
- plan ownership;
- user ownership;
- shape;
- strategy;
- strategy_version;
- trade_source;
- lifecycle status;
- opened_at;
- closed_at;
- created_at;
- updated_at.

PositionGroup is the canonical owner of pair/basket state.

### 62.5. PositionLeg

PositionLeg represents one instrument leg inside a PositionGroup.

Initial fields include:

- leg_id;
- group ownership;
- account identity;
- venue identity;
- native symbol;
- instrument type;
- asset class;
- side;
- target quantity;
- filled quantity;
- average entry price;
- average exit price;
- lifecycle status;
- timestamps.

Constraint:

`UNIQUE(position_group_id, leg_id)`

Until canonical Instrument persistence exists, venue/native-symbol/type/
asset-class values are stored as identity snapshots.

This is transitional persistence, not a replacement for the future
canonical Instrument foreign key.

### 62.6. ExecutionOrder

ExecutionOrder is the canonical order lifecycle projection.

Initial lineage:

- unique canonical order_id;
- execution plan;
- position leg;
- account;
- venue.

Initial order state includes:

- client_order_id;
- venue_order_id;
- side;
- order type;
- requested quantity;
- filled quantity;
- average fill price;
- optional limit price;
- reduce_only;
- lifecycle status;
- rejection reason;
- submitted / accepted / filled / cancelled timestamps;
- created_at / updated_at.

`client_order_id` is a canonical idempotency boundary.

Core V2 idempotency must derive from execution ownership such as:

plan_id + leg_id + order sequence / attempt

and must not depend on the legacy minute-bucket key used by SentOrder.

### 62.7. ExecutionFill

ExecutionFill stores immutable fill-level evidence.

Initial fields:

- unique canonical fill_id;
- execution_order ownership;
- optional venue_fill_id;
- quantity;
- price;
- fee;
- fee currency;
- executed_at;
- created_at.

One ExecutionOrder may own zero or many ExecutionFill rows.

ExecutionFill is the execution evidence source.

ExecutionOrder and PositionLeg may maintain aggregate projections
derived from fills.

Venue fill deduplication must use venue-provided stable fill IDs where
available and deterministic adapter/reconciliation identity where they
are not available.

### 62.8. Lifecycle ownership

Canonical state separation:

ExecutionPlan
→ execution workflow state

PositionGroup
→ logical trade / pair / basket state

PositionLeg
→ per-leg position state

ExecutionOrder
→ order lifecycle state

ExecutionFill
→ immutable execution evidence

Order state, fill evidence and position state must not be collapsed
into one table.

### 62.9. Backward compatibility

The initial Core V2 persistence migration must be additive.

Do not delete or repurpose:

- sent_orders;
- grid_orders;
- positions;
- trade_history.

Legacy runtime continues using these tables until the relevant Core V2
migration phase is independently verified.

TradeHistory remains realized attribution/accounting output rather than
execution source-of-truth.

### 62.10. Migration strategy

Migration order:

1. add canonical tables only;
2. verify schema / constraints / indexes;
3. add SQLAlchemy models;
4. test persistence independently;
5. introduce repository/service layer;
6. introduce reconciliation writes;
7. introduce execution writes;
8. only then migrate production readers/writers.

No production writer is switched by schema creation alone.

### 62.11. Production safety

This persistence design changes no production execution permission.

It does NOT authorize:

- pair-native live execution;
- venue cutover;
- Restricted Live;
- Full Live;
- AI direct execution access.

Current production safety boundaries remain unchanged.

### 62.12. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_CONTRACT_DESIGN — ARCHITECTURE APPROVED`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_CONTRACT_DESIGN_OK`

### 62.13. PRIMARY NEXT STEP

Design the first additive database migration for the canonical Core V2
execution persistence tables.

Before writing the migration:

- inspect current Alembic head/revision chain;
- inspect one recent high-quality migration style;
- confirm table names do not already exist;
- confirm PostgreSQL schema state;
- define exact constraints/index names.

Do not apply the migration in the same step.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_DESIGN_OK`

## 63. Trading Core V2 — Execution Persistence Migration Design — 2026-09-01

### 63.1. CHECK

Alembic and live PostgreSQL state were verified before migration design.

Alembic head:

`f81e68355381`

Live database current revision:

`f81e68355381`

Status:

`HEAD == CURRENT`

No migration divergence was detected.

Current PostgreSQL context:

- user: `nexus_user`
- database: `nexus_db`

### 63.2. Target table collision check

The following canonical Core V2 table names were checked in:

- source models;
- Alembic migrations;
- live PostgreSQL schema.

Checked names:

- `execution_plans`
- `position_groups`
- `position_legs`
- `execution_orders`
- `execution_fills`

Result:

`ABSENT`

No naming collision exists in the current codebase or live schema.

### 63.3. Migration style

Recent migration conventions were reviewed from current Alembic head.

Canonical migration style for Core V2:

- explicit revision / down_revision;
- additive `op.create_table(...)`;
- named `UniqueConstraint`;
- explicit index names;
- server-side defaults where operationally required;
- transactional PostgreSQL DDL;
- downgrade removes only newly introduced Core V2 objects.

The first Core V2 persistence migration must be additive only.

### 63.4. Table creation order

Required upgrade order:

1. `execution_plans`
2. `position_groups`
3. `position_legs`
4. `execution_orders`
5. `execution_fills`

This order follows foreign-key ownership.

Required downgrade order is the exact reverse:

1. `execution_fills`
2. `execution_orders`
3. `position_legs`
4. `position_groups`
5. `execution_plans`

### 63.5. Constraint design

Canonical uniqueness:

`execution_plans.plan_id`
→ UNIQUE

`position_groups.group_id`
→ UNIQUE

`position_legs`
→ UNIQUE(`position_group_id`, `leg_id`)

`execution_orders.order_id`
→ UNIQUE

`execution_orders.client_order_id`
→ UNIQUE

`execution_fills.fill_id`
→ UNIQUE

Venue fill deduplication must not rely on a nullable global
`venue_fill_id` UNIQUE constraint.

Where stable venue fill IDs exist, deduplication is scoped through
execution-order ownership.

### 63.6. Index design

Initial indexes must support canonical lifecycle queries.

ExecutionPlan:

- intent_id
- user_id
- status

PositionGroup:

- execution_plan_id
- user_id
- status

PositionLeg:

- position_group_id
- account_id
- venue_id
- native_symbol
- status

ExecutionOrder:

- execution_plan_id
- position_leg_id
- account_id
- venue_id
- venue_order_id
- status

ExecutionFill:

- execution_order_id
- venue_fill_id
- executed_at

Do not add speculative indexes outside verified query paths.

### 63.7. Compatibility

The migration must not modify or delete:

- positions
- sent_orders
- grid_orders
- trade_history
- exchanges
- trading_symbols

No legacy writer is redirected by schema creation alone.

Production runtime behavior remains unchanged.

### 63.8. Production safety

Schema creation grants no production execution permission.

This migration design does NOT enable:

- Restricted Live;
- Full Live;
- pair-native live execution;
- multi-venue live execution;
- AI direct exchange access.

Current production safety boundaries remain unchanged.

### 63.9. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_DESIGN — ARCHITECTURE VERIFIED`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_DESIGN_OK`

### 63.10. PRIMARY NEXT STEP

Create the additive Alembic migration file for:

- execution_plans;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills.

Do not apply the migration yet.

Required verification before apply:

- file content review;
- py_compile;
- flake8;
- `alembic heads`;
- offline SQL generation or equivalent structural verification;
- exact FK / unique / index review.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_FILE_OK`

## 64. Trading Core V2 — Execution Persistence Migration File — 2026-09-01

### 64.1. IMPLEMENTED

Created additive Alembic revision:

`aa3c49db572a_add_trading_core_v2_execution_.py`

Revision lineage:

`f81e68355381`
→
`aa3c49db572a`

Created schema definitions for:

- execution_plans;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills.

The migration has NOT been applied to the live PostgreSQL database.

### 64.2. VERIFIED STRUCTURE

Verified table ownership chain:

ExecutionPlan
→ PositionGroup
→ PositionLeg
→ ExecutionOrder
→ ExecutionFill

Verified foreign keys:

- execution_plans.user_id → users.id;
- position_groups.execution_plan_id → execution_plans.id;
- position_groups.user_id → users.id;
- position_legs.position_group_id → position_groups.id;
- position_legs.account_id → exchanges.id;
- execution_orders.execution_plan_id → execution_plans.id;
- execution_orders.position_leg_id → position_legs.id;
- execution_orders.account_id → exchanges.id;
- execution_fills.execution_order_id → execution_orders.id.

### 64.3. VERIFIED UNIQUENESS

Verified:

- `uq_execution_plans_plan_id`;
- `uq_position_groups_group_id`;
- `uq_position_legs_group_leg`;
- `uq_execution_orders_order_id`;
- `uq_execution_orders_client_order_id`;
- `uq_execution_fills_fill_id`;
- `uq_execution_fills_order_venue_fill`.

### 64.4. VERIFIED INDEXES

Verified lifecycle indexes for:

- intent / user / status;
- execution-plan ownership;
- position-group ownership;
- account / venue / symbol;
- order ownership / venue order ID / status;
- fill ownership / venue fill ID / execution time.

### 64.5. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Alembic head:

`aa3c49db572a (head)`

Offline migration SQL generation:

`alembic upgrade f81e68355381:aa3c49db572a --sql`

Result:

`offline_sql_exit=0`

Offline PostgreSQL DDL confirmed creation of all five canonical Core V2
tables with expected FK, unique and index definitions.

### 64.6. COMPATIBILITY

The migration is additive only.

It does NOT modify or delete:

- positions;
- sent_orders;
- grid_orders;
- trade_history;
- exchanges;
- trading_symbols.

No runtime writer has been redirected.

### 64.7. PRODUCTION SAFETY

The migration file alone grants no execution permission.

It does NOT enable:

- Restricted Live;
- Full Live;
- pair-native live execution;
- multi-venue live execution;
- AI direct execution access.

Current production safety boundaries remain unchanged.

### 64.8. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_FILE — TEST/STRUCTURE VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MIGRATION_FILE_OK`

### 64.9. PRIMARY NEXT STEP

Design and perform a controlled migration-apply verification.

Before applying to live development PostgreSQL:

- create a database schema backup / recovery point;
- verify current Alembic revision is still `f81e68355381`;
- verify target tables are still absent;
- apply only revision `aa3c49db572a`;
- verify Alembic current;
- verify all five tables / constraints / indexes;
- run downgrade / upgrade verification in an isolated database if available.

Do not introduce SQLAlchemy models or runtime writers in the same step.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_SCHEMA_OK`

## 65. Trading Core V2 — Execution Persistence Schema — 2026-09-01

### 65.1. APPLIED

Applied Alembic revision:

`aa3c49db572a`

Upgrade path:

`f81e68355381`
→
`aa3c49db572a`

Post-apply Alembic state:

`aa3c49db572a (head)`

### 65.2. CREATED TABLES

Verified in live PostgreSQL:

- `execution_plans`
- `position_groups`
- `position_legs`
- `execution_orders`
- `execution_fills`

All tables are owned by `nexus_user`.

### 65.3. VERIFIED FOREIGN KEYS

Verified:

- execution_plans.user_id → users.id
- position_groups.execution_plan_id → execution_plans.id
- position_groups.user_id → users.id
- position_legs.position_group_id → position_groups.id
- position_legs.account_id → exchanges.id
- execution_orders.execution_plan_id → execution_plans.id
- execution_orders.position_leg_id → position_legs.id
- execution_orders.account_id → exchanges.id
- execution_fills.execution_order_id → execution_orders.id

### 65.4. VERIFIED UNIQUE CONSTRAINTS

Verified:

- `uq_execution_plans_plan_id`
- `uq_position_groups_group_id`
- `uq_position_legs_group_leg`
- `uq_execution_orders_order_id`
- `uq_execution_orders_client_order_id`
- `uq_execution_fills_fill_id`
- `uq_execution_fills_order_venue_fill`

### 65.5. VERIFIED INDEXES

Verified lifecycle indexes on:

- intent / user / status;
- execution-plan ownership;
- position-group ownership;
- account / venue / native symbol;
- execution-order ownership;
- venue order ID;
- execution status;
- fill ownership;
- venue fill ID;
- executed_at.

### 65.6. VERIFIED DEFAULTS / NULLABILITY

Verified PostgreSQL defaults:

- ExecutionPlan status = CREATED
- PositionGroup status = PENDING
- PositionLeg filled_quantity = 0
- PositionLeg status = PENDING
- ExecutionOrder filled_quantity = 0
- ExecutionOrder reduce_only = false
- ExecutionOrder status = PENDING
- ExecutionFill fee = 0
- created_at / updated_at timestamps use server `now()` where defined.

Nullable lifecycle timestamps and optional prices/venue IDs match the
approved design.

### 65.7. RECOVERY POINT

Pre-apply schema backup was created successfully:

`/tmp/nexus_schema_before_core_v2.sql`

Backup creation:

`backup_exit=0`

No legacy table was modified or removed by the Core V2 migration.

### 65.8. PRODUCTION SAFETY

Schema application did not redirect any runtime writer.

No change was made to:

- ExecutionAgent;
- ExecutionBoundary;
- Orchestrator;
- AIRiskAgent;
- exchange clients;
- production permissions.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 65.9. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_SCHEMA — TEST/SCHEMA VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_SCHEMA_OK`

### 65.10. PRIMARY NEXT STEP

Implement SQLAlchemy model mappings for the five verified Core V2
tables.

Scope:

- ExecutionPlan;
- PositionGroup;
- PositionLeg;
- ExecutionOrder;
- ExecutionFill;
- model exports;
- focused model/schema tests.

Do not introduce runtime writers, repositories, reconciliation writes,
or ExecutionCoordinator integration in the same step.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MODELS_OK`

## 66. Trading Core V2 — Execution Persistence ORM Models — 2026-09-01

### 66.1. IMPLEMENTED

Created SQLAlchemy mappings for the verified Core V2 persistence schema:

- `models/execution_plan.py`
- `models/position_group.py`
- `models/position_leg.py`
- `models/execution_order.py`
- `models/execution_fill.py`

Updated:

- `models/__init__.py`

Added focused tests:

- `tests/test_trading_core_execution_models.py`

Implemented model exports:

- ExecutionPlan
- PositionGroup
- PositionLeg
- ExecutionOrder
- ExecutionFill

### 66.2. VERIFIED MAPPING

Verified ORM mappings match the live Core V2 schema for:

- table names;
- foreign keys;
- unique constraints;
- indexes;
- Numeric precision / scale;
- server defaults;
- nullable semantics.

No SQLAlchemy relationships were introduced in this phase.

Database foreign keys remain the canonical ownership boundary.

### 66.3. CORRECTIVE EVIDENCE

Initial verification exposed one missing source file:

`models/execution_fill.py`

Root cause:

- `models/__init__.py` exported ExecutionFill;
- focused tests imported ExecutionFill;
- source file had not been created.

No workaround was applied.

The missing model file was created according to the already verified
live schema and migration contract.

All verification was then repeated from the beginning.

### 66.4. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused tests:

`python -m pytest -q tests/test_trading_core_execution_models.py`

Result:

`6 passed in 0.70s`

`pytest_exit=0`

Central model import verification:

`import models`

Result:

`execution_plans execution_fills`

`import_exit=0`

### 66.5. COMPATIBILITY

No runtime writer was changed.

No change was made to:

- PositionAgent;
- ExecutionAgent;
- ExecutionBoundary;
- AIRiskAgent;
- Orchestrator;
- existing legacy persistence writers.

Legacy models remain operational.

### 66.6. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MODELS — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MODELS_OK`

### 66.7. PRIMARY NEXT STEP

Design the canonical persistence repository/service boundary for Core V2.

Scope:

- ExecutionPlan persistence;
- PositionGroup / PositionLeg persistence;
- ExecutionOrder persistence;
- ExecutionFill append / deduplication;
- transaction ownership;
- idempotency lookup;
- aggregate refresh rules.

Before implementation:

- inspect current async SQLAlchemy service/repository patterns;
- inspect transaction/commit conventions;
- inspect IntegrityError handling patterns;
- define which layer owns commit/rollback.

Do not connect ExecutionAgent, PositionAgent or Orchestrator in the same step.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_REPOSITORY_DESIGN_OK`

## 67. Trading Core V2 — Execution Repository Design — 2026-09-01

### 67.1. CHECKED CURRENT TRANSACTION PATTERNS

Current database layer:

- `AsyncSessionLocal` uses `AsyncSession`;
- `expire_on_commit=False`;
- sessions are injected through `get_db()`.

Verified modern persistence-style services:

- `AIComparisonPersistenceService`;
- `AIValidationEvidenceService`;
- `AINewsEventService`.

Their persistence methods primarily:

- receive `AsyncSession` from the caller;
- execute queries;
- add ORM rows;
- call `flush()`;
- do not own `commit()`.

Legacy/application/runtime code remains heterogeneous.

Current services and agents including TradingService, ExecutionAgent,
PositionAgent and ExchangeService contain direct `commit()` /
`rollback()` ownership.

Historical `.bak` files were not used as canonical architecture input.

### 67.2. CANONICAL CORE V2 TRANSACTION OWNERSHIP

Core V2 repositories MUST NOT call:

- `commit()`;
- `rollback()`.

Repository responsibility is limited to:

- query;
- add;
- update tracked entities;
- flush;
- refresh when required.

A single outer application/service transaction owns:

- begin;
- commit;
- rollback.

This allows one Core V2 aggregate operation to persist atomically across:

ExecutionPlan
→ PositionGroup
→ PositionLeg
→ ExecutionOrder
→ ExecutionFill

without partial repository-level commits.

### 67.3. REPOSITORY BOUNDARY

Canonical persistence component:

`ExecutionRepository`

It operates only on persistence models and `AsyncSession`.

It MUST NOT import or call:

- ExecutionAgent;
- PositionAgent;
- ExecutionBoundary;
- exchange clients;
- VenueAdapter implementations;
- Orchestrator.

It is persistence-only infrastructure.

### 67.4. EXECUTION PLAN OPERATIONS

Required repository operations:

- add execution plan;
- get by internal DB id;
- get by canonical `plan_id`;
- get by `intent_id`;
- update status;
- flush.

`plan_id` remains database-enforced unique.

Duplicate plan creation MUST NOT silently create a second row.

### 67.5. POSITION GROUP / LEG OPERATIONS

Required PositionGroup operations:

- add group;
- get by `group_id`;
- get by execution plan;
- update lifecycle status.

Required PositionLeg operations:

- add leg;
- get leg by `(position_group_id, leg_id)`;
- list legs for position group;
- update target / filled quantity;
- update average entry / exit price;
- update lifecycle status.

Canonical uniqueness remains:

`(position_group_id, leg_id)`.

### 67.6. EXECUTION ORDER OPERATIONS

Required operations:

- add execution order;
- get by canonical `order_id`;
- get by `client_order_id`;
- get by venue order ID scoped by account / venue when needed;
- list orders for execution plan;
- list orders for position leg;
- update venue order identity;
- update requested / filled state;
- update average fill price;
- update order lifecycle timestamps;
- update rejection reason.

Canonical idempotency identity:

`client_order_id`

with database unique enforcement.

`order_id` remains independently unique canonical internal identity.

### 67.7. EXECUTION FILL OPERATIONS

Execution fills are append-oriented.

Required operations:

- append fill;
- get by canonical `fill_id`;
- find by `(execution_order_id, venue_fill_id)`;
- list fills for execution order;
- aggregate filled quantity and notional when required.

Database uniqueness remains:

- `fill_id`;
- `(execution_order_id, venue_fill_id)`.

A nullable venue fill ID does not by itself provide deduplication.

When venue fill ID is absent, deterministic canonical `fill_id`
generation belongs to the reconciliation/application layer and MUST be
stable across retries/restarts.

Repository MUST NOT invent unstable random deduplication identities.

### 67.8. IDEMPOTENCY CONTRACT

Idempotency is enforced by two layers:

1. deterministic lookup before insert;
2. database unique constraints as the final concurrency guard.

Repository methods MUST NOT convert duplicate writes into silent success
without proving that the existing row represents the same canonical
operation.

For conflicting identity data, fail closed.

Database uniqueness violations are not authorization to auto-merge
records.

### 67.9. INTEGRITY ERROR CONTRACT

Repository methods MUST NOT own transaction rollback.

If `flush()` raises a database integrity failure:

- the exception propagates to the transaction-owning application layer;
- the outer transaction is rolled back there;
- any retry / reread occurs only after rollback in a valid transaction;
- identity mismatch remains an error.

No nested hidden commit/rollback behavior is allowed inside repository
methods.

### 67.10. AGGREGATE WRITE CONTRACT

Initial canonical aggregate creation must be possible inside one caller-
owned transaction:

1. ExecutionPlan;
2. PositionGroup;
3. PositionLeg(s);
4. initial ExecutionOrder(s), if already planned.

All repository writes may use `flush()` to obtain generated primary keys.

No intermediate `commit()` is allowed.

ExecutionFill writes occur later as execution/reconciliation events
arrive, each within the transaction owned by that event-processing
application service.

### 67.11. REFRESH / DERIVED STATE RULE

ExecutionOrder and PositionLeg aggregate quantities are projections of
persisted execution events.

Repository may persist explicitly calculated aggregate fields but MUST
NOT independently invent execution semantics.

Future reconciliation/application logic owns:

- fill interpretation;
- filled-quantity calculation;
- average-price calculation;
- lifecycle transition decisions.

Repository only persists validated resulting state.

### 67.12. FAILURE SEMANTICS

Core V2 persistence is fail-closed.

On:

- identity conflict;
- uniqueness conflict;
- missing ownership parent;
- invalid transaction state;
- database error;

the repository MUST NOT continue with partial writes.

The transaction-owning caller decides rollback and recovery.

### 67.13. COMPATIBILITY

This design does NOT change existing legacy transaction ownership.

No current service or agent is refactored in this phase.

The rule applies to new Trading Core V2 persistence code first.

Legacy transaction normalization is a separate migration/refactor scope.

### 67.14. PRODUCTION SAFETY

Repository design grants no execution permission.

It does NOT enable:

- pair-native live execution;
- Restricted Live;
- Full Live;
- AI direct exchange access.

Production safety boundaries remain unchanged.

### 67.15. STATUS

`TRADING_CORE_V2_EXECUTION_REPOSITORY_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_REPOSITORY_DESIGN_OK`

### 67.16. PRIMARY NEXT STEP

Implement the persistence-only `ExecutionRepository` according to this
contract.

Implementation scope:

- query/add/update/flush only;
- no commit/rollback;
- no runtime agent integration;
- no VenueAdapter calls;
- focused repository tests;
- transaction/idempotency tests.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_REPOSITORY_OK`

## 68. Trading Core V2 — Execution Repository — 2026-09-01

### 68.1. IMPLEMENTED

Created persistence-only repository:

`services/execution_repository.py`

Added focused tests:

`tests/test_trading_core_execution_repository.py`

Repository supports persistence operations for:

- ExecutionPlan;
- PositionGroup;
- PositionLeg;
- ExecutionOrder;
- ExecutionFill.

Implemented operations include:

- add;
- get by canonical identity;
- scoped lookup;
- list;
- update tracked state;
- flush.

### 68.2. TRANSACTION BOUNDARY VERIFIED

Repository does NOT call:

- `commit()`;
- `rollback()`.

Transaction ownership remains with the outer application/service layer.

Repository uses:

- `select`;
- `add`;
- tracked ORM updates;
- `flush`.

### 68.3. RUNTIME ISOLATION VERIFIED

Repository has no dependency on:

- ExecutionAgent;
- PositionAgent;
- ExecutionBoundary;
- VenueAdapter;
- Orchestrator.

It is persistence-only infrastructure.

No runtime execution path was connected in this phase.

### 68.4. TESTED CONTRACTS

Focused tests verify:

- ExecutionPlan add + flush;
- PositionGroup add + flush;
- PositionLeg add + flush;
- ExecutionOrder add + flush;
- ExecutionFill add + flush;
- absence of repository transaction ownership;
- absence of forbidden runtime dependencies.

### 68.5. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused tests:

`python -m pytest -q tests/test_trading_core_execution_repository.py`

Result:

`7 passed in 0.93s`

`pytest_exit=0`

### 68.6. STATUS

`TRADING_CORE_V2_EXECUTION_REPOSITORY — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_REPOSITORY_OK`

### 68.7. PRIMARY NEXT STEP

Design the Core V2 application transaction/service boundary above
ExecutionRepository.

Scope:

- caller-owned transaction lifecycle;
- aggregate creation transaction;
- idempotent create-or-verify behavior;
- IntegrityError handling after rollback;
- retry/read-after-rollback semantics;
- no runtime execution integration yet.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_DESIGN_OK`

## 69. Trading Core V2 — Execution Application Service Design — 2026-09-01

### 69.1. CHECKED CURRENT APPLICATION TRANSACTION PATTERNS

Current repository/persistence-style components use:

- caller-provided `AsyncSession`;
- `select`;
- `add`;
- `flush`;
- no repository-owned commit/rollback.

Current application/runtime services commonly own:

- `commit()`;
- `rollback()`.

No established canonical `async with db.begin()` pattern was found in
the checked active service/runtime scope.

Existing code therefore does not provide one uniform transaction
abstraction suitable for direct reuse.

### 69.2. CANONICAL APPLICATION COMPONENT

New canonical component:

`ExecutionApplicationService`

Responsibility:

- orchestrate persistence-level Core V2 use cases;
- own transaction completion;
- call `ExecutionRepository`;
- enforce idempotent create-or-verify behavior;
- handle rollback and post-rollback identity verification.

It MUST NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- place/cancel exchange orders;
- perform reconciliation;
- call ExecutionAgent;
- call PositionAgent;
- enable any production execution path.

### 69.3. TRANSACTION OWNERSHIP

`ExecutionApplicationService` is the transaction owner for Core V2
persistence use cases.

Repository methods continue to use `flush()` only.

For the current NEXUS session pattern, application methods use explicit:

1. repository operations;
2. `await db.commit()` on success;
3. `await db.rollback()` on failure.

No repository-level commit/rollback is permitted.

A future UnitOfWork abstraction may replace this implementation detail,
but only through a separate approved architecture step.

### 69.4. AGGREGATE CREATE TRANSACTION

Canonical aggregate creation is one transaction:

ExecutionPlan
→ PositionGroup
→ PositionLeg(s)
→ optional initial ExecutionOrder(s)

Required behavior:

1. validate canonical identities before writing;
2. lookup existing canonical plan identity;
3. if absent, create aggregate through repository calls;
4. allow repository `flush()` calls to assign database PKs;
5. commit once after the entire aggregate is valid;
6. rollback the whole operation on any failure.

No intermediate commit is allowed.

### 69.5. IDEMPOTENT CREATE-OR-VERIFY

Retrying the same canonical operation MUST NOT create a duplicate
aggregate.

Pre-insert behavior:

- lookup by canonical unique identity;
- if absent, attempt create;
- if present, verify canonical immutable identity fields.

If existing data matches the same canonical operation:

- return the existing canonical aggregate/result;
- do not create another row.

If identity fields conflict:

- fail closed;
- do not mutate the existing row into the new identity.

### 69.6. CONCURRENT INSERT / INTEGRITYERROR CONTRACT

Database unique constraints remain the final concurrency guard.

If `flush()` or `commit()` raises `IntegrityError` during an idempotent
create operation:

1. immediately `rollback()` the failed transaction;
2. do not query using the failed transaction before rollback;
3. reread using the canonical unique identity after rollback;
4. verify that the persisted row represents the exact same canonical
   operation;
5. return/reuse it only when identity equivalence is proven;
6. otherwise propagate/fail closed.

An `IntegrityError` alone is NOT treated as idempotent success.

### 69.7. PLAN IDENTITY VERIFICATION

For ExecutionPlan retry verification, canonical immutable identity must
at minimum agree on:

- plan_id;
- intent_id;
- user_id.

A matching `plan_id` with different intent/user identity is a conflict.

Mutable lifecycle fields such as status are not used to redefine plan
identity.

### 69.8. POSITION GROUP IDENTITY VERIFICATION

For PositionGroup retry verification, canonical immutable identity must
at minimum agree on:

- group_id;
- execution_plan_id;
- user_id;
- shape;
- strategy;
- strategy_version;
- trade_source.

A matching group_id with conflicting ownership/strategy identity fails
closed.

### 69.9. POSITION LEG IDENTITY VERIFICATION

PositionLeg uniqueness is scoped by:

`(position_group_id, leg_id)`

Retry verification must agree on immutable ownership/instrument fields:

- position_group_id;
- leg_id;
- account_id;
- venue_id;
- native_symbol;
- instrument_type;
- asset_class;
- side.

Lifecycle quantities/prices/status are projections and are not allowed
to redefine leg identity.

### 69.10. EXECUTION ORDER IDENTITY VERIFICATION

Canonical order idempotency uses:

- `order_id`;
- `client_order_id`.

A retry may reuse an existing order only when immutable identity agrees
on at least:

- order_id;
- client_order_id;
- execution_plan_id;
- position_leg_id;
- account_id;
- venue_id;
- side;
- order_type;
- requested_quantity;
- limit_price;
- reduce_only.

Conflicting identity fails closed.

Venue-assigned IDs and lifecycle/fill fields are mutable execution
state, not request identity.

### 69.11. EXECUTION FILL WRITE BOUNDARY

ExecutionFill persistence occurs in later event/reconciliation
application transactions.

Fill writes are NOT part of initial aggregate creation unless an
execution event already exists.

Canonical fill deduplication uses:

- deterministic `fill_id`;
- `(execution_order_id, venue_fill_id)` when venue fill ID exists.

When venue_fill_id is absent, deterministic fill_id generation is owned
by the future event/reconciliation application layer.

### 69.12. READ-AFTER-ROLLBACK RULE

After `IntegrityError`:

- rollback MUST complete first;
- only then may canonical identity be reread;
- reread is performed through ExecutionRepository;
- the result must pass immutable identity equivalence checks.

No query/retry is allowed while the AsyncSession remains in failed
transaction state.

### 69.13. ERROR SEMANTICS

Application service fails closed on:

- identity mismatch;
- parent ownership mismatch;
- uniqueness conflict that cannot be proven idempotent;
- missing required aggregate parent;
- invalid transaction state;
- database failure.

The service MUST NOT silently merge conflicting records.

### 69.14. SESSION CONTRACT

`ExecutionApplicationService` receives an `AsyncSession` from its caller.

The service owns commit/rollback for the use case it executes.

Callers MUST NOT wrap the same write use case in another independently
committing transaction layer.

This prevents ambiguous nested transaction ownership.

### 69.15. COMPATIBILITY

This design applies to new Trading Core V2 application code.

It does NOT refactor legacy transaction ownership in:

- TradingService;
- ExchangeService;
- ExecutionAgent;
- PositionAgent;
- other existing services/agents.

Legacy normalization remains separate backlog scope.

### 69.16. PRODUCTION SAFETY

Application persistence design grants no trading permission.

It does NOT enable:

- VenueAdapter execution;
- pair-native live execution;
- Restricted Live;
- Full Live;
- AI direct exchange access.

Production boundaries remain unchanged.

### 69.17. STATUS

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_DESIGN_OK`

### 69.18. PRIMARY NEXT STEP

Implement persistence-only `ExecutionApplicationService` for canonical
aggregate create-or-verify behavior.

Initial implementation scope:

- caller-provided AsyncSession;
- ExecutionRepository dependency;
- aggregate create;
- one commit on success;
- rollback on failure;
- IntegrityError rollback → reread → identity verify;
- focused transaction/idempotency tests.

No venue, execution-agent, reconciliation or live runtime integration.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_OK`

## 70. Trading Core V2 — Execution Application Service — 2026-09-01

### 70.1. IMPLEMENTED

Created persistence-only application service:

`services/execution_application_service.py`

Added focused tests:

`tests/test_trading_core_execution_application_service.py`

Implemented canonical aggregate create-or-verify flow for:

- ExecutionPlan;
- PositionGroup;
- PositionLeg(s);
- optional initial ExecutionOrder(s).

### 70.2. TRANSACTION OWNERSHIP VERIFIED

ExecutionApplicationService owns the persistence transaction lifecycle.

Verified behavior:

- repository methods remain flush-only;
- one `commit()` occurs after successful aggregate creation;
- `rollback()` occurs on failure;
- no intermediate commit occurs during aggregate construction.

### 70.3. IDEMPOTENCY VERIFIED

Verified pre-insert canonical identity lookup.

Existing ExecutionPlan may be reused only when immutable identity matches:

- plan_id;
- intent_id;
- user_id.

Identity mismatch fails closed.

### 70.4. INTEGRITYERROR RECOVERY VERIFIED

Verified concurrency/error contract:

IntegrityError
→ rollback
→ reread canonical plan identity
→ verify immutable identity
→ verify persisted aggregate
→ reuse only when equivalence is proven.

Queries are not performed against the failed transaction before rollback.

IntegrityError alone is not considered idempotent success.

### 70.5. AGGREGATE VALIDATION

Verified request validation for:

- positive canonical user identity;
- group user ownership matching plan user;
- at least one leg;
- unique leg IDs;
- orders referencing known legs.

### 70.6. RUNTIME ISOLATION

The service does NOT integrate with:

- VenueAdapter;
- ExecutionBoundary;
- ExecutionAgent;
- PositionAgent;
- exchange order placement;
- reconciliation;
- live execution.

This phase is persistence orchestration only.

### 70.7. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused tests:

`python -m pytest -q tests/test_trading_core_execution_application_service.py`

Result:

`7 passed in 0.87s`

`pytest_exit=0`

### 70.8. STATUS

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_OK`

### 70.9. PRIMARY NEXT STEP

Design the canonical execution-plan contract that converts approved
PortfolioTarget / risk output into persistence-ready ExecutionPlan and
per-leg execution requests.

Scope:

- ExecutionPlan domain contract;
- per-leg order request contract;
- quantity / price / reduce-only semantics;
- account / venue / instrument ownership;
- deterministic plan/order/client-order identities;
- validation rules;
- no VenueAdapter execution yet;
- no ExecutionAgent integration yet.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT_DESIGN_OK`

## 71. Trading Core V2 — Execution Plan Contract Design — 2026-09-01

### 71.1. CHECKED EXISTING DOMAIN CONTRACTS

Verified existing canonical domain contracts:

- `TradeIntent`;
- `TradeLegIntent`;
- `TradeIntentKind`;
- `TradeIntentShape`;
- `TradeSide`;
- `VenueId`;
- `AccountId`;
- `InstrumentId`;
- `VenueOrderType`;
- `VenueOrderRequest`.

No canonical `PortfolioTarget` contract currently exists in the checked
repository scope.

Existing `ExecutionPlan` is currently a persistence model, not yet the
canonical domain execution-plan contract.

### 71.2. CANONICAL LAYER BOUNDARY

Target flow:

TradeIntent
→ future PortfolioTarget / risk-approved target
→ ExecutionPlan
→ ExecutionLegPlan(s)
→ ExecutionCoordinator
→ VenueOrderRequest
→ VenueAdapter

ExecutionPlan represents approved execution intent.

It does NOT represent:

- raw strategy intent;
- venue API payload;
- persisted ORM row;
- exchange order result.

### 71.3. DOMAIN / PERSISTENCE NAME SEPARATION

Canonical domain contract:

`trading_core.execution.ExecutionPlan`

Persistence model remains:

`models.execution_plan.ExecutionPlan`

These types have different responsibilities.

Domain code MUST NOT import SQLAlchemy persistence models.

Persistence/application layers may map canonical ExecutionPlan into ORM
entities.

### 71.4. EXECUTION PLAN IDENTITY

Canonical ExecutionPlan fields:

- `plan_id`;
- `intent_id`;
- `user_id`;
- `shape`;
- `strategy`;
- `strategy_version`;
- `source`;
- `legs`;
- `created_at`.

`plan_id` is a deterministic canonical identity for the approved
execution plan.

`intent_id` preserves lineage to TradeIntent.

`plan_id` generation belongs to the planner/application layer and MUST
be stable across retries.

The domain contract MUST NOT generate a random ID internally.

### 71.5. EXECUTION LEG PLAN

Canonical per-leg contract:

`ExecutionLegPlan`

Required fields:

- `leg_id`;
- `order_id`;
- `client_order_id`;
- `account_id: AccountId`;
- `instrument_id: InstrumentId`;
- `side: TradeSide`;
- `quantity`;
- `order_type: VenueOrderType`;
- `limit_price`;
- `reduce_only`.

Optional future execution-policy metadata may be added only through a
separate approved contract extension.

### 71.6. IDENTITY REUSE

ExecutionPlan MUST reuse existing canonical value objects:

- `AccountId`;
- `InstrumentId`;
- `TradeSide`;
- `VenueOrderType`.

Do NOT introduce duplicate execution-specific enums for:

- BUY/SELL;
- MARKET/LIMIT;
- venue;
- account;
- instrument.

VenueOrderSide remains a venue-boundary enum and may be converted from
TradeSide at the VenueOrderRequest mapping boundary.

### 71.7. QUANTITY CONTRACT

ExecutionPlan leg quantity is FINAL execution quantity approved by
portfolio/risk planning.

Unlike `TradeLegIntent.quantity`, ExecutionLegPlan quantity is mandatory.

Rules:

- quantity must be positive;
- quantity must be finite;
- no zero quantity;
- no negative quantity.

ExecutionPlan MUST NOT infer or resize quantity.

Sizing belongs upstream to PortfolioTarget / risk / planner logic.

### 71.8. PRICE / ORDER TYPE CONTRACT

ExecutionLegPlan uses canonical `VenueOrderType`.

For MARKET:

- `limit_price` MUST be absent.

For LIMIT:

- `limit_price` MUST be present and positive.

ExecutionPlan validation mirrors the semantic constraints already
verified in `VenueOrderRequest`.

ExecutionPlan itself does NOT perform venue tick-size rounding.

Venue/instrument normalization occurs later in execution planning /
adapter translation.

### 71.9. REDUCE-ONLY CONTRACT

`reduce_only` is explicit per execution leg.

It is never inferred from BUY/SELL direction.

For CLOSE / REDUCE intents, upstream planning is expected to set
reduce_only according to instrument/venue semantics.

ExecutionPlan only carries the approved value.

### 71.10. ACCOUNT / INSTRUMENT OWNERSHIP

Each ExecutionLegPlan requires:

`account_id.venue_id == instrument_id.venue_id`

Cross-venue PAIR/BASKET plans are allowed.

Different legs may use different accounts/venues.

A single leg may not reference an account from a different venue than
its instrument.

### 71.11. LEG IDENTITY

Within one ExecutionPlan:

- leg_id MUST be unique;
- order_id MUST be unique;
- client_order_id MUST be unique.

These identities MUST be deterministic and stable across retry/restart.

The domain contract validates uniqueness but does not generate IDs.

### 71.12. SHAPE CONTRACT

ExecutionPlan uses existing `TradeIntentShape`.

Validation:

- SINGLE_LEG → exactly 1 leg;
- PAIR → exactly 2 legs;
- BASKET → at least 2 legs.

No new execution-shape enum is introduced.

### 71.13. TRADE INTENT LINEAGE

ExecutionPlan preserves TradeIntent lineage but is not required to
contain the full TradeIntent object.

Canonical lineage fields:

- intent_id;
- strategy;
- strategy_version;
- source;
- shape.

Future planner logic must verify that generated ExecutionPlan lineage
matches the source TradeIntent / approved target.

### 71.14. VENUE ORDER REQUEST MAPPING

ExecutionLegPlan maps one-to-one into a future VenueOrderRequest:

- client_order_id → client_order_id;
- account_id → account_id;
- instrument_id → instrument_id;
- TradeSide → VenueOrderSide;
- quantity → quantity;
- order_type → order_type;
- limit_price → limit_price;
- reduce_only → reduce_only.

This mapping belongs to execution coordination/planning infrastructure.

The domain ExecutionPlan MUST NOT call VenueAdapter.

### 71.15. PERSISTENCE MAPPING

ExecutionPlan domain data maps into verified persistence tables:

ExecutionPlan
→ execution_plans

ExecutionLegPlan
→ PositionLeg + ExecutionOrder

Persistence mapping includes:

- venue_id from InstrumentId / AccountId;
- native_symbol;
- instrument_type;
- asset_class;
- account_id;
- side;
- quantity;
- order type;
- limit price;
- reduce_only;
- deterministic identities.

The domain contract MUST NOT depend on ORM models.

### 71.16. STATUS OWNERSHIP

ExecutionPlan domain contract does NOT own execution lifecycle mutation.

Persistence/runtime statuses such as:

- CREATED;
- PENDING;
- ACCEPTED;
- PARTIALLY_FILLED;
- FILLED;
- CANCELLED;
- REJECTED;

belong to persistence/execution lifecycle state.

The immutable domain plan describes what was approved for execution.

### 71.17. NUMERIC REPRESENTATION

Canonical ExecutionPlan quantities/prices SHOULD use `Decimal`.

Reason:

- persistence schema uses Numeric(20, 8);
- execution quantities/prices are financial values;
- deterministic identity comparison must avoid float drift.

TradeIntent currently uses optional float quantity and VenueOrderRequest
currently uses float.

ExecutionPlan becomes the precision boundary where approved execution
values are represented as Decimal.

Conversion to venue-native numeric representation happens only at the
adapter mapping boundary.

### 71.18. PORTFOLIO TARGET STATUS

A canonical PortfolioTarget contract is NOT IMPLEMENTED yet.

ExecutionPlan design does not invent that contract.

Future work must define:

TradeIntent
→ PortfolioTarget
→ PortfolioRisk
→ ExecutionPlan

as a separate canonical domain step.

Until then, ExecutionPlan may be constructed only by explicitly
approved planner/application inputs in tests/shadow development.

### 71.19. PRODUCTION SAFETY

ExecutionPlan contract design grants no execution permission.

It does NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- call ExecutionAgent;
- submit orders;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production boundaries remain unchanged.

### 71.20. STATUS

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT_DESIGN_OK`

### 71.21. PRIMARY NEXT STEP

Implement the pure-Python canonical ExecutionPlan domain contract.

Scope:

- `trading_core/execution.py`;
- immutable ExecutionPlan;
- immutable ExecutionLegPlan;
- Decimal quantity/price validation;
- reuse canonical identities/enums;
- shape/uniqueness validation;
- no ORM imports;
- no VenueAdapter calls;
- focused domain tests.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT_OK`

## 72. Trading Core V2 — Execution Plan Contract — 2026-09-01

### 72.1. IMPLEMENTED

Created pure-Python canonical execution domain contract:

`trading_core/execution.py`

Implemented immutable:

- `ExecutionPlan`;
- `ExecutionLegPlan`.

Added focused tests:

`tests/test_trading_core_execution.py`

### 72.2. CANONICAL TYPE REUSE VERIFIED

Execution contract reuses existing canonical types:

- `AccountId`;
- `InstrumentId`;
- `TradeSide`;
- `TradeIntentShape`;
- `VenueOrderType`.

No duplicate BUY/SELL, MARKET/LIMIT, venue, account, instrument or
shape enums were introduced.

### 72.3. EXECUTION LEG CONTRACT VERIFIED

ExecutionLegPlan validates:

- non-empty leg_id;
- non-empty order_id;
- non-empty client_order_id;
- AccountId;
- InstrumentId;
- account/instrument venue ownership;
- TradeSide;
- mandatory Decimal quantity;
- finite positive quantity;
- VenueOrderType;
- MARKET without limit_price;
- LIMIT with positive Decimal limit_price;
- explicit boolean reduce_only.

### 72.4. EXECUTION PLAN CONTRACT VERIFIED

ExecutionPlan validates:

- non-empty plan_id;
- non-empty intent_id;
- positive user_id;
- TradeIntentShape;
- strategy;
- source;
- datetime created_at;
- at least one ExecutionLegPlan;
- unique leg_id values;
- unique order_id values;
- unique client_order_id values.

Shape rules verified:

- SINGLE_LEG = exactly 1 leg;
- PAIR = exactly 2 legs;
- BASKET = at least 2 legs.

### 72.5. MULTI-VENUE CONTRACT VERIFIED

Cross-venue PAIR plans are allowed.

Each individual execution leg still requires:

`account_id.venue_id == instrument_id.venue_id`

This preserves multi-venue architecture without allowing invalid
cross-venue ownership inside one leg.

### 72.6. NUMERIC PRECISION VERIFIED

Execution quantity and limit price use `Decimal`.

Verified rejection of:

- float execution quantity;
- zero quantity;
- negative quantity;
- NaN;
- Infinity;
- invalid LIMIT prices.

ExecutionPlan performs no sizing and no venue tick-size normalization.

### 72.7. ARCHITECTURAL PURITY

The domain execution contract does NOT depend on:

- SQLAlchemy;
- ORM models;
- ExecutionRepository;
- ExecutionApplicationService;
- ExecutionAgent;
- ExecutionBoundary;
- VenueAdapter implementation;
- exchange clients.

No order submission or runtime execution behavior exists in this
contract.

### 72.8. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused execution contract tests:

`python -m pytest -q tests/test_trading_core_execution.py`

Result:

`15 passed in 0.09s`

`execution_pytest_exit=0`

Core domain regression:

- `tests/test_trading_core_identities.py`
- `tests/test_trading_core_intents.py`
- `tests/test_trading_core_venue.py`
- `tests/test_trading_core_execution.py`

Result:

`45 passed in 0.19s`

`core_regression_exit=0`

### 72.9. PRODUCTION SAFETY

This pure domain contract grants no execution permission.

It does NOT enable:

- VenueAdapter execution;
- ExecutionBoundary execution;
- Restricted Live;
- Full Live;
- AI direct exchange access.

Production boundaries remain unchanged.

### 72.10. STATUS

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_CONTRACT_OK`

### 72.11. PRIMARY NEXT STEP

Design the canonical mapping boundary from immutable domain
`ExecutionPlan` into persistence/application create contracts and,
later, VenueOrderRequest.

Scope:

- domain → persistence mapping ownership;
- ExecutionPlan → PositionGroup / PositionLeg / ExecutionOrder mapping;
- enum/value conversion;
- Decimal preservation;
- deterministic identity preservation;
- TradeSide → VenueOrderSide mapping boundary definition;
- no VenueAdapter calls;
- no execution coordinator integration yet.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_MAPPING_DESIGN_OK`

## 73. Trading Core V2 — Execution Plan Mapping Design — 2026-09-01

### 73.1. CHECKED CURRENT MAPPING PATTERNS

No canonical mapper / translation infrastructure was found in the
checked Trading Core V2 scope.

Current code contains serialization helpers such as `to_dict()`, but no
established domain-to-persistence mapping convention suitable for
ExecutionPlan reuse.

Current representations:

- `trading_core.execution.ExecutionPlan`
  = immutable canonical domain contract;

- `ExecutionAggregateCreate`
  = persistence application input DTO;

- SQLAlchemy execution models
  = persistence representation;

- `VenueOrderRequest`
  = venue-boundary request.

### 73.2. CANONICAL MAPPING OWNERSHIP

Two separate mapping boundaries are required.

Boundary A:

Domain ExecutionPlan
→ Persistence application contract

Boundary B:

ExecutionLegPlan
→ VenueOrderRequest

These mappings MUST remain separate.

Persistence mapping MUST NOT depend on VenueAdapter.

Venue-request mapping MUST NOT depend on SQLAlchemy models.

### 73.3. DOMAIN → PERSISTENCE MAPPER

Canonical component:

`ExecutionPersistenceMapper`

Target location:

`services/execution_persistence_mapper.py`

Responsibility:

- accept immutable domain `ExecutionPlan`;
- validate already-canonical domain input;
- produce `ExecutionAggregateCreate`;
- preserve deterministic identities;
- preserve Decimal quantities/prices;
- convert canonical value objects into persistence scalar values.

It MUST NOT:

- commit;
- rollback;
- access AsyncSession;
- import ExecutionRepository;
- access VenueAdapter;
- submit orders.

It is a pure translation component.

### 73.4. EXECUTION PLAN → EXECUTION PLAN CREATE

Mapping:

Domain ExecutionPlan.plan_id
→ ExecutionPlanCreate.plan_id

Domain ExecutionPlan.intent_id
→ ExecutionPlanCreate.intent_id

Domain ExecutionPlan.user_id
→ ExecutionPlanCreate.user_id

No identity regeneration is allowed.

### 73.5. EXECUTION PLAN → POSITION GROUP CREATE

One immutable domain ExecutionPlan maps to one PositionGroupCreate.

Canonical mapping:

- group_id
  = deterministic group identity supplied by mapper input / identity
    policy, not generated randomly inside persistence layer;

- user_id
  = ExecutionPlan.user_id;

- shape
  = ExecutionPlan.shape.value;

- strategy
  = ExecutionPlan.strategy;

- strategy_version
  = ExecutionPlan.strategy_version;

- trade_source
  = ExecutionPlan.source.

Because canonical ExecutionPlan currently does NOT contain `group_id`,
the mapper MUST NOT invent a random group identity.

Group identity generation remains an explicit upstream deterministic
identity-policy responsibility.

### 73.6. GROUP ID REQUIREMENT

Persistence mapping therefore requires one explicit deterministic
`group_id` argument in addition to ExecutionPlan.

Initial mapper API:

`to_aggregate_create(plan, group_id)`

Rules:

- group_id required;
- group_id normalized;
- empty group_id rejected;
- mapper does not generate UUID/random values.

A future PositionGroup domain contract may absorb this identity only
through a separately approved contract change.

### 73.7. EXECUTION LEG → POSITION LEG CREATE

Each ExecutionLegPlan maps to one PositionLegCreate.

Mapping:

- leg_id
  → leg_id;

- account_id.value
  → account_id;

- account_id.venue_id.value
  → venue_id;

- instrument_id.native_symbol
  → native_symbol;

- instrument_id.instrument_type.value
  → instrument_type;

- instrument_id.asset_class.value
  → asset_class;

- side.value
  → side;

- quantity
  → target_quantity.

Decimal quantity MUST remain Decimal.

No float conversion is allowed in persistence mapping.

### 73.8. EXECUTION LEG → EXECUTION ORDER CREATE

Each ExecutionLegPlan also maps to one ExecutionOrderCreate.

Mapping:

- order_id
  → order_id;

- client_order_id
  → client_order_id;

- account_id.value
  → account_id;

- account_id.venue_id.value
  → venue_id;

- side.value
  → side;

- order_type.value
  → order_type;

- quantity
  → requested_quantity;

- limit_price
  → limit_price;

- reduce_only
  → reduce_only;

- leg_id
  → leg_id.

Deterministic order/client-order identities are preserved exactly.

### 73.9. DECIMAL PRESERVATION

Persistence mapper MUST preserve:

- quantity as Decimal;
- limit_price as Decimal or None.

No conversion to float is permitted.

Reason:

- domain execution precision boundary is Decimal;
- persistence schema uses Numeric(20, 8);
- float conversion would reintroduce precision drift.

### 73.10. ENUM / VALUE CONVERSION

Domain-to-persistence scalar conversion uses enum `.value`.

Examples:

- TradeIntentShape.PAIR
  → `"PAIR"`;

- TradeSide.BUY
  → `"BUY"`;

- VenueOrderType.MARKET
  → `"MARKET"`;

- InstrumentType.PERPETUAL
  → `"PERPETUAL"`;

- AssetClass.CRYPTO
  → `"CRYPTO"`.

Persistence rows continue to store scalar strings.

Canonical enums remain domain truth.

### 73.11. VENUE REQUEST MAPPER

Venue mapping is a separate future component.

Canonical responsibility:

`ExecutionVenueRequestMapper`

Target mapping:

ExecutionLegPlan
→ VenueOrderRequest

It MUST NOT import ORM models.

It MUST NOT call VenueAdapter.

It only translates canonical execution data into venue-boundary request
data.

### 73.12. TRADE SIDE → VENUE SIDE

TradeSide to VenueOrderSide conversion occurs only at the venue request
mapping boundary.

Canonical mapping:

TradeSide.BUY
→ VenueOrderSide.BUY

TradeSide.SELL
→ VenueOrderSide.SELL

No string-based implicit conversion inside VenueAdapter implementations
is required.

The mapper performs explicit enum conversion.

### 73.13. VENUE NUMERIC CONVERSION

Domain ExecutionLegPlan uses Decimal.

Current VenueOrderRequest uses float.

Therefore Decimal → float conversion, if still required by the current
VenueOrderRequest contract, occurs only at the venue-request boundary.

Persistence mapping MUST NOT perform this conversion.

A future VenueOrderRequest Decimal migration is separate contract scope.

### 73.14. MAPPING VALIDATION

Mapper assumes ExecutionPlan constructor validation has already passed,
but MUST still fail closed on mapper-specific requirements:

- invalid / empty deterministic group_id;
- unsupported domain type;
- missing required deterministic identities.

Mapper MUST NOT silently repair or infer invalid execution data.

### 73.15. APPLICATION SERVICE INTEGRATION BOUNDARY

ExecutionApplicationService should eventually accept output from
ExecutionPersistenceMapper rather than manually reconstruct domain
fields.

Target flow:

ExecutionPlan
→ ExecutionPersistenceMapper
→ ExecutionAggregateCreate
→ ExecutionApplicationService
→ ExecutionRepository

This removes manual field copying from runtime/application callers.

No change to ExecutionApplicationService is implemented in this design
step.

### 73.16. ARCHITECTURAL DEPENDENCY RULE

Allowed:

`services.execution_persistence_mapper`
→ `trading_core.execution`
→ application create DTO contracts

Forbidden:

domain trading_core
→ services
→ models
→ SQLAlchemy

The dependency direction remains outward from pure domain into
infrastructure mapping.

### 73.17. PRODUCTION SAFETY

Mapping design grants no execution permission.

It does NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- call ExecutionAgent;
- submit or cancel orders;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production boundaries remain unchanged.

### 73.18. STATUS

`TRADING_CORE_V2_EXECUTION_PLAN_MAPPING_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PLAN_MAPPING_DESIGN_OK`

### 73.19. PRIMARY NEXT STEP

Implement pure translation component:

`services/execution_persistence_mapper.py`

Scope:

- ExecutionPlan → ExecutionAggregateCreate;
- explicit deterministic group_id input;
- Decimal preservation;
- enum/value conversion;
- deterministic identity preservation;
- no database/session access;
- no VenueAdapter calls;
- focused mapper tests.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MAPPER_OK`

## 74. Trading Core V2 — Execution Persistence Mapper — 2026-09-01

### 74.1. IMPLEMENTED

Created pure translation component:

`services/execution_persistence_mapper.py`

Added focused tests:

`tests/test_trading_core_execution_persistence_mapper.py`

Implemented mapping:

Domain `ExecutionPlan`
→ `ExecutionAggregateCreate`

### 74.2. PLAN IDENTITY MAPPING VERIFIED

Verified exact preservation of:

- plan_id;
- intent_id;
- user_id.

Mapper does not regenerate canonical identities.

### 74.3. POSITION GROUP MAPPING VERIFIED

Verified mapping:

- explicit deterministic group_id;
- user_id;
- shape;
- strategy;
- strategy_version;
- trade_source.

group_id is normalized and empty group IDs are rejected.

Mapper does not generate random group identity.

### 74.4. POSITION LEG MAPPING VERIFIED

Each ExecutionLegPlan maps to PositionLegCreate with:

- leg_id;
- account_id;
- venue_id;
- native_symbol;
- instrument_type;
- asset_class;
- side;
- target_quantity.

Canonical AccountId / InstrumentId values are converted into persistence
scalar fields without changing identity.

### 74.5. EXECUTION ORDER MAPPING VERIFIED

Each ExecutionLegPlan maps to ExecutionOrderCreate with:

- order_id;
- client_order_id;
- account_id;
- venue_id;
- side;
- order_type;
- requested_quantity;
- limit_price;
- reduce_only;
- leg_id.

Deterministic identities are preserved.

### 74.6. DECIMAL PRESERVATION VERIFIED

Execution quantity remains Decimal.

LIMIT price remains Decimal.

No float conversion is performed by persistence mapping.

This preserves compatibility with the verified Numeric(20, 8)
persistence schema.

### 74.7. MULTI-VENUE MAPPING VERIFIED

Cross-venue execution plans remain separated per leg.

Verified preservation of:

- distinct venue IDs;
- distinct account IDs;
- distinct instrument identities.

Mapper does not collapse multi-venue plans into a single exchange
identity.

### 74.8. ARCHITECTURAL PURITY

ExecutionPersistenceMapper has no responsibility for:

- AsyncSession;
- ExecutionRepository;
- commit;
- rollback;
- VenueAdapter;
- ExecutionBoundary;
- ExecutionAgent;
- exchange order placement.

It is translation-only infrastructure.

### 74.9. EVIDENCE

Ephemeral NEXUS application image verification:

`python -m py_compile`
→ PASS
→ exit 0

`python -m flake8`
→ PASS
→ exit 0

Focused mapper tests:

`python -m pytest -q tests/test_trading_core_execution_persistence_mapper.py`

Result:

`8 passed in 0.89s`

`pytest_exit=0`

Core mapping regression:

- `tests/test_trading_core_execution.py`
- `tests/test_trading_core_execution_application_service.py`
- `tests/test_trading_core_execution_persistence_mapper.py`

Result:

`30 passed in 0.99s`

`mapping_regression_exit=0`

### 74.10. PRODUCTION SAFETY

This mapper grants no execution permission.

It does NOT enable:

- VenueAdapter execution;
- ExecutionBoundary execution;
- ExecutionAgent integration;
- Restricted Live;
- Full Live;
- AI direct exchange access.

Production boundaries remain unchanged.

### 74.11. STATUS

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MAPPER — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_PERSISTENCE_MAPPER_OK`

### 74.12. PRIMARY NEXT STEP

Design the separate canonical venue-request mapping boundary:

ExecutionLegPlan
→ VenueOrderRequest

Scope:

- explicit TradeSide → VenueOrderSide conversion;
- Decimal → current VenueOrderRequest numeric representation;
- deterministic client_order_id preservation;
- AccountId / InstrumentId preservation;
- MARKET / LIMIT / reduce_only mapping;
- no VenueAdapter call;
- no coordinator integration;
- no live execution.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPING_DESIGN_OK`

## 75. Trading Core V2 — Execution Venue Request Mapping Design — 2026-09-01

### 75.1. CHECKED CURRENT VENUE REQUEST BOUNDARY

Verified canonical venue contract:

`trading_core.venue.VenueOrderRequest`

Current required fields:

- client_order_id;
- AccountId;
- InstrumentId;
- VenueOrderSide;
- quantity;
- VenueOrderType;
- optional limit_price;
- reduce_only.

Verified canonical execution-leg contract:

`trading_core.execution.ExecutionLegPlan`

Current fields already provide:

- deterministic client_order_id;
- AccountId;
- InstrumentId;
- TradeSide;
- Decimal quantity;
- VenueOrderType;
- Decimal / None limit_price;
- reduce_only.

No active runtime `VenueOrderRequest(...)` construction or
`submit_order(...)` call-site was found in the checked Core V2/service/
agent scope.

### 75.2. CANONICAL MAPPER

Canonical translation component:

`ExecutionVenueRequestMapper`

Target location:

`services/execution_venue_request_mapper.py`

Responsibility:

ExecutionLegPlan
→ VenueOrderRequest

The mapper is translation-only.

It MUST NOT:

- call VenueAdapter;
- call submit_order;
- call cancel_order;
- access AsyncSession;
- access ExecutionRepository;
- access ORM models;
- commit or rollback;
- perform execution coordination.

### 75.3. IDENTITY PRESERVATION

Mapper preserves exactly:

ExecutionLegPlan.client_order_id
→ VenueOrderRequest.client_order_id

ExecutionLegPlan.account_id
→ VenueOrderRequest.account_id

ExecutionLegPlan.instrument_id
→ VenueOrderRequest.instrument_id

No identity regeneration, normalization or replacement is permitted.

### 75.4. SIDE CONVERSION

Canonical side conversion occurs only in this boundary:

TradeSide.BUY
→ VenueOrderSide.BUY

TradeSide.SELL
→ VenueOrderSide.SELL

Conversion MUST be explicit.

VenueAdapter implementations MUST NOT be required to understand
TradeSide.

Persistence mapping continues to store TradeSide.value as scalar text.

### 75.5. ORDER TYPE MAPPING

ExecutionLegPlan.order_type already uses canonical VenueOrderType.

Therefore mapping is direct:

ExecutionLegPlan.order_type
→ VenueOrderRequest.order_type

No new MARKET/LIMIT enum is introduced.

### 75.6. QUANTITY NUMERIC BOUNDARY

ExecutionLegPlan quantity is Decimal.

Current VenueOrderRequest quantity contract is float.

Therefore the current canonical conversion point is:

Decimal
→ float

inside ExecutionVenueRequestMapper only.

Rules:

- source Decimal must already be finite and positive;
- mapper converts only after ExecutionLegPlan validation;
- persistence mapping MUST continue preserving Decimal;
- domain ExecutionPlan remains Decimal-based.

This float conversion is an adapter-boundary compatibility step, not a
change to canonical financial precision upstream.

### 75.7. LIMIT PRICE NUMERIC BOUNDARY

ExecutionLegPlan.limit_price:

- Decimal for LIMIT;
- None for MARKET.

Current VenueOrderRequest.limit_price:

- float for LIMIT;
- None for MARKET.

Conversion:

Decimal
→ float

occurs only in ExecutionVenueRequestMapper.

Mapper MUST NOT invent or round a price.

Venue tick size / precision normalization remains downstream
venue/instrument-specific responsibility.

### 75.8. MARKET / LIMIT SEMANTICS

Mapper preserves already-validated domain semantics:

MARKET:
- limit_price = None

LIMIT:
- positive limit_price required

The mapper does not change order type based on price presence.

Invalid domain objects fail closed rather than being repaired.

### 75.9. REDUCE-ONLY MAPPING

ExecutionLegPlan.reduce_only
→ VenueOrderRequest.reduce_only

The value is preserved exactly.

Mapper MUST NOT infer reduce_only from:

- BUY/SELL direction;
- shape;
- strategy;
- source.

### 75.10. ACCOUNT / INSTRUMENT OWNERSHIP

ExecutionLegPlan already enforces:

account_id.venue_id
==
instrument_id.venue_id

Mapper preserves the same AccountId and InstrumentId instances.

No cross-venue identity rewriting occurs.

Cross-venue PAIR/BASKET execution remains represented as separate
VenueOrderRequest objects per leg.

### 75.11. ONE LEG → ONE VENUE REQUEST

Initial canonical mapping cardinality:

one ExecutionLegPlan
→ one VenueOrderRequest

ExecutionVenueRequestMapper does NOT:

- split one leg into child orders;
- batch multiple legs;
- sequence pair execution;
- coordinate partial fills;
- choose retry policy.

Those responsibilities belong to future ExecutionCoordinator /
execution-policy layers.

### 75.12. ORDER ID OWNERSHIP

ExecutionLegPlan contains both:

- order_id;
- client_order_id.

VenueOrderRequest currently carries only client_order_id.

Therefore:

- `client_order_id` crosses the venue request boundary;
- canonical internal `order_id` remains Core V2 persistence/coordinator
  identity and is not discarded from the parent ExecutionLegPlan.

The mapper MUST NOT replace client_order_id with order_id.

### 75.13. MAPPER VALIDATION

Mapper accepts only `ExecutionLegPlan`.

It MUST:

- reject non-ExecutionLegPlan input;
- call / rely on ExecutionLegPlan validation;
- fail closed on invalid side/order/numeric state.

It MUST NOT silently coerce arbitrary strings into canonical enums.

### 75.14. DEPENDENCY DIRECTION

Allowed dependency:

services.execution_venue_request_mapper
→ trading_core.execution
→ trading_core.venue

Forbidden dependency:

trading_core
→ services

Forbidden mapper dependencies:

- models;
- SQLAlchemy;
- ExecutionRepository;
- ExecutionApplicationService;
- ExecutionBoundary;
- ExecutionAgent;
- venue-specific adapters.

### 75.15. FUTURE DECIMAL VENUE CONTRACT

Current VenueOrderRequest uses float.

This design treats Decimal → float as an explicit compatibility boundary.

A future migration of VenueOrderRequest to Decimal may remove this
conversion.

Such a change is separate canonical contract scope and MUST NOT be
performed implicitly while implementing this mapper.

### 75.16. PRODUCTION SAFETY

This mapper design grants no execution permission.

It does NOT:

- instantiate or call VenueAdapter;
- submit/cancel/query exchange orders;
- call ExecutionBoundary;
- call ExecutionAgent;
- enable pair-native live execution;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production boundaries remain unchanged.

### 75.17. STATUS

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPING_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPING_DESIGN_OK`

### 75.18. PRIMARY NEXT STEP

Implement pure translation component:

`services/execution_venue_request_mapper.py`

Scope:

- ExecutionLegPlan → VenueOrderRequest;
- explicit TradeSide → VenueOrderSide;
- Decimal → float only at venue boundary;
- identity preservation;
- MARKET / LIMIT preservation;
- reduce_only preservation;
- no VenueAdapter calls;
- no coordinator integration;
- focused mapper tests.

Target evidence tag:

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPER_OK`

## 76. Trading Core V2 — Execution Venue Request Mapper — 2026-09-01

### 76.1. IMPLEMENTED

Created pure translation component:

`services/execution_venue_request_mapper.py`

Created focused tests:

`tests/test_trading_core_execution_venue_request_mapper.py`

Implemented mapping:

ExecutionLegPlan
→ VenueOrderRequest

### 76.2. SIDE MAPPING VERIFIED

Explicit conversion verified:

TradeSide.BUY
→ VenueOrderSide.BUY

TradeSide.SELL
→ VenueOrderSide.SELL

No implicit string conversion is delegated to VenueAdapter.

### 76.3. IDENTITY PRESERVATION VERIFIED

Verified exact preservation of:

- client_order_id;
- AccountId object;
- InstrumentId object.

Mapper does not regenerate or replace execution identities.

### 76.4. NUMERIC BOUNDARY VERIFIED

Verified venue-boundary conversion:

Decimal quantity
→ float quantity

Decimal LIMIT price
→ float LIMIT price

MARKET limit_price remains None.

Domain and persistence layers remain Decimal-based.

### 76.5. ORDER SEMANTICS VERIFIED

Verified preservation of:

- VenueOrderType.MARKET;
- VenueOrderType.LIMIT;
- reduce_only.

Mapper performs no order execution and no venue-specific rounding.

### 76.6. ARCHITECTURAL PURITY

ExecutionVenueRequestMapper does NOT:

- call VenueAdapter;
- submit orders;
- cancel orders;
- access AsyncSession;
- access ExecutionRepository;
- import ORM models;
- call ExecutionBoundary;
- call ExecutionAgent;
- coordinate multi-leg execution.

### 76.7. EVIDENCE

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

`python -m flake8`
→ PASS
→ `flake8_exit=0`

Focused tests:

`python -m pytest -q tests/test_trading_core_execution_venue_request_mapper.py`

Result:

`8 passed in 0.08s`

`pytest_exit=0`

Execution mapping regression:

- `tests/test_trading_core_execution.py`
- `tests/test_trading_core_execution_persistence_mapper.py`
- `tests/test_trading_core_execution_venue_request_mapper.py`

Result:

`31 passed in 0.84s`

`venue_mapping_regression_exit=0`

### 76.8. PRODUCTION SAFETY

No execution permission was added.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

No VenueAdapter submit_order path was connected.

### 76.9. STATUS

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPER — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_VENUE_REQUEST_MAPPER_OK`

### 76.10. CORRECTIVE FINDING

A design-conformance issue remains in the previously verified
ExecutionApplicationService.

Current pre-existing plan path performs:

- lookup by plan_id;
- `_verify_plan_identity(...)`;
- immediate return.

It does NOT perform full `_verify_existing_aggregate(...)` validation
on that prelookup path.

This conflicts with the approved create-or-verify aggregate semantics,
where an existing canonical identity may be reused only when the full
immutable aggregate identity is equivalent.

Therefore this is a new technical reason to reopen focused verification
of ExecutionApplicationService before further execution architecture
work.

### 76.11. PRIMARY NEXT STEP

Correct and re-verify ExecutionApplicationService pre-existing-plan
idempotency so that an existing plan cannot be accepted while its
group / legs / orders are missing or identity-conflicting.

Target corrective evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_FULL_IDEMPOTENCY_OK`

## 77. Trading Core V2 — Execution Application Service Full Idempotency Correction — 2026-09-01

### 77.1. CORRECTIVE ROOT CAUSE

Previously verified `ExecutionApplicationService` contained an
idempotency design-conformance gap.

Normal pre-existing-plan path performed:

- lookup by plan_id;
- ExecutionPlan immutable identity verification;
- immediate return.

It did NOT verify the complete existing execution aggregate.

The IntegrityError recovery path already performed full aggregate
verification.

This created inconsistent create-or-verify semantics between normal
prelookup retry and concurrent insert/race recovery.

### 77.2. CORRECTION IMPLEMENTED

Updated:

`services/execution_application_service.py`

Normal pre-existing-plan path now performs:

- `_verify_plan_identity(...)`;
- `_verify_existing_aggregate(...)`;
- returns existing plan only after complete aggregate equivalence is
  verified.

Canonical behavior is now:

existing plan
→ verify plan identity
→ verify exactly one PositionGroup
→ verify PositionGroup immutable identity
→ verify exact PositionLeg identity set
→ verify each PositionLeg immutable identity
→ verify exact ExecutionOrder identity set
→ verify each ExecutionOrder immutable identity
→ reuse existing aggregate only if equivalent.

### 77.3. FAIL-CLOSED BEHAVIOR VERIFIED

Added / updated focused regression coverage for:

- complete existing aggregate idempotent success;
- existing plan with missing PositionGroup;
- existing plan with conflicting PositionGroup.

Missing or conflicting aggregate state no longer succeeds merely because
plan_id / ExecutionPlan identity matches.

The service fails closed.

### 77.4. HAPPY-PATH FIXTURE CORRECTED

The previous `test_existing_plan_is_idempotent` fixture represented only
an existing ExecutionPlan.

After full-idempotency correction, a valid idempotent success requires
the complete aggregate to exist.

The test fixture was updated to represent:

- existing ExecutionPlan;
- matching PositionGroup;
- matching PositionLeg records;
- matching ExecutionOrder records.

No production behavior was weakened to satisfy the old fixture.

### 77.5. TRANSACTION SEMANTICS

Normal pre-existing aggregate verification performs no write transaction.

Therefore successful idempotent reuse performs:

- no commit;
- no rollback.

Fail-closed immutable identity mismatch in the prelookup path also does
not require rollback because no persistence mutation was started.

IntegrityError recovery retains the existing:

rollback
→ reread
→ full aggregate verification

behavior.

### 77.6. EVIDENCE

Syntax verification:

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

Style verification:

`python -m flake8`
→ PASS
→ `flake8_exit=0`

Focused application-service tests:

`python -m pytest -q tests/test_trading_core_execution_application_service.py`

Result:

`9 passed in 0.88s`

`focused_pytest_exit=0`

Execution persistence regression:

- `tests/test_trading_core_execution_models.py`
- `tests/test_trading_core_execution_repository.py`
- `tests/test_trading_core_execution_application_service.py`
- `tests/test_trading_core_execution_persistence_mapper.py`

Result:

`30 passed in 1.14s`

`persistence_regression_exit=0`

### 77.7. PRODUCTION SAFETY

This correction changes persistence idempotency verification only.

It does NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- submit orders;
- enable ExecutionCoordinator runtime;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production permissions remain unchanged.

### 77.8. STATUS

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_FULL_IDEMPOTENCY — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_EXECUTION_APPLICATION_SERVICE_FULL_IDEMPOTENCY_OK`

The technical reason that reopened the previously verified
ExecutionApplicationService is resolved.

### 77.9. PRIMARY NEXT STEP

Re-establish the current Trading Core V2 roadmap position from the live
Audit after this corrective branch, and identify the first unfinished
canonical roadmap item before starting additional execution runtime
work.

Target:

one canonical next implementation/design step selected from the live
Audit; no coordinator or live execution work is assumed until this
check is complete.

## 78. Trading Core V2 — Order / Position Ledger Design — 2026-09-01

### 78.1. CHECKED EXISTING LEDGER FOUNDATION

Verified existing Core V2 persistence entities:

- ExecutionPlan;
- PositionGroup;
- PositionLeg;
- ExecutionOrder;
- ExecutionFill.

Verified existing ExecutionRepository support for:

- execution order create/read/list/update;
- execution fill append/read/list;
- position-leg state mutation;
- venue-order lookup.

Existing Core V2 persistence foundation is retained.

### 78.2. LEGACY MODELS

Legacy models remain:

- SentOrder;
- TradeHistory.

SentOrder remains legacy execution idempotency/history support.

TradeHistory remains legacy finalized trade/PnL history used by existing
AI/research services.

Neither model becomes canonical Trading Core V2 Ledger authority.

They are KEEP / LEGACY and must not be deleted automatically.

### 78.3. CURRENT-STATE VS LEDGER HISTORY

Existing Core V2 models contain mutable current-state fields:

PositionGroup:
- status;
- opened_at;
- closed_at.

PositionLeg:
- target_quantity;
- filled_quantity;
- average_entry_price;
- average_exit_price;
- status.

ExecutionOrder:
- venue_order_id;
- filled_quantity;
- average_fill_price;
- status;
- rejection_reason;
- submitted_at;
- accepted_at;
- filled_at;
- cancelled_at.

These fields represent current materialized state.

They do NOT constitute an immutable historical event trail.

### 78.4. EXECUTION FILL ROLE

ExecutionFill is append-oriented execution evidence.

It provides immutable fill-level history for:

- fill_id;
- execution_order_id;
- venue_fill_id;
- quantity;
- price;
- fee;
- fee_currency;
- executed_at.

ExecutionFill is KEEP and forms part of Ledger V2.

ExecutionFill alone is insufficient for full lifecycle history because
non-fill events such as submit, accept, reject, cancel, recovery and
reconciliation discrepancy are not represented as immutable records.

### 78.5. CANONICAL LEDGER EVENT

Ledger V2 requires a new append-only lifecycle event contract.

Canonical name:

`ExecutionLedgerEvent`

Target persistence table:

`execution_ledger_events`

Purpose:

provide immutable auditable historical evidence for execution and
position lifecycle transitions.

### 78.6. EVENT IDENTITY AND LINEAGE

Each ledger event must have deterministic immutable identity and lineage.

Required fields:

- event_id;
- event_type;
- event_version;
- user_id;
- execution_plan_id;
- position_group_id nullable;
- position_leg_id nullable;
- execution_order_id nullable;
- execution_fill_id nullable;
- account_id nullable;
- venue_id nullable;
- occurred_at;
- recorded_at;
- source;
- correlation_id nullable;
- causation_id nullable;
- metadata / payload.

Event identity MUST be idempotent.

Duplicate ingestion of the same canonical event MUST fail closed or
resolve to the same event record.

### 78.7. EVENT TYPES

Initial canonical lifecycle event families:

- PLAN_CREATED;
- GROUP_CREATED;
- GROUP_STATE_CHANGED;
- LEG_CREATED;
- LEG_STATE_CHANGED;
- ORDER_CREATED;
- ORDER_SUBMITTED;
- ORDER_ACCEPTED;
- ORDER_PARTIALLY_FILLED;
- ORDER_FILLED;
- ORDER_REJECTED;
- ORDER_CANCELLED;
- FILL_RECORDED;
- RECOVERY_STARTED;
- RECOVERY_COMPLETED;
- RECONCILIATION_DISCREPANCY;
- RECONCILIATION_RESOLVED.

Exact enum implementation is deferred to implementation design/testing.

No venue-specific event type is canonical.

### 78.8. MATERIALIZED CURRENT STATE

PositionGroup / PositionLeg / ExecutionOrder remain materialized current
state.

Ledger events provide immutable history.

Canonical relationship:

append immutable event
→ validate transition
→ update materialized state in same application transaction

Current-state mutation without corresponding Ledger V2 event is not
allowed once the Ledger writer is integrated.

### 78.9. TRANSACTIONAL CONSISTENCY

For future Ledger-integrated mutations:

event append and materialized-state mutation MUST occur in the same
database transaction.

Required invariant:

if current state changes,
the corresponding immutable event must commit atomically with that
state change.

No event-only or state-only partial commit is allowed for canonical Core
V2 lifecycle transitions.

### 78.10. RESTART SAFETY

Ledger V2 is restart-safe because:

- immutable events remain persisted;
- fills remain persisted;
- materialized state can be checked against event history;
- reconciliation can determine the latest known local state;
- recovery events can describe incomplete execution lifecycle.

Restart does not infer state solely from in-memory coordinator state.

### 78.11. RECOVERY STATE

Recovery is not represented only as a mutable status string.

Canonical recovery lifecycle must be auditable through events:

RECOVERY_STARTED
→ corrective/reconciliation events
→ RECOVERY_COMPLETED

or terminal failure evidence.

PositionGroup / PositionLeg materialized status may expose current
RECOVERY state, but the event trail remains authoritative historical
evidence.

### 78.12. LOCAL / EXCHANGE STATE

Ledger V2 must distinguish:

- local materialized state;
- last known venue/exchange state;
- immutable evidence that caused local state changes.

Exchange truth is established by VenueAdapter/Reconciliation in later
Phase 3.

Ledger itself stores the resulting facts/events but does not query the
exchange.

### 78.13. MULTI-USER ISOLATION

Every canonical ledger event requires user ownership.

user_id must match the owning execution plan / position group lineage.

Cross-user lineage is invalid and must fail closed.

### 78.14. PAIR / GROUP IDENTITY

Existing PositionGroup.group_id is the current canonical grouped-trade
identity for SINGLE_LEG / PAIR / BASKET execution groups.

No separate `pair_trade_id` column is introduced at this design step.

For PAIR shape:

PositionGroup.group_id
serves as the canonical pair execution group identity.

A future dedicated PairTrade domain object may extend this only through
separate approved architecture work.

### 78.15. STRATEGY LINEAGE

Strategy lineage remains anchored at:

ExecutionPlan.intent_id
→ PositionGroup.strategy
→ PositionGroup.strategy_version
→ PositionGroup.trade_source

Ledger events referencing a group/order/leg inherit and preserve this
lineage through foreign-key ownership rather than duplicating mutable
strategy fields into every event unless required for immutable payload
evidence.

### 78.16. REPOSITORY OWNERSHIP

ExecutionRepository remains persistence-only and flush-only.

Ledger support should extend it with append/read methods for
ExecutionLedgerEvent.

Repository MUST NOT:

- commit;
- rollback;
- reconcile exchange state;
- coordinate execution;
- infer lifecycle transitions.

Application/service layer owns transaction and lifecycle rules.

### 78.17. EVENT APPEND RULE

ExecutionLedgerEvent is append-only.

Canonical repository operations:

- add_ledger_event;
- get_ledger_event_by_event_id;
- list_ledger_events_for_plan;
- list_ledger_events_for_group;
- list_ledger_events_for_leg;
- list_ledger_events_for_order.

No generic update/delete lifecycle method is allowed for canonical
events.

Historical events are never rewritten to reflect newer state.

### 78.18. RECONCILIATION BOUNDARY

Phase 3 Reconciliation will consume:

- current local materialized state;
- execution orders;
- fills;
- immutable ledger events;
- actual venue state.

Reconciliation may append discrepancy/recovery events.

It must not destructively rewrite historical ledger evidence.

### 78.19. STATUS

`TRADING_CORE_V2_LEDGER_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_DESIGN_OK`

### 78.20. PRIMARY NEXT STEP

Design the additive persistence contract and migration for:

`execution_ledger_events`

Scope:

- columns;
- foreign keys;
- unique deterministic event_id;
- indexes;
- append-only semantics;
- user/plan/group/leg/order/fill lineage;
- payload representation;
- no runtime writer integration yet;
- no reconciliation implementation yet;
- no coordinator integration.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_PERSISTENCE_DESIGN_OK`

## 79. Trading Core V2 — Ledger Event Persistence Design — 2026-09-01

### 79.1. CURRENT SCHEMA BASELINE

Verified current Alembic head:

`aa3c49db572a`

Any additive Ledger V2 migration must use:

`down_revision = "aa3c49db572a"`

unless the Alembic head changes before migration creation.

### 79.2. TARGET TABLE

New additive table:

`execution_ledger_events`

Purpose:

immutable append-only lifecycle history for Trading Core V2 execution,
position, recovery and reconciliation facts.

This table supplements existing current-state tables.

It does not replace:

- execution_plans;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills.

### 79.3. PRIMARY KEY AND EVENT IDENTITY

Columns:

- `id` Integer primary key;
- `event_id` String(160), NOT NULL;
- unique constraint on event_id.

Constraint:

`uq_execution_ledger_events_event_id`

`event_id` is the canonical deterministic idempotency identity.

No random event ID generation occurs inside the persistence model.

### 79.4. EVENT CLASSIFICATION

Columns:

- `event_type` String(60), NOT NULL;
- `event_version` Integer, NOT NULL, server default `1`;
- `source` String(80), NOT NULL.

event_type remains scalar persistence text.

Canonical domain enum is defined separately at implementation-contract
stage.

event_version supports future payload evolution without rewriting
historical rows.

### 79.5. OWNERSHIP

Required:

- `user_id` Integer, FK `users.id`, NOT NULL.

Index:

`ix_execution_ledger_events_user_id`

Every canonical ledger event is user-owned.

Cross-user lineage validation belongs to application/domain validation,
not to implicit database inference.

### 79.6. EXECUTION PLAN LINEAGE

Required:

- `execution_plan_id` Integer,
  FK `execution_plans.id`,
  NOT NULL.

Index:

`ix_execution_ledger_events_execution_plan_id`

Every canonical Core V2 ledger event belongs to one execution plan.

### 79.7. OPTIONAL AGGREGATE LINEAGE

Nullable foreign keys:

- `position_group_id`
  → `position_groups.id`;

- `position_leg_id`
  → `position_legs.id`;

- `execution_order_id`
  → `execution_orders.id`;

- `execution_fill_id`
  → `execution_fills.id`;

- `account_id`
  → `exchanges.id`.

Each receives an explicit index.

These fields allow plan-level, group-level, leg-level, order-level,
fill-level and account-level event queries.

Nullable means an event may exist at a higher lifecycle level.

### 79.8. VENUE IDENTITY

Nullable:

- `venue_id` String(80).

Index:

`ix_execution_ledger_events_venue_id`

venue_id is stored explicitly for audit/query convenience and
multi-venue reconciliation evidence.

Application validation must ensure venue/account lineage consistency
where both are present.

### 79.9. CORRELATION / CAUSATION

Nullable:

- `correlation_id` String(160);
- `causation_id` String(160).

Indexes:

- `ix_execution_ledger_events_correlation_id`;
- `ix_execution_ledger_events_causation_id`.

Purpose:

- correlation_id groups one logical execution/recovery workflow;
- causation_id references the deterministic identity of the event or
  command that caused this event.

No FK is introduced because causation may originate outside the local
ledger event table.

### 79.10. EVENT TIME

Required:

- `occurred_at` DateTime, NOT NULL;
- `recorded_at` DateTime, NOT NULL,
  `server_default=func.now()`.

Index:

`ix_execution_ledger_events_occurred_at`

Meaning:

- occurred_at = when the represented fact happened;
- recorded_at = when NEXUS persisted the fact.

These timestamps must not be conflated.

### 79.11. PAYLOAD

Required:

- `payload` PostgreSQL JSONB, NOT NULL.

Server default:

`'{}'::jsonb`

Reason:

- PostgreSQL is canonical current production database;
- project already uses JSONB extensively;
- event payloads require structured extensible evidence;
- future event versions may add fields without schema rewrite.

Payload MUST remain JSON-serializable structured data.

It must not contain Python-specific serialized objects.

### 79.12. PAYLOAD RESPONSIBILITY

Payload stores event-specific immutable evidence only.

Core identity and lineage fields MUST remain first-class columns and
must not exist only inside JSONB.

Examples of payload data:

- previous_status;
- new_status;
- venue response state;
- discrepancy details;
- recovery reason;
- quantity/price evidence;
- rejection details.

Canonical required identifiers remain relational columns.

### 79.13. APPEND-ONLY SEMANTICS

`execution_ledger_events` is append-only.

Application/repository rules:

- INSERT allowed;
- SELECT allowed;
- UPDATE lifecycle API forbidden;
- DELETE lifecycle API forbidden.

No generic repository update/delete methods are created.

Historical corrections are represented as new corrective events.

Database-level immutable triggers are NOT introduced at this design
stage.

Enforcement begins at repository/application contract level.

### 79.14. UNIQUE / IDEMPOTENCY CONTRACT

Required unique:

`event_id`

No second unique constraint is introduced on correlation/causation
because multiple valid events may share them.

Replay/reconciliation ingestion rules must:

- lookup by event_id;
- reuse exact event identity if equivalent;
- fail closed on immutable identity conflict.

### 79.15. INDEXES

Required indexes:

- user_id;
- execution_plan_id;
- position_group_id;
- position_leg_id;
- execution_order_id;
- execution_fill_id;
- account_id;
- venue_id;
- event_type;
- occurred_at;
- correlation_id;
- causation_id.

No premature composite indexes are required at this stage.

Composite indexes should be added only from demonstrated query/runtime
evidence.

### 79.16. FOREIGN KEY POLICY

Foreign-key style follows existing Core V2 persistence:

plain SQLAlchemy ForeignKey references.

No automatic ON DELETE CASCADE is introduced.

Reason:

Ledger history must not disappear automatically if another record is
deleted.

Historical records are never automatically deleted.

### 79.17. ORM MODEL

Target ORM model:

`models/execution_ledger_event.py`

Class:

`ExecutionLedgerEvent`

Model responsibilities:

- table/schema definition;
- no lifecycle behavior;
- no event generation;
- no exchange access;
- no transaction ownership.

Export later through `models/__init__.py`.

### 79.18. MIGRATION

Target additive Alembic migration:

create `execution_ledger_events`

with:

- all columns defined above;
- foreign keys;
- unique event_id;
- explicit indexes;
- JSONB payload.

Migration downgrade may drop only the newly created table/indexes.

It MUST NOT modify or delete existing Core V2 execution tables.

### 79.19. REPOSITORY FOLLOW-UP

After schema/model verification, extend ExecutionRepository with
append/read-only ledger methods.

Initial methods:

- add_ledger_event;
- get_ledger_event_by_event_id;
- list_ledger_events_for_plan;
- list_ledger_events_for_group;
- list_ledger_events_for_leg;
- list_ledger_events_for_order.

No generic update/delete event methods.

### 79.20. PRODUCTION SAFETY

This persistence design adds no runtime execution behavior.

It does NOT:

- query venue state;
- reconcile exchange state;
- submit orders;
- call ExecutionBoundary;
- call VenueAdapter;
- start ExecutionCoordinator;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production permissions remain unchanged.

### 79.21. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_PERSISTENCE_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_PERSISTENCE_DESIGN_OK`

### 79.22. PRIMARY NEXT STEP

Implement and verify the additive Alembic migration for:

`execution_ledger_events`

Scope:

- migration file only;
- current head as down_revision;
- PostgreSQL JSONB payload;
- exact FK/unique/index contract;
- offline SQL verification;
- py_compile;
- flake8;
- alembic heads verification;
- no DB apply until migration file is verified.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_MIGRATION_FILE_OK`

## 80. Trading Core V2 — Ledger Event Migration File — 2026-09-01

### 80.1. IMPLEMENTED

Created additive Alembic migration:

`migrations/versions/c6e91f7a2b34_add_execution_ledger_events.py`

Revision:

`c6e91f7a2b34`

Down revision:

`aa3c49db572a`

### 80.2. TARGET TABLE VERIFIED

Migration creates:

`execution_ledger_events`

with canonical columns for:

- deterministic event identity;
- event type/version;
- user ownership;
- execution plan lineage;
- optional group/leg/order/fill/account lineage;
- venue identity;
- source;
- correlation / causation;
- occurred_at;
- recorded_at;
- JSONB payload.

### 80.3. UNIQUE CONSTRAINT VERIFIED

Verified:

`uq_execution_ledger_events_event_id`

on:

`event_id`

This provides deterministic event-level idempotency identity.

### 80.4. FOREIGN KEYS VERIFIED

Offline SQL confirms foreign keys to:

- users;
- execution_plans;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills;
- exchanges.

No ON DELETE CASCADE was introduced.

### 80.5. INDEXES VERIFIED

Verified indexes:

- ix_execution_ledger_events_user_id;
- ix_execution_ledger_events_execution_plan_id;
- ix_execution_ledger_events_position_group_id;
- ix_execution_ledger_events_position_leg_id;
- ix_execution_ledger_events_execution_order_id;
- ix_execution_ledger_events_execution_fill_id;
- ix_execution_ledger_events_account_id;
- ix_execution_ledger_events_venue_id;
- ix_execution_ledger_events_event_type;
- ix_execution_ledger_events_occurred_at;
- ix_execution_ledger_events_correlation_id;
- ix_execution_ledger_events_causation_id.

### 80.6. JSONB PAYLOAD VERIFIED

Verified PostgreSQL JSONB payload:

`payload JSONB DEFAULT '{}'::jsonb NOT NULL`

This matches existing project structured-evidence conventions.

### 80.7. ALEMBIC CHAIN VERIFIED

Alembic heads output:

`c6e91f7a2b34 (head)`

Migration chain:

`aa3c49db572a`
→ `c6e91f7a2b34`

No migration branch conflict was introduced.

### 80.8. OFFLINE SQL VERIFIED

Command:

`alembic upgrade c6e91f7a2b34 --sql`

Result:

`offline_sql_exit=0`

Offline SQL explicitly contains:

`CREATE TABLE execution_ledger_events`

plus required unique constraint, foreign keys and indexes.

### 80.9. STATIC VERIFICATION

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

`python -m flake8`
→ PASS
→ `flake8_exit=0`

`alembic heads`
→ PASS
→ `heads_exit=0`

### 80.10. DATABASE STATE

Migration file is VERIFIED.

Database migration has NOT yet been applied in this step.

No runtime Ledger writer integration has been enabled.

### 80.11. PRODUCTION SAFETY

No execution behavior changed.

This migration file does NOT:

- query venue state;
- reconcile exchange state;
- submit orders;
- call VenueAdapter;
- call ExecutionBoundary;
- start ExecutionCoordinator;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production permissions remain unchanged.

### 80.12. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_MIGRATION_FILE — TEST/STRUCTURE VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_MIGRATION_FILE_OK`

### 80.13. PRIMARY NEXT STEP

Perform pre-apply database verification for the new Ledger event
migration.

Scope:

- confirm current DB revision is exactly `aa3c49db572a`;
- confirm `execution_ledger_events` is absent;
- create schema-only backup;
- record backup exit/status;
- do NOT apply migration until these checks are verified.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_PREAPPLY_CHECK_OK`

## 81. Trading Core V2 — Ledger Event Pre-Apply Check — 2026-09-01

### 81.1. DATABASE REVISION VERIFIED

Verified current live database Alembic revision:

`aa3c49db572a`

This matches the required down_revision for the new Ledger event
migration:

`c6e91f7a2b34`

### 81.2. TARGET TABLE ABSENCE VERIFIED

Checked:

`public.execution_ledger_events`

Result:

ABSENT.

No pre-existing target table or schema divergence was detected.

### 81.3. PRE-APPLY SCHEMA BACKUP VERIFIED

Created schema-only backup:

`/tmp/nexus_schema_before_ledger_events.sql`

Result:

`backup_exit=0`

Backup size:

`126K`

Backup content verification confirmed existing Core V2 schema including:

`public.execution_plans`

Target `execution_ledger_events` was absent from the pre-apply schema
backup.

### 81.4. PRE-APPLY INVARIANTS

Verified:

- DB revision matches expected migration baseline;
- target table is absent;
- schema-only backup exists;
- backup command completed successfully;
- existing Core V2 schema is present in backup.

### 81.5. PRODUCTION SAFETY

No schema migration was applied during this check.

No execution/runtime behavior changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 81.6. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_PREAPPLY_CHECK — VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_PREAPPLY_CHECK_OK`

### 81.7. PRIMARY NEXT STEP

Apply exactly:

`alembic upgrade c6e91f7a2b34`

Then verify:

- DB current revision;
- execution_ledger_events existence;
- columns;
- foreign keys;
- unique constraint;
- indexes;
- JSONB payload;
- no unexpected adjacent schema changes.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_SCHEMA_OK`

## 82. Trading Core V2 — Ledger Event Schema Apply — 2026-09-01

### 82.1. MIGRATION APPLIED

Applied exactly:

`alembic upgrade c6e91f7a2b34`

Alembic reported:

`Running upgrade aa3c49db572a -> c6e91f7a2b34, add execution ledger events`

### 82.2. DATABASE REVISION VERIFIED

Current DB revision after apply:

`c6e91f7a2b34 (head)`

The live database now matches the current Ledger event migration head.

### 82.3. TARGET TABLE VERIFIED

Verified table exists:

`public.execution_ledger_events`

### 82.4. COLUMNS VERIFIED

Verified columns and types:

- id Integer primary key;
- event_id String(160) NOT NULL;
- event_type String(60) NOT NULL;
- event_version Integer NOT NULL DEFAULT 1;
- user_id Integer NOT NULL;
- execution_plan_id Integer NOT NULL;
- position_group_id Integer nullable;
- position_leg_id Integer nullable;
- execution_order_id Integer nullable;
- execution_fill_id Integer nullable;
- account_id Integer nullable;
- venue_id String(80) nullable;
- source String(80) NOT NULL;
- correlation_id String(160) nullable;
- causation_id String(160) nullable;
- occurred_at timestamp NOT NULL;
- recorded_at timestamp NOT NULL DEFAULT now();
- payload JSONB NOT NULL DEFAULT '{}'::jsonb.

### 82.5. UNIQUE CONSTRAINT VERIFIED

Verified:

`uq_execution_ledger_events_event_id`

on:

`event_id`

### 82.6. FOREIGN KEYS VERIFIED

Verified foreign keys:

- user_id → users.id;
- execution_plan_id → execution_plans.id;
- position_group_id → position_groups.id;
- position_leg_id → position_legs.id;
- execution_order_id → execution_orders.id;
- execution_fill_id → execution_fills.id;
- account_id → exchanges.id.

No ON DELETE CASCADE is present.

### 82.7. INDEXES VERIFIED

Verified:

- execution_ledger_events_pkey;
- ix_execution_ledger_events_account_id;
- ix_execution_ledger_events_causation_id;
- ix_execution_ledger_events_correlation_id;
- ix_execution_ledger_events_event_type;
- ix_execution_ledger_events_execution_fill_id;
- ix_execution_ledger_events_execution_order_id;
- ix_execution_ledger_events_execution_plan_id;
- ix_execution_ledger_events_occurred_at;
- ix_execution_ledger_events_position_group_id;
- ix_execution_ledger_events_position_leg_id;
- ix_execution_ledger_events_user_id;
- ix_execution_ledger_events_venue_id;
- uq_execution_ledger_events_event_id.

### 82.8. JSONB VERIFIED

Verified:

`payload jsonb NOT NULL DEFAULT '{}'::jsonb`

The applied schema matches the canonical persistence design.

### 82.9. ADJACENT SCHEMA SAFETY

The migration was additive.

Existing Core V2 execution tables remain referenced through foreign keys.

No existing execution table was dropped or replaced.

### 82.10. PRODUCTION SAFETY

Schema persistence only was changed.

No runtime Ledger writer was enabled.

No execution coordinator was started.

No VenueAdapter / ExecutionBoundary invocation path was changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 82.11. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_SCHEMA — TEST/SCHEMA VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_SCHEMA_OK`

### 82.12. PRIMARY NEXT STEP

Implement and verify the ORM model:

`models/execution_ledger_event.py`

Requirements:

- exact parity with applied schema;
- JSONB payload;
- all FK/index/unique definitions;
- export through models/__init__.py;
- focused structure tests;
- py_compile;
- flake8;
- no repository/runtime writer integration yet.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_MODEL_OK`

## 83. Trading Core V2 — Ledger Event ORM Model — 2026-09-01

### 83.1. IMPLEMENTED

Created:

`models/execution_ledger_event.py`

Class:

`ExecutionLedgerEvent`

Table:

`execution_ledger_events`

### 83.2. SCHEMA PARITY

ORM model matches the applied Ledger event schema.

Verified fields include:

- id;
- event_id;
- event_type;
- event_version;
- user_id;
- execution_plan_id;
- position_group_id;
- position_leg_id;
- execution_order_id;
- execution_fill_id;
- account_id;
- venue_id;
- source;
- correlation_id;
- causation_id;
- occurred_at;
- recorded_at;
- payload.

### 83.3. FOREIGN KEYS

Verified ORM foreign keys:

- user_id → users.id;
- execution_plan_id → execution_plans.id;
- position_group_id → position_groups.id;
- position_leg_id → position_legs.id;
- execution_order_id → execution_orders.id;
- execution_fill_id → execution_fills.id;
- account_id → exchanges.id.

### 83.4. UNIQUE / INDEX CONTRACT

Verified unique constraint:

`uq_execution_ledger_events_event_id`

Verified Ledger indexes through ORM metadata for:

- user_id;
- execution_plan_id;
- position_group_id;
- position_leg_id;
- execution_order_id;
- execution_fill_id;
- account_id;
- venue_id;
- event_type;
- occurred_at;
- correlation_id;
- causation_id.

### 83.5. JSONB

Verified:

`payload`

uses PostgreSQL:

`JSONB`

with non-null persistence contract and empty-object server default.

### 83.6. MODEL EXPORT

Verified export through:

`models/__init__.py`

Import:

`from models.execution_ledger_event import ExecutionLedgerEvent`

Export:

`"ExecutionLedgerEvent"`

Runtime import contract verified:

`from models import ExecutionLedgerEvent`

Result:

`execution_ledger_events`

`import_contract_exit=0`

### 83.7. STATIC VERIFICATION

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

`python -m flake8`
→ PASS
→ `flake8_exit=0`

### 83.8. TEST VERIFICATION

Focused model tests:

`10 passed`

Core V2 model regression:

`16 passed`

No regression detected in the existing Core V2 persistence model suite.

### 83.9. PRODUCTION SAFETY

This step added ORM representation only.

No Ledger runtime writer was enabled.

No exchange reconciliation was implemented.

No execution coordinator was started.

No VenueAdapter / ExecutionBoundary call path changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 83.10. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_MODEL — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_MODEL_OK`

### 83.11. PRIMARY NEXT STEP

Extend and verify `ExecutionRepository` with append/read-only Ledger event
persistence methods.

Required initial methods:

- add_ledger_event;
- get_ledger_event_by_event_id;
- list_ledger_events_for_plan;
- list_ledger_events_for_group;
- list_ledger_events_for_leg;
- list_ledger_events_for_order.

Constraints:

- repository remains persistence-only;
- flush only;
- no commit;
- no rollback;
- no update/delete Ledger event methods;
- no lifecycle transition inference;
- no reconciliation;
- no venue calls;
- no coordinator integration.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_REPOSITORY_OK`

## 84. Trading Core V2 — Ledger Event Repository — 2026-09-01

### 84.1. IMPLEMENTED

Extended:

`services/execution_repository.py`

with append/read-only Ledger event persistence methods:

- add_ledger_event;
- get_ledger_event_by_event_id;
- list_ledger_events_for_plan;
- list_ledger_events_for_group;
- list_ledger_events_for_leg;
- list_ledger_events_for_order.

### 84.2. APPEND CONTRACT

`add_ledger_event`:

- adds ExecutionLedgerEvent to the AsyncSession;
- flushes;
- returns the persisted ORM object;
- does not commit;
- does not rollback.

Transaction ownership remains with the caller.

### 84.3. READ CONTRACT

Verified read support by:

- canonical event_id;
- execution plan;
- position group;
- position leg;
- execution order.

List methods return deterministic event ordering:

`occurred_at ASC`
then
`id ASC`

This preserves chronological ordering with a stable tie-breaker.

### 84.4. APPEND-ONLY GUARANTEE

No Ledger event mutation API was added.

Confirmed absent:

- update_ledger_event;
- delete_ledger_event;
- remove_ledger_event.

Historical corrections must be represented by new immutable events.

### 84.5. TRANSACTION BOUNDARY

ExecutionRepository remains persistence-only and flush-only.

Source guard confirmed no:

- `.commit(`;
- `.rollback(`.

Repository does not own application transactions.

### 84.6. RUNTIME BOUNDARY

ExecutionRepository remains free of runtime execution dependencies.

No Ledger repository method:

- calls ExecutionAgent;
- calls PositionAgent;
- calls ExecutionBoundary;
- calls VenueAdapter;
- calls Orchestrator;
- reconciles venue state;
- infers lifecycle transitions.

### 84.7. STATIC VERIFICATION

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

`python -m flake8`
→ PASS
→ `flake8_exit=0`

### 84.8. TEST VERIFICATION

Focused repository suite:

`14 passed`

Result:

`focused_pytest_exit=0`

Persistence regression suite:

`30 passed`

Result:

`persistence_regression_exit=0`

No regression detected in existing Core V2 persistence/model/repository
behavior.

### 84.9. PRODUCTION SAFETY

This step adds persistence access only.

No runtime Ledger writer has been integrated into execution use cases.

No Reconciliation Engine was implemented.

No Execution Coordinator was started.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 84.10. STATUS

`TRADING_CORE_V2_LEDGER_EVENT_REPOSITORY — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_EVENT_REPOSITORY_OK`

### 84.11. PRIMARY NEXT STEP

Design the Ledger application-service contract that atomically combines:

- immutable Ledger event append;
- corresponding materialized current-state mutation;
- caller-owned transaction;
- idempotent event identity handling;
- fail-closed immutable identity conflicts.

No runtime exchange/reconciliation/coordinator integration yet.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_APPLICATION_SERVICE_DESIGN_OK`

## 85. Trading Core V2 — Ledger Application Service Design — 2026-09-01

### 85.1. EXISTING APPLICATION BOUNDARY VERIFIED

Verified existing:

`services/execution_application_service.py`

Class:

`ExecutionApplicationService`

This service already owns application-level transaction semantics for
Trading Core V2 execution persistence.

Verified behavior:

- caller supplies AsyncSession;
- service performs commit on successful aggregate creation;
- service performs rollback on IntegrityError;
- service performs rollback on other exceptions;
- repository remains flush-only;
- existing aggregate path performs full immutable identity verification;
- IntegrityError retry path performs rollback before reread;
- service has no VenueAdapter / ExecutionBoundary / exchange-order calls.

### 85.2. ARCHITECTURAL DECISION

Ledger application semantics will EXTEND:

`ExecutionApplicationService`

No separate `LedgerApplicationService` is introduced at this stage.

Reason:

a second application service owning commits/rollbacks for the same
execution aggregate would duplicate transaction ownership and create
ambiguous lifecycle authority.

Canonical ownership remains:

`ExecutionApplicationService`
→ application transaction ownership

`ExecutionRepository`
→ persistence-only / flush-only

### 85.3. LEDGER WRITE RESPONSIBILITY

ExecutionApplicationService will become the canonical application
boundary for Ledger-integrated materialized-state transitions.

Required invariant:

materialized state mutation
+
immutable ExecutionLedgerEvent append
+
single commit

must occur inside one application transaction.

If either state mutation or event append fails:

the whole use case must rollback.

### 85.4. INITIAL LEDGER USE CASE CONTRACT

Initial implementation target:

a dedicated state-transition use case inside
`ExecutionApplicationService`.

Canonical method family:

`apply_order_state_transition(...)`

Exact final method signature may be refined during implementation CHECK,
but it must receive explicit transition facts rather than infer them
from exchange state.

Inputs must include sufficient immutable evidence for:

- event_id;
- execution_order identity;
- target materialized order state;
- event_type;
- occurred_at;
- source;
- payload;
- optional venue_order_id;
- optional filled_quantity;
- optional average_fill_price;
- optional rejection_reason;
- optional lifecycle timestamps;
- optional correlation_id;
- optional causation_id.

No VenueAdapter object is accepted.

### 85.5. ORDER-FIRST INITIAL SCOPE

Initial Ledger application integration is intentionally limited to:

`ExecutionOrder`

Reason:

- ExecutionOrder already has a defined mutable lifecycle state;
- repository already exposes update_execution_order_state;
- immutable Ledger event lineage supports execution_order_id;
- order lifecycle is the first dependency needed by future
  reconciliation/coordinator work.

Group/leg/materialized-state Ledger transitions remain follow-up work.

This is an incremental migration, not a clean-sheet lifecycle rewrite.

### 85.6. EVENT IDENTITY / IDEMPOTENCY

Before appending a Ledger event:

service must lookup:

`get_ledger_event_by_event_id(event_id)`

If event_id does not exist:

- validate request/lineage;
- append event;
- mutate corresponding materialized state;
- commit once.

If event_id already exists:

service must verify immutable event identity.

Equivalent event:

- treated as idempotent replay;
- no duplicate event append;
- no second state mutation;
- no second commit required for already completed canonical transition.

Conflicting immutable identity:

- fail closed;
- raise;
- do not mutate materialized state.

### 85.7. IMMUTABLE EVENT IDENTITY

At minimum, replay verification must compare:

- event_id;
- event_type;
- event_version;
- user_id;
- execution_plan_id;
- execution_order_id;
- account_id where present;
- venue_id where present;
- source;
- occurred_at;
- correlation_id;
- causation_id;
- payload.

A reused event_id with different immutable evidence is invalid.

### 85.8. LINEAGE VALIDATION

Before state mutation:

ExecutionOrder must exist.

Service must validate that Ledger request lineage matches the persisted
order:

- execution_plan_id;
- account_id;
- venue_id.

The owning ExecutionPlan user_id must match Ledger event user_id.

If lineage cannot be proven:

fail closed.

No cross-user or cross-plan transition is allowed.

### 85.9. EVENT / STATE CONSISTENCY

The requested event_type and materialized state transition must be
explicitly compatible.

Initial canonical order event families:

- ORDER_CREATED;
- ORDER_SUBMITTED;
- ORDER_ACCEPTED;
- ORDER_PARTIALLY_FILLED;
- ORDER_FILLED;
- ORDER_REJECTED;
- ORDER_CANCELLED.

The service must not silently infer event_type from arbitrary status
strings.

Transition validation belongs to application/domain policy, not the
repository.

### 85.10. TRANSACTION ORDER

Canonical new-event transaction sequence:

1. validate request;
2. check event_id;
3. load and verify ExecutionOrder lineage;
4. construct immutable ExecutionLedgerEvent;
5. append event through ExecutionRepository;
6. mutate ExecutionOrder materialized state through ExecutionRepository;
7. commit once;
8. refresh/return resulting state if required.

Both repository calls only flush.

Any failure before commit rolls back the full transaction.

### 85.11. INTEGRITYERROR RACE HANDLING

Unique event_id may race under concurrent writers.

Required behavior:

- catch IntegrityError;
- rollback first;
- reread event by event_id;
- if absent, re-raise;
- if present, verify full immutable event identity;
- if equivalent, treat as idempotent replay;
- if conflicting, fail closed.

This follows the already verified aggregate create-or-verify pattern.

### 85.12. EXISTING AGGREGATE CREATE PATH

Existing:

`create_or_verify_aggregate(...)`

must remain behaviorally unchanged by initial Ledger transition work.

No automatic Ledger backfill is introduced into aggregate creation in
the first implementation step.

Reason:

backfilling PLAN_CREATED / GROUP_CREATED / LEG_CREATED / ORDER_CREATED
into already-running aggregate creation changes transaction semantics
and requires separate explicit implementation/testing.

### 85.13. REPOSITORY BOUNDARY

ExecutionRepository remains unchanged in ownership:

- no commit;
- no rollback;
- no lifecycle inference;
- no reconciliation;
- no venue calls.

Existing methods reused:

- get_execution_order_by_order_id;
- update_execution_order_state;
- add_ledger_event;
- get_ledger_event_by_event_id.

Additional read methods may be added only if implementation evidence
shows a concrete need.

### 85.14. NO EVENT UPDATE / DELETE

Application service must never correct Ledger history by modifying an
existing ExecutionLedgerEvent.

Corrections require a new deterministic event.

No update/delete Ledger event API is introduced.

### 85.15. RECONCILIATION BOUNDARY

This design does not implement Reconciliation.

Future Reconciliation Engine may invoke the same canonical application
transition boundary with explicit discrepancy/recovery evidence.

Reconciliation itself remains responsible for comparing local and venue
state.

Ledger application service remains responsible only for safely
persisting validated state transitions and immutable evidence.

### 85.16. COORDINATOR BOUNDARY

ExecutionCoordinator is not implemented here.

Future coordinator code must not mutate ExecutionOrder state directly
once canonical Ledger-integrated transition APIs are active.

It should submit explicit transition commands/facts through the
application boundary.

### 85.17. PRODUCTION SAFETY

This design does not enable runtime execution.

It does NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- submit orders;
- reconcile venue state;
- start ExecutionCoordinator;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production permissions remain unchanged.

### 85.18. STATUS

`TRADING_CORE_V2_LEDGER_APPLICATION_SERVICE_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_APPLICATION_SERVICE_DESIGN_OK`

### 85.19. PRIMARY NEXT STEP

Implement and verify the initial Ledger-integrated ExecutionOrder state
transition use case inside:

`ExecutionApplicationService`

Scope:

- explicit immutable transition request contract;
- event_id idempotency;
- full immutable replay verification;
- ExecutionOrder lineage validation;
- atomic Ledger append + materialized order-state mutation;
- one commit on new successful transition;
- rollback on failure;
- IntegrityError rollback → reread → verify;
- focused tests;
- existing ExecutionApplicationService regression;
- no aggregate-create Ledger backfill yet;
- no venue/reconciliation/coordinator integration.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_ORDER_TRANSITION_APPLICATION_OK`

## 86. Trading Core V2 — Ledger Order Transition Application — 2026-09-01

### 86.1. IMPLEMENTED

Extended:

`services/execution_application_service.py`

with the initial canonical Ledger-integrated ExecutionOrder transition
use case.

Added immutable request contract:

`ExecutionOrderTransition`

Added application method:

`apply_order_state_transition(...)`

Existing:

`create_or_verify_aggregate(...)`

remains behaviorally separate and unchanged in responsibility.

### 86.2. CANONICAL TRANSACTION CONTRACT

For a new order lifecycle transition the application service performs:

1. transition request validation;
2. ExecutionPlan ownership validation;
3. deterministic Ledger event_id lookup;
4. ExecutionOrder lookup;
5. order / plan / account / venue lineage validation;
6. immutable ExecutionLedgerEvent construction;
7. Ledger event append through ExecutionRepository;
8. ExecutionOrder materialized-state mutation through ExecutionRepository;
9. one application-level commit;
10. refresh and return.

Ledger append and materialized state mutation therefore participate in
the same caller-supplied AsyncSession transaction.

### 86.3. TRANSACTION OWNERSHIP

ExecutionApplicationService remains the transaction owner.

ExecutionRepository remains flush-only.

Successful new transition:

- one commit.

Failure before commit:

- rollback.

No transaction ownership was moved into the repository.

### 86.4. EVENT / STATE COMPATIBILITY

Initial supported canonical order lifecycle mappings are explicit:

- ORDER_CREATED → PENDING;
- ORDER_SUBMITTED → SUBMITTED;
- ORDER_ACCEPTED → ACCEPTED;
- ORDER_PARTIALLY_FILLED → PARTIALLY_FILLED;
- ORDER_FILLED → FILLED;
- ORDER_REJECTED → REJECTED;
- ORDER_CANCELLED → CANCELLED.

Unsupported event types fail closed.

event_type / target_status mismatch fails closed before persistence.

The service does not silently infer event type from arbitrary status
strings.

### 86.5. OWNERSHIP VALIDATION

ExecutionOrder does not directly contain user_id.

Canonical ownership is therefore proven through:

ExecutionOrder.execution_plan_id
→ ExecutionPlan.id
→ ExecutionPlan.user_id.

The service loads the owning ExecutionPlan and requires:

`ExecutionPlan.user_id == request.user_id`

Mismatch fails closed.

This closes the cross-user Ledger evidence gap identified during
implementation verification.

### 86.6. ORDER LINEAGE VALIDATION

Before mutation, the service verifies:

- ExecutionOrder exists;
- order.execution_plan_id matches request.execution_plan_id;
- account_id matches when explicitly supplied;
- venue_id matches when explicitly supplied.

Unproven or conflicting lineage fails closed.

### 86.7. IDEMPOTENT REPLAY

The service checks deterministic:

`event_id`

before creating a new event.

If an equivalent event already exists:

- no duplicate Ledger event is appended;
- no second ExecutionOrder mutation occurs;
- no second commit occurs;
- existing materialized order is returned after lineage verification.

### 86.8. IMMUTABLE REPLAY VERIFICATION

Existing Ledger event replay verification includes:

- event_id;
- event_type;
- event_version;
- user_id;
- execution_plan_id;
- execution_order_id;
- account_id;
- venue_id;
- source;
- occurred_at;
- correlation_id;
- causation_id;
- payload.

A reused event_id with conflicting immutable evidence fails closed.

execution_order_id is explicitly included so one event identity cannot
be replayed against a different order.

### 86.9. INTEGRITYERROR RACE HANDLING

Concurrent deterministic event insertion is handled using:

IntegrityError
→ rollback
→ reread event_id
→ reread ExecutionOrder
→ verify order lineage
→ verify full immutable event identity.

If the event does not exist after rollback:

the original IntegrityError is re-raised.

Equivalent race result is treated as idempotent replay.

Conflicting event identity fails closed.

### 86.10. FAILURE HANDLING

Generic transition persistence failure:

- rolls back;
- does not commit;
- propagates the exception.

Focused test verifies failure of the materialized state write after
Ledger append causes application rollback.

### 86.11. MATERIALIZED STATE FIELDS

Initial transition contract supports explicit updates for:

- status;
- venue_order_id;
- filled_quantity;
- average_fill_price;
- rejection_reason;
- submitted_at;
- accepted_at;
- filled_at;
- cancelled_at.

No exchange state is queried or inferred by this service.

### 86.12. TEST VERIFICATION

Focused Ledger order-transition suite:

`8 passed`

Result:

`ledger_transition_exit=0`

Coverage includes:

- successful new transition / one commit;
- equivalent replay / no mutation and no commit;
- immutable event conflict fail closed;
- user ownership conflict fail closed;
- execution-plan lineage conflict fail closed;
- event/status mismatch fail closed;
- IntegrityError rollback → reread → replay verification;
- generic transition failure rollback.

### 86.13. APPLICATION REGRESSION

Existing ExecutionApplicationService plus Ledger transition tests:

`17 passed`

Result:

`application_regression_exit=0`

No regression detected in existing aggregate create-or-verify
semantics.

### 86.14. CORE V2 REGRESSION

Combined persistence/application scope:

`47 passed`

Result:

`core_v2_regression_exit=0`

Covered:

- existing execution persistence models;
- ExecutionLedgerEvent model;
- ExecutionRepository;
- existing ExecutionApplicationService;
- Ledger order-transition application use case.

### 86.15. STATIC VERIFICATION

`python -m py_compile`
→ PASS
→ `py_compile_exit=0`

`python -m flake8`
→ PASS
→ `flake8_exit=0`

### 86.16. CURRENT LIMITS

This initial integration is intentionally order-first.

Not yet integrated:

- PositionGroup Ledger transitions;
- PositionLeg Ledger transitions;
- ExecutionFill application ingestion;
- aggregate-create PLAN/GROUP/LEG/ORDER event backfill;
- Reconciliation Engine;
- Execution Coordinator.

These are not implied DONE by this evidence.

### 86.17. PRODUCTION SAFETY

No runtime exchange integration was added.

The service does NOT:

- call VenueAdapter;
- call ExecutionBoundary;
- submit/cancel exchange orders;
- reconcile venue state;
- start ExecutionCoordinator.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 86.18. STATUS

`TRADING_CORE_V2_LEDGER_ORDER_TRANSITION_APPLICATION — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_ORDER_TRANSITION_APPLICATION_OK`

### 86.19. PRIMARY NEXT STEP

Re-establish the remaining canonical Phase 2 Ledger requirements from
the live Audit and determine the first unfinished Ledger requirement
before declaring:

`TRADING_CORE_V2_LEDGER_OK`

Specifically verify whether the order-first application transition plus
current Plan/Group/Leg/Order/Fill persistence satisfies or still lacks
required:

- per-leg lifecycle evidence;
- recovery state evidence;
- immutable historical trail coverage;
- restart-safe Ledger semantics;
- multi-user isolation;
- fill lifecycle/application ingestion.

Do not start Phase 3 Reconciliation until Phase 2 Ledger evidence gate
is factually established.

Target:

one first unfinished Phase 2 Ledger requirement selected from live
Audit evidence.


## 87. Trading Core V2 — Phase 2 Ledger Gap Mapping — 2026-09-01

### 87.1. CANONICAL PHASE 2 REVIEW

Re-checked canonical Phase 2 requirements from Section 53.7 against
verified Ledger work in Sections 78–86.

Verified foundation exists for:

- execution intent / execution plan lineage;
- strategy and strategy-version lineage;
- grouped / pair execution identity;
- per-leg order ownership;
- exchange order identity;
- order lifecycle timestamps;
- immutable Ledger event persistence;
- deterministic event idempotency;
- user ownership validation for canonical order transitions;
- atomic Ledger event + ExecutionOrder materialized-state mutation.

### 87.2. EXISTING FILL FOUNDATION

Verified existing persistence support:

`ExecutionFill`

and:

`ExecutionRepository.add_execution_fill(...)`

Verified existing mutable leg state:

`PositionLeg.filled_quantity`

plus:

`ExecutionRepository.update_position_leg_state(...)`

ExecutionFill is append-oriented immutable fill evidence.

### 87.3. FIRST UNFINISHED PHASE 2 REQUIREMENT

The first unfinished canonical Phase 2 requirement is:

`PER-LEG FILL LIFECYCLE / APPLICATION INGESTION`

Current repository primitives do not constitute a canonical
application-level fill ingestion use case.

No verified application transaction currently proves:

ExecutionFill append
+
PositionLeg filled state update
+
immutable FILL_RECORDED Ledger event
+
single commit.

### 87.4. WHY REPOSITORY SUPPORT IS INSUFFICIENT

Existing:

`add_execution_fill(...)`

is persistence-only and flush-only.

Existing:

`update_position_leg_state(...)`

is also persistence-only and flush-only.

Neither method owns lifecycle semantics.

The existence of both repository methods does not prove atomic,
restart-safe per-leg fill state.

### 87.5. REQUIRED CANONICAL FILL INGESTION

The next Ledger application use case must atomically persist:

1. validated ExecutionFill;
2. immutable `FILL_RECORDED` ExecutionLedgerEvent;
3. corresponding PositionLeg materialized fill state;
4. corresponding ExecutionOrder materialized fill state where required;
5. one application-level transaction.

The implementation must be deterministic and idempotent.

### 87.6. FILL IDEMPOTENCY

Canonical fill ingestion must use persisted fill identity.

Existing identities include:

- fill_id;
- execution_order_id + venue_fill_id.

Duplicate equivalent fill ingestion must not:

- create a second fill;
- double-increment filled quantity;
- create duplicate lifecycle evidence.

Conflicting reuse of immutable fill identity must fail closed.

### 87.7. PER-LEG FILL STATE

PositionLeg materialized fill state must be derived from validated
persisted execution evidence rather than blindly incremented from an
untrusted request.

Required fields to consider include:

- filled_quantity;
- average_entry_price / average_exit_price where lifecycle semantics
  require them;
- leg status where fill completion changes state.

Exact aggregation policy must be established before implementation.

### 87.8. LEDGER EVIDENCE

Successful canonical fill ingestion must append immutable:

`FILL_RECORDED`

with lineage to:

- user;
- execution plan;
- position group / leg;
- execution order;
- execution fill;
- account;
- venue.

This closes the current gap between immutable ExecutionFill persistence
and the general execution lifecycle event trail.

### 87.9. REMAINING PHASE 2 GAPS AFTER FILL INGESTION

Not declared complete by this mapping:

- full PositionLeg lifecycle event integration;
- PositionGroup lifecycle event integration;
- recovery lifecycle evidence;
- explicit last-known local / venue state evidence;
- complete restart/recovery proof.

These remain later Phase 2 checks.

Phase 3 Reconciliation must not begin before the full
`TRADING_CORE_V2_LEDGER_OK` evidence gate is established.

### 87.10. PRODUCTION SAFETY

This section is factual gap mapping only.

No runtime behavior changed.

No exchange calls were introduced.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 87.11. STATUS

`TRADING_CORE_V2_PHASE2_LEDGER_GAP_MAPPING — VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_PHASE2_LEDGER_GAP_MAPPING_OK`

### 87.12. PRIMARY NEXT STEP

Design the canonical per-leg fill ingestion application contract.

Required design scope:

- ExecutionFill immutable identity verification;
- venue_fill_id replay semantics;
- ExecutionOrder / PositionLeg lineage validation;
- user ownership validation;
- deterministic filled_quantity aggregation;
- atomic ExecutionFill + FILL_RECORDED event + materialized state update;
- IntegrityError race handling;
- restart/idempotent replay behavior;
- no venue query;
- no Reconciliation Engine;
- no ExecutionCoordinator.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_DESIGN_OK`

## 88. Trading Core V2 — Ledger Fill Ingestion Design — 2026-09-01

### 88.1. EXISTING FOUNDATION VERIFIED

Verified existing persistence entities:

- ExecutionFill;
- ExecutionOrder;
- PositionLeg;
- ExecutionLedgerEvent.

Verified repository primitives:

- add_execution_fill;
- get_execution_fill_by_fill_id;
- get_execution_fill_by_venue_identity;
- list_execution_fills;
- update_execution_order_state;
- update_position_leg_state;
- add_ledger_event;
- get_ledger_event_by_event_id.

Repository methods remain persistence-only and flush-only.

### 88.2. CURRENT GAP

No verified application-level fill ingestion use case currently exists.

No existing code proves one atomic transaction for:

ExecutionFill append
+
FILL_RECORDED Ledger event
+
ExecutionOrder fill-state update
+
PositionLeg fill-state update.

Existing repository setters accept already-computed materialized values
and do not establish canonical fill aggregation policy.

### 88.3. APPLICATION OWNER

Fill ingestion will extend:

`ExecutionApplicationService`

No separate fill transaction owner is introduced.

Reason:

ExecutionApplicationService already owns Core V2 application commit /
rollback semantics and Ledger-integrated order transitions.

### 88.4. CANONICAL REQUEST CONTRACT

Target immutable request contract:

`ExecutionFillIngestion`

Required inputs:

- fill_id;
- order_id;
- user_id;
- execution_plan_id;
- quantity;
- price;
- fee;
- fee_currency;
- executed_at;
- source;
- event_id;
- payload.

Optional:

- venue_fill_id;
- account_id;
- venue_id;
- correlation_id;
- causation_id.

Quantity and price use Decimal at the application boundary.

No float arithmetic is canonical for fill accounting.

### 88.5. INPUT VALIDATION

Required validation:

- fill_id non-empty;
- event_id non-empty;
- order_id non-empty;
- user_id positive;
- execution_plan_id positive;
- quantity > 0;
- price > 0;
- fee >= 0;
- source non-empty.

Invalid input fails closed before persistence.

### 88.6. FILL IDENTITY

Canonical primary fill identity:

`fill_id`

Secondary venue identity when available:

`execution_order_id + venue_fill_id`

Both identities must be checked before new fill creation.

If fill_id already exists:

- full immutable fill identity must match;
- equivalent fill is idempotent replay;
- conflicting identity fails closed.

If venue_fill_id is present and resolves to an existing fill:

- immutable fill identity must match;
- equivalent fill is idempotent replay;
- conflicting identity fails closed.

No duplicate fill may change order or leg aggregates twice.

### 88.7. IMMUTABLE FILL IDENTITY

At minimum compare:

- fill_id;
- execution_order_id;
- venue_fill_id;
- quantity;
- price;
- fee;
- fee_currency;
- executed_at.

A reused immutable fill identity with different evidence fails closed.

### 88.8. LINEAGE VALIDATION

Before new ingestion:

ExecutionOrder must exist.

Service must validate:

- order.execution_plan_id == request.execution_plan_id;
- order.account_id == request.account_id when supplied;
- order.venue_id == request.venue_id when supplied.

PositionLeg referenced by:

`order.position_leg_id`

must exist.

The owning ExecutionPlan must exist and:

`ExecutionPlan.user_id == request.user_id`

Cross-user, cross-plan, cross-leg or conflicting venue/account lineage
fails closed.

### 88.9. AGGREGATION SOURCE OF TRUTH

Materialized fill quantities and prices must be derived from persisted
ExecutionFill evidence.

The application service must not blindly increment:

`current_filled_quantity + request.quantity`

because replay/restart/race conditions can double count.

Canonical aggregation after new fill persistence:

load all persisted fills for the ExecutionOrder
→ deterministic aggregate.

### 88.10. ORDER FILLED QUANTITY

Canonical:

`ExecutionOrder.filled_quantity`

equals:

sum of all persisted ExecutionFill.quantity for that execution order.

Invariant:

`0 <= filled_quantity <= requested_quantity`

If aggregate fill quantity exceeds requested_quantity:

fail closed and rollback.

### 88.11. ORDER AVERAGE FILL PRICE

Canonical weighted average:

sum(fill.quantity * fill.price)
/
sum(fill.quantity)

using Decimal arithmetic only.

If total filled quantity is zero:

average_fill_price remains null.

No arithmetic uses binary float.

### 88.12. ORDER MATERIALIZED STATUS

For fill ingestion:

if:

`0 < filled_quantity < requested_quantity`

target materialized order status:

`PARTIALLY_FILLED`

if:

`filled_quantity == requested_quantity`

target materialized order status:

`FILLED`

Overfill:

fail closed.

Fill ingestion does not infer SUBMITTED / ACCEPTED / REJECTED /
CANCELLED transitions.

Those remain separate lifecycle events.

### 88.13. POSITION LEG FILLED QUANTITY

Canonical initial Phase 2 policy:

`PositionLeg.filled_quantity`

is derived from persisted fills across all ExecutionOrders belonging to
that PositionLeg which represent entry/open exposure.

However, the current persistence schema does not explicitly classify an
ExecutionOrder as ENTRY vs EXIT beyond `reduce_only`.

Therefore initial implementation uses:

`reduce_only == False`

as the only approved entry-fill aggregation scope.

Canonical leg filled_quantity:

sum of ExecutionFill.quantity
for ExecutionOrders on the leg where reduce_only == False.

This policy must fail closed if future order semantics cannot be
classified unambiguously.

### 88.14. POSITION LEG AVERAGE ENTRY PRICE

Initial canonical entry price:

weighted Decimal average across persisted fills from:

ExecutionOrders for the PositionLeg
where:

`reduce_only == False`

Formula:

sum(fill.quantity * fill.price)
/
sum(fill.quantity)

No average_exit_price mutation occurs in the initial fill-ingestion
implementation.

Exit-fill accounting requires a separately designed close/reduction
contract.

### 88.15. POSITION LEG STATUS

Initial fill ingestion may update PositionLeg status only from
entry/open fill evidence.

If:

`0 < leg.filled_quantity < leg.target_quantity`

and target_quantity is known:

`OPENING`

If:

`leg.filled_quantity == leg.target_quantity`

and target_quantity is known:

`OPEN`

If target_quantity is null:

fill ingestion updates quantity/average price but does not infer terminal
leg status.

If aggregate entry fills exceed target_quantity:

fail closed.

### 88.16. REDUCE-ONLY / EXIT FILLS

A fill belonging to:

`ExecutionOrder.reduce_only == True`

must NOT increase:

- PositionLeg.filled_quantity;
- PositionLeg.average_entry_price.

Initial implementation may still:

- persist ExecutionFill;
- update ExecutionOrder fill quantity / average fill price;
- append FILL_RECORDED.

Canonical PositionLeg exit quantity / average_exit_price semantics are
deferred to a separate approved design.

This prevents incorrect mixing of entry and exit accounting.

### 88.17. LEDGER EVENT

Every new canonical fill ingestion must append:

`FILL_RECORDED`

ExecutionLedgerEvent.

Required lineage:

- user_id;
- execution_plan_id;
- position_group_id;
- position_leg_id;
- execution_order_id;
- execution_fill_id;
- account_id;
- venue_id.

Event occurred_at:

`ExecutionFill.executed_at`

Payload includes immutable fill evidence sufficient for audit, including:

- fill_id;
- venue_fill_id;
- quantity;
- price;
- fee;
- fee_currency;
- resulting order filled_quantity;
- resulting order average_fill_price;
- resulting leg filled_quantity where applicable;
- resulting leg average_entry_price where applicable.

### 88.18. EVENT ID IDEMPOTENCY

Fill ingestion also uses deterministic Ledger:

`event_id`

Equivalent fill replay must verify both:

- immutable ExecutionFill identity;
- immutable FILL_RECORDED Ledger event identity.

No replay may append a second event or mutate materialized totals again.

Conflicting event_id fails closed.

### 88.19. NEW FILL TRANSACTION ORDER

Canonical new-fill transaction:

1. validate request;
2. validate ExecutionPlan ownership;
3. load ExecutionOrder;
4. validate order lineage;
5. load PositionLeg;
6. check fill_id;
7. check venue_fill_id when present;
8. check event_id;
9. create ExecutionFill;
10. flush fill;
11. load/recompute persisted order fills;
12. compute deterministic order aggregates;
13. recompute leg entry aggregates when reduce_only == False;
14. validate no order/leg overfill;
15. construct FILL_RECORDED Ledger event;
16. append Ledger event;
17. update ExecutionOrder materialized fill state;
18. update PositionLeg entry state when applicable;
19. commit once;
20. refresh / return canonical persisted state.

All writes occur in one AsyncSession transaction.

### 88.20. INTEGRITYERROR RACE HANDLING

Unique fill/event identities may race.

Required handling:

IntegrityError
→ rollback
→ reread fill identity
→ reread event identity
→ reload order/leg lineage
→ verify immutable equivalence.

Equivalent persisted race result:

idempotent success.

Conflicting persisted identity:

fail closed.

If expected persisted identities are absent after rollback:

re-raise original IntegrityError.

### 88.21. RESTART SAFETY

Restart-safe aggregation derives materialized totals from persisted
ExecutionFill rows.

In-memory counters are not authoritative.

Repeated ingestion after process restart:

- resolves persisted fill identity;
- verifies immutable evidence;
- does not double count;
- does not append duplicate event evidence.

### 88.22. REQUIRED REPOSITORY READ SUPPORT

Current repository has:

`list_execution_fills(execution_order_id)`

For deterministic PositionLeg entry aggregation, implementation requires
a persistence read path across all orders/fills for one leg.

Preferred minimal extension:

reuse:

`list_execution_orders_for_leg(position_leg_id)`

then:

`list_execution_fills(execution_order_id)`

for each relevant non-reduce-only order.

No new aggregate SQL repository API is required initially.

This preserves repository simplicity.

### 88.23. NO FLOAT ACCOUNTING

All canonical quantity / price / weighted-average calculations use:

`Decimal`

Existing PostgreSQL Numeric(20, 8) remains persistence representation.

Float conversion is forbidden in Ledger fill aggregation.

### 88.24. SCOPE LIMIT

This design does not implement:

- venue fill polling;
- exchange reconciliation;
- ExecutionCoordinator;
- reduce-only PositionLeg exit aggregation;
- average_exit_price lifecycle;
- realized PnL;
- PositionGroup lifecycle state;
- recovery policy.

These remain separate canonical steps.

### 88.25. PRODUCTION SAFETY

Fill ingestion remains a persistence/application contract.

It does NOT:

- query VenueAdapter;
- call ExecutionBoundary;
- submit/cancel orders;
- enable Restricted Live;
- enable Full Live;
- allow AI direct exchange access.

Production permissions remain unchanged.

### 88.26. STATUS

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_DESIGN_OK`

### 88.27. PRIMARY NEXT STEP

Implement and verify the initial canonical fill-ingestion application
use case inside:

`ExecutionApplicationService`

Scope:

- immutable ExecutionFill request;
- Decimal-only validation and aggregation;
- fill_id / venue_fill_id replay handling;
- ExecutionPlan / ExecutionOrder / PositionLeg lineage;
- user ownership validation;
- deterministic order fill aggregation;
- non-reduce-only PositionLeg entry aggregation;
- FILL_RECORDED Ledger event;
- one transaction / one commit;
- rollback and IntegrityError race handling;
- focused tests;
- existing Core V2 regression;
- no venue/reconciliation/coordinator integration.

Target evidence tag:

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_APPLICATION_OK`

## 89. Trading Core V2 — Ledger Fill Ingestion Application — 2026-09-02

### 89.1. IMPLEMENTED

Extended:

`ExecutionApplicationService`

with canonical:

`ExecutionFillIngestion`

and:

`ingest_execution_fill(...)`

Added minimal repository dependency:

`get_position_leg_by_id(...)`

Repository remains persistence-only and flush-only.

### 89.2. CANONICAL FILL PATH

Verified new-fill path:

request validation
→ ExecutionPlan ownership
→ ExecutionOrder lineage
→ PositionLeg lookup
→ fill/event replay checks
→ ExecutionFill append
→ deterministic persisted-fill aggregation
→ FILL_RECORDED Ledger event
→ ExecutionOrder materialized update
→ PositionLeg entry-state update where applicable
→ one commit
→ refresh / return.

### 89.3. DECIMAL AGGREGATION

Order and leg fill accounting uses Decimal-only aggregation.

Canonical order values are derived from persisted ExecutionFill rows:

- filled_quantity = sum(fill.quantity);
- average_fill_price = weighted average by fill quantity.

No blind current-value increment is canonical.

### 89.4. ORDER STATE

Persisted fills determine:

- PARTIALLY_FILLED when aggregate quantity is below requested quantity;
- FILLED when aggregate quantity equals requested quantity.

Order overfill fails closed and rolls back.

### 89.5. POSITION LEG ENTRY STATE

For non-reduce-only orders, PositionLeg entry state is recomputed from
persisted fills across non-reduce-only ExecutionOrders for that leg.

Verified materialized fields include:

- filled_quantity;
- average_entry_price;
- OPENING / OPEN where target_quantity permits deterministic inference.

Leg overfill fails closed.

### 89.6. REDUCE-ONLY SAFETY

A fill for:

`ExecutionOrder.reduce_only == True`

does not mutate PositionLeg entry quantity / average-entry state.

The fill is still persisted, recorded in Ledger, and reflected in its
ExecutionOrder.

Exit-leg accounting remains outside this initial contract.

### 89.7. FILL IDEMPOTENCY

Verified deterministic fill identity handling through:

- fill_id;
- execution_order_id + venue_fill_id when supplied.

Equivalent persisted replay:

- does not create a second fill;
- does not append a second Ledger event;
- does not mutate materialized state again;
- does not commit again.

Conflicting immutable fill identity fails closed.

### 89.8. LEDGER EVIDENCE

Each new canonical fill appends immutable:

`FILL_RECORDED`

with lineage to:

- user;
- execution plan;
- position group;
- position leg;
- execution order;
- execution fill;
- account;
- venue.

Replay verifies immutable fill and Ledger evidence.

### 89.9. TRANSACTION SEMANTICS

Successful new fill:

- one application-level commit.

Generic failure:

- rollback;
- no commit;
- exception propagated.

IntegrityError race:

rollback
→ reread persisted fill
→ reread Ledger event
→ reload ExecutionOrder
→ reload PositionLeg
→ verify lineage
→ verify immutable fill identity
→ verify immutable Ledger identity
→ idempotent return.

If persisted race evidence is incomplete, original IntegrityError is
re-raised.

### 89.10. RESTART SAFETY

Materialized order/leg fill state is derived from persisted
ExecutionFill rows rather than in-memory counters.

Equivalent fill replay after restart does not double-count persisted
fill evidence.

### 89.11. FOCUSED TEST EVIDENCE

Focused fill-ingestion suite:

`8 passed`

Result:

`focused_exit=0`

Verified:

- successful new fill / one commit;
- Decimal weighted average;
- equivalent replay idempotency;
- immutable fill conflict fail closed;
- order overfill rollback;
- reduce-only leg-entry protection;
- IntegrityError rollback → reread → replay verification;
- generic write failure rollback.

### 89.12. APPLICATION REGRESSION

Execution application scope:

`25 passed`

Result:

`application_regression_exit=0`

No regression detected in:

- aggregate create-or-verify;
- Ledger order transition;
- Ledger fill ingestion.

### 89.13. CORE V2 REGRESSION

Combined persistence/application scope:

`56 passed`

Result:

`core_v2_regression_exit=0`

Covered:

- execution persistence models;
- ExecutionLedgerEvent model;
- ExecutionRepository;
- ExecutionApplicationService;
- Ledger order transition;
- Ledger fill ingestion.

### 89.14. STATIC VERIFICATION

`python -m py_compile`
→ PASS

`python -m flake8`
→ PASS

### 89.15. CURRENT LIMITS

This evidence does NOT establish:

- reduce-only PositionLeg exit aggregation;
- average_exit_price lifecycle;
- generic PositionLeg lifecycle Ledger events;
- PositionGroup lifecycle Ledger events;
- recovery lifecycle;
- Reconciliation Engine;
- ExecutionCoordinator.

These remain separate requirements.

### 89.16. PRODUCTION SAFETY

No VenueAdapter query was added.

No ExecutionBoundary call was added.

No exchange order submission/cancellation was added.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 89.17. STATUS

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_APPLICATION — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_FILL_INGESTION_APPLICATION_OK`

### 89.18. PRIMARY NEXT STEP

Re-evaluate the remaining Phase 2 Ledger requirements after verified
fill ingestion and identify exactly the first unfinished Ledger gap
before declaring:

`TRADING_CORE_V2_LEDGER_OK`

Do not begin Phase 3 Reconciliation until the Phase 2 Ledger gate is
factually established.

## 90. Trading Core V2 — PositionLeg Lifecycle Ledger Gap — 2026-09-02

### 90.1. FACTUAL CHECK

Verified current PositionLeg state writers.

Current repository writer:

`ExecutionRepository.update_position_leg_state(...)`

Current application usage:

`ExecutionApplicationService.ingest_execution_fill(...)`

The fill-ingestion application may derive and persist:

- OPENING;
- OPEN.

### 90.2. LEDGER EVENT CHECK

Repository/application/test search found no current use of:

`LEG_STATE_CHANGED`

and no current use of:

`LEG_CREATED`

as canonical ExecutionLedgerEvent lifecycle records.

### 90.3. CURRENT BEHAVIOR

Current fill ingestion atomically persists:

ExecutionFill
+
FILL_RECORDED
+
ExecutionOrder materialized fill state
+
PositionLeg materialized entry state.

However, when PositionLeg.status changes, the immutable Ledger currently
records the fill fact but does not record a dedicated immutable leg
lifecycle transition fact.

### 90.4. GAP

Canonical immutable PositionLeg lifecycle trail is therefore incomplete.

Current materialized:

`PositionLeg.status`

can reflect:

- PENDING;
- OPENING;
- OPEN;

but the transition itself is not represented by a dedicated:

`LEG_STATE_CHANGED`

event.

### 90.5. WHY FILL_RECORDED IS NOT SUFFICIENT

`FILL_RECORDED`

is immutable execution evidence for a fill.

It is not a canonical substitute for a lifecycle transition record
because it does not explicitly establish:

- previous PositionLeg status;
- resulting PositionLeg status;
- transition reason;
- lifecycle transition identity.

Materialized state and immutable lifecycle history remain separate
concerns.

### 90.6. FIRST REMAINING PHASE 2 GAP

The first verified unfinished Phase 2 Ledger requirement after fill
ingestion is:

`POSITION LEG LIFECYCLE EVENT INTEGRATION`

This must be resolved before declaring:

`TRADING_CORE_V2_LEDGER_OK`

### 90.7. PRODUCTION SAFETY

This section is factual gap confirmation only.

No runtime code changed.

No venue/exchange access changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 90.8. STATUS

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_GAP — VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_GAP_OK`

### 90.9. PRIMARY NEXT STEP

Design the canonical PositionLeg lifecycle Ledger transition contract.

Design scope:

- LEG_STATE_CHANGED immutable identity;
- previous_status / target_status;
- PositionLeg / PositionGroup / ExecutionPlan lineage;
- user ownership;
- transition reason/source;
- event idempotency;
- atomic materialized state + Ledger event transaction;
- interaction with fill ingestion;
- no PositionGroup lifecycle yet;
- no Reconciliation Engine;
- no ExecutionCoordinator.

Target evidence tag:

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_DESIGN_OK`

## 91. Trading Core V2 — PositionLeg Lifecycle Ledger Design — 2026-09-02

### 91.1. PURPOSE

Canonical PositionLeg materialized status changes require dedicated
immutable lifecycle evidence.

Canonical event:

`LEG_STATE_CHANGED`

### 91.2. APPLICATION OWNER

Lifecycle integration remains inside:

`ExecutionApplicationService`

No separate transaction owner is introduced.

### 91.3. TRANSITION CONTRACT

A leg transition must explicitly carry:

- event_id;
- user_id;
- execution_plan_id;
- position_leg_id;
- previous_status;
- target_status;
- occurred_at;
- source;
- reason;
- payload;
- optional correlation_id;
- optional causation_id.

No arbitrary implicit status transition is canonical.

### 91.4. LINEAGE

Before transition the service must verify:

PositionLeg
→ PositionGroup
→ ExecutionPlan
→ user ownership.

The requested execution_plan_id and user_id must match persisted
ownership.

Account / venue lineage remains inherited from PositionLeg.

### 91.5. IMMUTABLE EVENT

`LEG_STATE_CHANGED` must contain lineage to:

- user;
- execution plan;
- position group;
- position leg;
- account;
- venue.

Payload must include at minimum:

- previous_status;
- target_status;
- reason.

Equivalent event_id replay is idempotent.

Conflicting immutable event identity fails closed.

### 91.6. ATOMICITY

Canonical transition transaction:

validate
→ verify lineage / ownership
→ verify current leg status
→ check event_id
→ append LEG_STATE_CHANGED
→ update PositionLeg materialized status
→ one commit.

Failure rolls back both event and materialized state.

### 91.7. CURRENT FILL INGESTION INTEGRATION

`ingest_execution_fill(...)` already derives OPENING / OPEN from
persisted fill evidence.

When fill ingestion causes an actual PositionLeg status change:

previous_status != target_status

the same fill-ingestion transaction must append:

`LEG_STATE_CHANGED`

in addition to:

`FILL_RECORDED`.

No LEG_STATE_CHANGED event is emitted when status is unchanged.

### 91.8. EVENT IDENTITY IN FILL INGESTION

Fill-triggered leg transition requires its own deterministic event_id,
separate from the FILL_RECORDED event_id.

The fill ingestion request must not reuse one event_id for two immutable
events.

Exact deterministic derivation / request contract must be implemented
explicitly and tested.

### 91.9. NO DOUBLE AUTHORITY

PositionLeg status must not be mutated through one application path
while lifecycle evidence is written through another transaction.

Once integrated, canonical application writes of PositionLeg.status
must pair materialized mutation with LEG_STATE_CHANGED evidence.

Repository remains persistence-only.

### 91.10. INITIAL STATE SCOPE

Initial lifecycle scope covers currently proven states:

- PENDING;
- OPENING;
- OPEN.

Closing / recovery / closed / failed semantics are deferred until their
own lifecycle requirements are designed.

### 91.11. PRODUCTION SAFETY

No VenueAdapter or ExecutionBoundary integration is added by this
design.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 91.12. STATUS

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_DESIGN_OK`

### 91.13. PRIMARY NEXT STEP

Implement and verify PositionLeg lifecycle Ledger integration for
fill-triggered PENDING → OPENING → OPEN transitions.

Target evidence tag:

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_APPLICATION_OK`

## 92. Trading Core V2 — PositionLeg Lifecycle Ledger Application — 2026-09-02

### 92.1. IMPLEMENTED

Integrated immutable PositionLeg lifecycle evidence into:

`ExecutionApplicationService.ingest_execution_fill(...)`

Canonical lifecycle event:

`LEG_STATE_CHANGED`

Current verified fill-triggered transitions:

- PENDING → OPENING;
- OPENING → OPEN.

No lifecycle event is emitted when derived status is unchanged.

Reduce-only fill ingestion does not mutate PositionLeg entry lifecycle.

### 92.2. ATOMIC TRANSACTION

For a fill-triggered PositionLeg transition the canonical transaction is:

ExecutionFill
→ FILL_RECORDED
→ LEG_STATE_CHANGED
→ ExecutionOrder materialized update
→ PositionLeg materialized update
→ one commit.

Failure rolls back the transaction.

### 92.3. IMMUTABLE LIFECYCLE EVIDENCE

`LEG_STATE_CHANGED` records:

- user / execution-plan lineage;
- position-group / position-leg lineage;
- account / venue lineage;
- previous_status;
- target_status;
- reason = FILL_INGESTION;
- source;
- correlation / causation;
- occurred_at.

Derived lifecycle event identity is separate from FILL_RECORDED.

ExecutionLedgerEvent.event_id schema limit is 160 characters and the
derived lifecycle event ID is fail-closed against that limit.

### 92.4. FILL ROOT EVIDENCE

`FILL_RECORDED.payload` now also records lifecycle outcome evidence:

- leg_previous_status;
- leg_target_status;
- leg_state_event_id.

This allows restart/race replay to determine whether a corresponding
LEG_STATE_CHANGED event is mandatory.

### 92.5. IDEMPOTENCY / RACE SAFETY

IntegrityError replay verifies:

ExecutionFill
+
FILL_RECORDED
+
LEG_STATE_CHANGED when referenced by FILL_RECORDED.

Complete equivalent lifecycle evidence returns idempotently.

Missing mandatory LEG_STATE_CHANGED evidence fails closed.

Conflicting immutable lifecycle identity/payload fails closed.

### 92.6. FOCUSED EVIDENCE

`tests/test_trading_core_ledger_fill_ingestion.py`

Result:

`12 passed`

`focused_exit=0`

Verified:

- PENDING → OPENING;
- OPENING → OPEN;
- unchanged status does not emit lifecycle event;
- reduce-only does not emit lifecycle event;
- complete lifecycle IntegrityError replay;
- missing lifecycle event fails closed;
- previous fill-ingestion/idempotency/rollback behavior.

### 92.7. REGRESSION EVIDENCE

Combined Trading Core V2 persistence/application regression:

`60 passed`

`core_v2_regression_exit=0`

No regression detected across:

- execution models;
- ExecutionLedgerEvent model;
- ExecutionRepository;
- ExecutionApplicationService;
- order lifecycle;
- fill ingestion;
- PositionLeg lifecycle integration.

Static verification:

`py_compile` — PASS

`flake8` — PASS

### 92.8. PRODUCTION SAFETY

No VenueAdapter query was added.

No ExecutionBoundary call was added.

No order submission/cancellation was added.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 92.9. STATUS

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_APPLICATION — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_LEG_LIFECYCLE_APPLICATION_OK`

### 92.10. PRIMARY NEXT STEP

Re-evaluate remaining Phase 2 Ledger requirements and identify exactly
the first unfinished requirement before declaring:

`TRADING_CORE_V2_LEDGER_OK`

## 93. Trading Core V2 — PositionGroup Creation Ledger Design — 2026-09-02

### 93.1. FACT

PositionGroup is created by:

`ExecutionApplicationService.create_or_verify_aggregate(...)`

Current materialized initial state is:

`PENDING`

No canonical immutable:

`GROUP_CREATED`

ExecutionLedgerEvent is currently appended during aggregate creation.

### 93.2. PURPOSE

Every canonical PositionGroup creation must have immutable creation
evidence in the same transaction as materialized aggregate creation.

Canonical event:

`GROUP_CREATED`

### 93.3. APPLICATION OWNER

The transaction owner remains:

`ExecutionApplicationService`

Repository remains persistence-only / flush-only.

No separate PositionGroup lifecycle service is introduced.

### 93.4. GROUP_CREATED LINEAGE

`GROUP_CREATED` must contain lineage to:

- user;
- execution plan;
- position group.

The event must also record sufficient immutable group identity evidence:

- group_id;
- shape;
- strategy;
- strategy_version;
- trade_source;
- initial_status.

Initial canonical status:

`PENDING`

### 93.5. EVENT IDENTITY

GROUP_CREATED requires its own deterministic immutable event_id.

It must not reuse ExecutionPlan, order, fill, or leg lifecycle event IDs.

The exact event-id derivation must respect the existing
ExecutionLedgerEvent.event_id maximum length of 160 characters.

Equivalent aggregate replay must not create another GROUP_CREATED event.

Conflicting immutable event identity must fail closed.

### 93.6. ATOMICITY

Canonical aggregate creation transaction:

ExecutionPlan
→ PositionGroup
→ GROUP_CREATED
→ PositionLeg(s)
→ ExecutionOrder(s)
→ one commit.

Any failure rolls back the aggregate and its GROUP_CREATED evidence.

### 93.7. EXISTING IDEMPOTENCY

Existing create-or-verify aggregate IntegrityError replay must continue
to remain restart-safe and idempotent.

After GROUP_CREATED integration, equivalent replay must verify persisted
GROUP_CREATED evidence in addition to materialized PositionGroup
identity before returning success.

Incomplete or conflicting GROUP_CREATED evidence must fail closed.

### 93.8. SCOPE

This design covers only:

`GROUP_CREATED`

It does NOT yet define:

`GROUP_STATE_CHANGED`

Recovery lifecycle remains separate.

Exchange reconciliation remains Phase 3.

ExecutionCoordinator remains Phase 4.

### 93.9. PRODUCTION SAFETY

No VenueAdapter access is introduced.

No ExecutionBoundary call is introduced.

No exchange order submission/cancellation is introduced.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 93.10. STATUS

`TRADING_CORE_V2_POSITION_GROUP_CREATION_LEDGER_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_GROUP_CREATION_LEDGER_DESIGN_OK`

### 93.11. PRIMARY NEXT STEP

Implement and verify GROUP_CREATED integration inside canonical
aggregate creation transaction.

Target evidence tag:

`TRADING_CORE_V2_POSITION_GROUP_CREATION_LEDGER_APPLICATION_OK`

## 94. Trading Core V2 — PositionGroup Creation Ledger Application — 2026-09-02

### 94.1. IMPLEMENTED

Integrated immutable PositionGroup creation evidence into:

`ExecutionApplicationService.create_or_verify_aggregate(...)`

Canonical event:

`GROUP_CREATED`

### 94.2. AGGREGATE CREATION TRANSACTION

Verified canonical order:

ExecutionPlan
→ PositionGroup(PENDING)
→ GROUP_CREATED
→ PositionLeg(s)
→ ExecutionOrder(s)
→ one commit.

GROUP_CREATED is persisted in the same application-owned transaction
as the materialized aggregate.

### 94.3. IMMUTABLE EVENT CONTRACT

GROUP_CREATED records:

- event_id;
- user;
- execution plan;
- position group;
- source;
- occurred_at.

Payload records:

- group_id;
- shape;
- strategy;
- strategy_version;
- trade_source;
- initial_status = PENDING.

### 94.4. REQUEST METADATA

`ExecutionAggregateCreate` now carries deterministic:

- event_id;
- occurred_at.

Validation fails closed when:

- event_id is empty;
- event_id exceeds ExecutionLedgerEvent schema limit;
- occurred_at is missing.

### 94.5. IDEMPOTENT REPLAY

Existing aggregate replay verifies:

ExecutionPlan identity
→ PositionGroup identity
→ persisted GROUP_CREATED
→ GROUP_CREATED immutable identity/payload
→ PositionLeg identities
→ ExecutionOrder identities.

Missing GROUP_CREATED evidence fails closed.

Conflicting GROUP_CREATED identity/payload fails closed.

### 94.6. INTEGRITYERROR RACE

Concurrent aggregate creation race is handled as:

IntegrityError
→ rollback
→ reread persisted ExecutionPlan
→ verify PositionGroup
→ verify GROUP_CREATED
→ verify legs/orders
→ idempotent return.

No second GROUP_CREATED event is appended during equivalent replay.

### 94.7. FOCUSED EVIDENCE

`tests/test_trading_core_execution_application_service.py`

Result:

`11 passed`

`aggregate_focused_exit=0`

Verified:

- GROUP_CREATED happy path;
- immutable event identity/payload;
- existing aggregate replay;
- missing GROUP_CREATED fail closed;
- IntegrityError race replay;
- previous aggregate validation/idempotency behavior.

### 94.8. REGRESSION EVIDENCE

Combined Trading Core V2 persistence/application regression:

`62 passed`

`core_v2_regression_exit=0`

No regression detected across:

- execution models;
- ExecutionLedgerEvent model;
- ExecutionRepository;
- aggregate application service;
- order lifecycle;
- fill ingestion;
- PositionLeg lifecycle.

Static verification:

`py_compile` — PASS

`flake8` — PASS

### 94.9. PRODUCTION SAFETY

No VenueAdapter access was added.

No ExecutionBoundary call was added.

No exchange order submission/cancellation was added.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 94.10. STATUS

`TRADING_CORE_V2_POSITION_GROUP_CREATION_LEDGER_APPLICATION — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_GROUP_CREATION_LEDGER_APPLICATION_OK`

### 94.11. PRIMARY NEXT STEP

Re-check the next unfinished Phase 2 Ledger requirement.

Current candidate from verified Phase 2 gap mapping:

`POSITION GROUP STATE LIFECYCLE / GROUP_STATE_CHANGED`

Do not declare:

`TRADING_CORE_V2_LEDGER_OK`

until the remaining Phase 2 requirements are factually verified.

## 95. Trading Core V2 — PositionGroup State Lifecycle Boundary — 2026-09-02

### 95.1. FACTUAL CHECK

Verified current PositionGroup status writers.

Repository primitive exists:

`ExecutionRepository.update_position_group_status(...)`

Current repository behavior is persistence-only:

group.status = status
→ flush.

No application-level caller was found.

No current runtime use of:

`GROUP_STATE_CHANGED`

was found.

### 95.2. CURRENT MATERIALIZED STATE

PositionGroup creation is now verified with initial materialized status:

`PENDING`

and immutable creation evidence:

`GROUP_CREATED`

No later PositionGroup runtime transition is currently owned by
ExecutionApplicationService or another canonical Trading Core V2
application component.

### 95.3. ARCHITECTURAL BOUNDARY

Phase 2 Ledger must not invent PositionGroup lifecycle transitions that
do not yet exist in the canonical runtime.

States such as:

- OPENING;
- OPEN;
- CLOSING;
- RECOVERY;
- CLOSED;
- FAILED;

belong to execution coordination semantics when a canonical component
actually owns those transitions.

The future canonical owner is expected to be ExecutionCoordinator,
subject to its separately approved implementation phase.

### 95.4. GROUP_STATE_CHANGED STATUS

`GROUP_STATE_CHANGED`

remains a valid Ledger event family for future real PositionGroup
transitions.

It is NOT emitted speculatively during Phase 2 merely to satisfy event
coverage.

Once a canonical PositionGroup status transition owner exists, every
materialized transition must be paired atomically with immutable:

`GROUP_STATE_CHANGED`

evidence.

### 95.5. PHASE 2 INTERPRETATION

For current Phase 2 scope, PositionGroup lifecycle evidence is complete
for facts that actually exist:

PositionGroup creation
→ PENDING
→ GROUP_CREATED.

There is currently no verified later materialized PositionGroup status
transition requiring GROUP_STATE_CHANGED integration.

Therefore no fake runtime transition implementation is required for the
current Ledger gate.

### 95.6. PRODUCTION SAFETY

No runtime code changed.

No PositionGroup transition behavior was introduced.

No VenueAdapter access changed.

No ExecutionBoundary access changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 95.7. STATUS

`TRADING_CORE_V2_POSITION_GROUP_STATE_LIFECYCLE_BOUNDARY — VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_POSITION_GROUP_STATE_LIFECYCLE_BOUNDARY_OK`

### 95.8. PRIMARY NEXT STEP

Check the next unfinished Phase 2 Ledger requirement:

`RECOVERY LIFECYCLE EVIDENCE`

Do not begin Phase 3 Reconciliation until the Phase 2 Ledger gate is
factually established.

## 96. Trading Core V2 — Recovery Lifecycle Boundary — 2026-09-02

### 96.1. FACTUAL CHECK

Searched Trading Core V2 models, services, trading_core and tests for:

- RECOVERY_STARTED;
- RECOVERY_COMPLETED;
- recovery_state;
- recovery_status;
- RECOVERY materialized status;
- last-known local / venue recovery fields.

No current canonical Trading Core V2 recovery runtime path was found.

### 96.2. CURRENT STATE

Current Ledger event model already supports future immutable event families:

`RECOVERY_STARTED`

and:

`RECOVERY_COMPLETED`

However, no current canonical application component owns a real
recovery state transition.

No recovery materialized state is currently written by
ExecutionApplicationService or ExecutionRepository-backed application
logic.

### 96.3. ARCHITECTURAL BOUNDARY

Phase 2 Ledger must not invent a recovery state machine that does not
yet exist in canonical runtime behavior.

Recovery execution semantics belong to later components that actually
own recovery decisions and transitions, including:

- Reconciliation Engine;
- ExecutionCoordinator;
- future pair-native recovery.

When such runtime transitions exist, materialized recovery state must
be paired atomically with immutable Ledger evidence.

### 96.4. RECOVERY EVENT STATUS

`RECOVERY_STARTED`

and:

`RECOVERY_COMPLETED`

remain valid Ledger event families.

They are schema-ready but are not emitted speculatively during Phase 2.

No fake recovery transition implementation is required for the current
Ledger gate.

### 96.5. PHASE 2 INTERPRETATION

For current Phase 2 scope, recovery requirements are satisfied only as
an architectural/event-contract boundary.

Actual restart recovery against exchange state remains a later
Reconciliation responsibility.

Actual coordinated execution recovery remains a later
ExecutionCoordinator responsibility.

### 96.6. PRODUCTION SAFETY

No runtime code changed.

No recovery behavior was activated.

No VenueAdapter access changed.

No ExecutionBoundary access changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 96.7. STATUS

`TRADING_CORE_V2_RECOVERY_LIFECYCLE_BOUNDARY — VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_RECOVERY_LIFECYCLE_BOUNDARY_OK`

### 96.8. PRIMARY NEXT STEP

Check the next unfinished Phase 2 Ledger requirement:

`EXPLICIT LAST-KNOWN LOCAL / VENUE STATE EVIDENCE`

Do not begin Phase 3 Reconciliation until the Phase 2 Ledger gate is
factually established.

## 97. Trading Core V2 — Explicit Local / Venue Order State Design — 2026-09-02

### 97.1. FACT

ExecutionOrder currently persists canonical local state through:

`status`

and venue identity through:

`venue_order_id`.

Canonical VenueAdapter contract already defines:

`VenueOrderState`

with:

- PENDING;
- ACCEPTED;
- PARTIALLY_FILLED;
- FILLED;
- CANCELLED;
- REJECTED;
- UNKNOWN.

No persisted explicit last-known venue order state currently exists.

No venue-state observation timestamp currently exists.

### 97.2. PHASE 2 GAP

Canonical Phase 2 requires:

`local / exchange state`

Current local state exists.

Current explicit persisted venue state does not.

Therefore this is a real Phase 2 Ledger persistence gap.

### 97.3. CANONICAL EXECUTIONORDER EXTENSION

ExecutionOrder must explicitly persist:

`status`
→ canonical local materialized state.

`venue_state`
→ last-known observed VenueOrderState.

`venue_state_observed_at`
→ timestamp at which the stored venue_state was observed.

`venue_order_id`
remains the venue order identity.

### 97.4. NULLABILITY

`venue_state` and `venue_state_observed_at` are nullable.

Before the first actual venue observation:

venue_state = NULL
venue_state_observed_at = NULL.

No synthetic venue state is inferred from local status.

### 97.5. STATE AUTHORITY

Local and venue state are intentionally distinct.

Canonical rule:

local status
!= automatically equal to
venue_state.

Phase 2 persists both representations.

Phase 3 Reconciliation will compare them.

### 97.6. VENUE STATE DOMAIN

Persisted venue_state values must be constrained by the existing
canonical:

`VenueOrderState`

contract.

No duplicate venue-state enum is introduced.

### 97.7. UPDATE OWNERSHIP

ExecutionRepository remains persistence-only.

Application-level callers may persist last-known venue observations.

Phase 2 does not query BingX or any VenueAdapter to obtain those
observations.

Actual venue querying belongs to later runtime components, primarily
Reconciliation.

### 97.8. AUDITABILITY

A venue-state observation must be persistable together with immutable
Ledger evidence when a canonical application use case owns that
observation.

Exact Reconciliation discrepancy semantics remain Phase 3.

### 97.9. PRODUCTION SAFETY

No VenueAdapter query is introduced by this design.

No ExecutionBoundary call is introduced.

No exchange order submission/cancellation is introduced.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 97.10. STATUS

`TRADING_CORE_V2_LOCAL_VENUE_ORDER_STATE_DESIGN — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LOCAL_VENUE_ORDER_STATE_DESIGN_OK`

### 97.11. PRIMARY NEXT STEP

Implement persistence support for:

- ExecutionOrder.venue_state;
- ExecutionOrder.venue_state_observed_at.

Then verify schema, ORM, repository update behavior, focused tests and
regression.

Target evidence tag:

`TRADING_CORE_V2_LOCAL_VENUE_ORDER_STATE_PERSISTENCE_OK`

## 98. Trading Core V2 — Explicit Local / Venue Order State Persistence — 2026-09-02

### 98.1. IMPLEMENTED

ExecutionOrder persistence now explicitly distinguishes:

`status`
→ canonical local materialized order state.

`venue_state`
→ last-known observed venue order state.

`venue_state_observed_at`
→ timestamp of the last-known venue-state observation.

Existing:

`venue_order_id`

continues to represent venue order identity.

### 98.2. DATABASE MIGRATION

Alembic migration:

`d7f4b2a91c6e_add_execution_order_venue_state.py`

Revision chain:

`c6e91f7a2b34`
→ `d7f4b2a91c6e`

Migration applied successfully.

Database current revision:

`d7f4b2a91c6e (head)`.

Verified PostgreSQL schema:

- execution_orders.venue_state VARCHAR(30), nullable;
- execution_orders.venue_state_observed_at TIMESTAMP, nullable;
- ix_execution_orders_venue_state exists.

### 98.3. ORM

ExecutionOrder ORM now maps:

- venue_state;
- venue_state_observed_at.

ORM mapping remains aligned with PostgreSQL schema.

### 98.4. REPOSITORY

`ExecutionRepository.update_execution_order_state(...)`

can now persist independently:

- local status;
- venue_state;
- venue_state_observed_at.

Repository remains persistence-only.

No automatic synchronization between local and venue state is performed.

### 98.5. STATE AUTHORITY

Canonical rule verified:

local status
!= automatically equal to
venue_state.

No synthetic venue state is derived from local state.

Before first actual venue observation:

venue_state = NULL
venue_state_observed_at = NULL.

### 98.6. FOCUSED EVIDENCE

Repository focused suite:

`16 passed`

`repository_focused_exit=0`

Execution model focused suite:

`6 passed`

`models_focused_exit=0`

Static checks:

`py_compile` — PASS

`flake8` — PASS

### 98.7. REGRESSION EVIDENCE

Combined Trading Core V2 regression:

`63 passed`

`core_v2_regression_exit=0`

Verified no regression across:

- execution models;
- execution ledger event model;
- execution repository;
- aggregate application service;
- order lifecycle;
- fill ingestion;
- PositionLeg lifecycle.

### 98.8. PRODUCTION SAFETY

No VenueAdapter query was introduced.

No BingX access was introduced.

No ExecutionBoundary call was introduced.

No order submission/cancellation behavior was changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

### 98.9. STATUS

`TRADING_CORE_V2_LOCAL_VENUE_ORDER_STATE_PERSISTENCE — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LOCAL_VENUE_ORDER_STATE_PERSISTENCE_OK`

### 98.10. PRIMARY NEXT STEP

Verify the final unfinished Phase 2 Ledger requirement:

`COMPLETE RESTART / RECOVERY PROOF`

Do not declare:

`TRADING_CORE_V2_LEDGER_OK`

until restart/recovery safety is factually verified.

## 99. Trading Core V2 — Ledger Phase 2 Final Gate — 2026-09-02

### 99.1. SCOPE CLOSED

Phase 2 objective:

make Trading Core V2 ownership, persistence state and immutable Ledger
evidence explicit, restart-safe, idempotent and auditable.

Verified Phase 2 capabilities include:

- execution plan persistence;
- position group persistence;
- per-leg persistence;
- per-order persistence;
- per-fill persistence;
- strategy/version lineage;
- pair/group identity;
- venue order identity;
- immutable ExecutionLedgerEvent trail;
- order lifecycle evidence;
- fill ingestion evidence;
- PositionLeg lifecycle evidence;
- PositionGroup creation evidence;
- deterministic replay identity;
- IntegrityError race recovery;
- explicit local order state;
- explicit last-known venue order state;
- venue-state observation timestamp;
- restart-safe aggregate reread and verification.

### 99.2. POSITIONGROUP LIFECYCLE BOUNDARY

Current runtime has no canonical application owner for later
PositionGroup state transitions.

Therefore Phase 2 does not invent speculative GROUP_STATE_CHANGED
runtime transitions.

GROUP_STATE_CHANGED remains a valid future Ledger event family and must
be emitted atomically when a future canonical component owns a real
materialized group state transition.

### 99.3. RECOVERY BOUNDARY

Current Phase 2 runtime has no canonical recovery state machine.

RECOVERY_STARTED and RECOVERY_COMPLETED remain valid Ledger event
families for future real recovery ownership.

Actual venue reconciliation and coordinated execution recovery remain
later-phase responsibilities.

Phase 2 does not emit fake recovery transitions.

### 99.4. LOCAL / VENUE STATE

ExecutionOrder now persists independently:

`status`
→ canonical local materialized state.

`venue_state`
→ last-known observed venue state.

`venue_state_observed_at`
→ observation timestamp.

No synthetic venue state is inferred from local status.

Alembic migration:

`d7f4b2a91c6e`

Database verified at:

`d7f4b2a91c6e (head)`.

### 99.5. RESTART / RECOVERY PROOF

Fresh-session PostgreSQL E2E verified:

session #1
→ persist aggregate
→ commit
→ session closes.

session #2
→ fresh ExecutionApplicationService
→ same canonical request
→ reread persisted aggregate
→ verify immutable GROUP_CREATED evidence
→ verify legs/orders
→ no duplicate plans/groups/legs/orders/events.

Focused restart E2E:

`1 passed`

`restart_e2e_exit=0`

Cleanup executed through a separate AsyncSessionLocal boundary.

### 99.6. FINAL REGRESSION

Final Trading Core V2 combined regression:

`64 passed`

`core_v2_final_exit=0`

Verified no regression across:

- execution models;
- ExecutionLedgerEvent model;
- ExecutionRepository;
- ExecutionApplicationService;
- order lifecycle;
- fill ingestion;
- PositionLeg lifecycle;
- restart E2E.

### 99.7. PHASE 2 REQUIRED PROPERTIES

Restart-safe:
VERIFIED.

Idempotent:
VERIFIED.

Auditable:
VERIFIED.

Multi-user identity isolation:
retained through user/account-scoped canonical persistence contracts and
foreign-key lineage already verified in Phase 2 foundation work.

Immutable historical event trail:
VERIFIED.

Explicit local / venue order state:
VERIFIED.

### 99.8. PRODUCTION SAFETY

No VenueAdapter query was activated as part of Phase 2.

No ExecutionBoundary call was introduced.

No BingX order submission/cancellation path was changed.

Restricted Live remains DISABLED.

Full Live remains DISABLED.

AI direct exchange access remains BLOCKED.

Strategy Decision Engine AI promotion path remains SHADOW-ONLY.

### 99.9. STATUS

`TRADING_CORE_V2_LEDGER — TEST VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_LEDGER_OK`

### 99.10. PHASE STATUS

`PHASE 2 — ORDER / POSITION LEDGER V2 — DONE`

Canonical Phase 2 gate is CLOSED.

Phase 3 may begin only as a separate canonical step:

`EXCHANGE RECONCILIATION`

No Phase 3 implementation is started by this Audit entry.

### 99.11. PRIMARY NEXT STEP

Begin Phase 3 FACT/CHECK only:

`EXCHANGE RECONCILIATION`

First action:

re-read the canonical Phase 3 requirements from this Audit and inspect
existing venue query / order state retrieval capabilities before any
implementation.

## 100. Trading Core V2 — Multi-Venue Adapter Architecture / Capability Matrix Design — 2026-09-03

### 100.1. OBJECTIVE

Phase 3 Exchange Reconciliation must be multi-venue by design.

NEXUS must not implement a BingX-specific reconciliation architecture
and later duplicate that architecture for each additional exchange.

Canonical target:

exchange-specific transport
→ venue-specific adapter
→ NEXUS canonical venue contracts
→ shared Reconciliation Engine.

### 100.2. CANONICAL ARCHITECTURE

Required boundary:

BingXClient
→ BingXVenueAdapter

BinanceClient
→ BinanceVenueAdapter

BybitClient
→ BybitVenueAdapter

OKXClient
→ OKXVenueAdapter

future exchange client
→ corresponding VenueAdapter

All concrete adapters implement the same canonical:

`VenueAdapter`

contract.

The shared Reconciliation Engine must consume canonical venue contracts
only.

It must not parse exchange-specific raw dictionaries.

### 100.3. REFERENCE-FIRST ENGINEERING

Approved GitHub/reference stack:

P0 mapping reference:

`CCXT`

Use for:

- exchange capability discovery;
- order normalization semantics;
- open-order semantics;
- trade/fill semantics;
- position normalization;
- exchange-specific status mappings;
- pagination and capability differences.

P0 connector architecture reference:

`Hummingbot`

Use for:

- connector separation;
- perpetual connector behavior;
- order-state normalization;
- hedge / one-way position semantics;
- private user-stream patterns;
- connector lifecycle patterns.

P0 production architecture reference:

`NautilusTrader`

Use for:

- strict venue identity;
- deterministic adapter boundaries;
- execution/reconciliation separation;
- multi-venue architecture;
- production-safe event-driven patterns.

No external project is copied wholesale.

No external framework becomes canonical NEXUS domain ownership by default.

NEXUS canonical contracts remain authoritative.

### 100.4. INITIAL VENUE CERTIFICATION PRIORITY

P0:

- BingX;
- Binance USD-M;
- Bybit;
- OKX.

P1:

- Bitget;
- Gate.io;
- KuCoin Futures;
- Hyperliquid.

P2 candidates:

- BitMEX;
- Deribit;
- Kraken Futures;
- MEXC;
- HTX;
- Coinbase International;
- Backpack.

P2 remains backlog and is not implementation scope yet.

### 100.5. REQUIRED CAPABILITY MATRIX

Every concrete VenueAdapter must explicitly declare and test support for:

ORDER DISCOVERY

- get_order;
- get_open_orders;
- historical order discovery if available.

FILLS

- fill/trade discovery;
- venue_fill_id;
- order-to-fill linkage;
- fill quantity;
- fill price;
- fill timestamp.

POSITIONS

- active position discovery;
- native symbol;
- LONG / SHORT identity;
- hedge-mode identity;
- size;
- entry price;
- leverage where available.

ORDER IDENTITY

- client_order_id;
- venue_order_id;
- account identity;
- venue identity;
- native instrument identity.

ORDER STATE

Canonical normalized states:

- PENDING;
- ACCEPTED;
- PARTIALLY_FILLED;
- FILLED;
- CANCELLED;
- REJECTED;
- UNKNOWN.

SAFETY / EXECUTION METADATA

- reduce_only;
- hedge / one-way position mode;
- sandbox / demo availability;
- rate-limit behavior;
- pagination behavior;
- unsupported capability behavior;
- UNKNOWN status fail-safe behavior.

TRANSPORT

- REST query support;
- private WebSocket/user-stream support when available.

### 100.6. CAPABILITY-DRIVEN RECONCILIATION

Reconciliation must not assume every exchange exposes the same APIs.

Example:

one venue may provide:

get_order
+ get_open_orders
+ fills
+ positions.

Another venue may not provide complete historical order discovery.

Therefore reconciliation behavior must depend on explicit:

`VenueCapabilities`

rather than exchange-name conditionals.

Unsupported capability must be explicit and fail safely.

### 100.7. CANONICAL RECONCILIATION INPUTS

Phase 3 will require canonical representations for:

- venue order state;
- venue positions;
- venue fills/trades.

Existing:

`VenueOrderResult`

remains canonical for order observations unless a separately approved
contract evolution is required.

Position and fill observation contracts must be designed before their
first concrete adapter implementation.

### 100.8. RAW EXCHANGE DATA BOUNDARY

Raw exchange payload fields such as:

- orderId;
- clientOrderId;
- executedQty;
- avgPrice;
- positionAmt;
- positionSide;

must remain inside exchange-specific transport/adapter boundaries.

Shared reconciliation logic must never depend directly on those raw
field names.

### 100.9. BINGX CURRENT FACT

Current BingX client already provides raw/query primitives including:

- get_order;
- get_open_orders;
- get_positions.

Current BingX code also contains partial normalization for:

- orderId;
- avgPrice;
- executedQty;
- status;
- position side;
- position size;
- entry price.

However:

`BingXVenueAdapter`

does not currently exist.

Raw BingX data is not yet normalized into canonical VenueAdapter results.

### 100.10. IMPLEMENTATION SEQUENCE

Canonical implementation sequence:

1. complete shared reconciliation observation contracts;
2. define generic VenueAdapter contract-test suite;
3. implement BingXVenueAdapter;
4. certify BingX adapter;
5. implement BinanceVenueAdapter;
6. certify Binance adapter;
7. implement BybitVenueAdapter;
8. certify Bybit adapter;
9. implement OKXVenueAdapter;
10. certify OKX adapter;
11. add P1 venues through the same certification template.

This sequence must not create separate reconciliation engines per venue.

### 100.11. PHASE 3 RECONCILIATION REQUIREMENTS

Shared Reconciliation Engine remains responsible for:

- active positions;
- open orders;
- fill matching;
- missing local fill detection;
- stale local position detection;
- unknown exchange order detection;
- restart recovery;
- deterministic repeated reconciliation;
- discrepancy reporting.

No automatic destructive correction is allowed without an approved
policy.

### 100.12. PRODUCTION SAFETY

This design does not activate:

- Restricted Live;
- Full Live;
- AI direct exchange access.

No new exchange order submission path is introduced.

No ExecutionBoundary access is changed.

Phase 3 reconciliation remains observation/reconciliation work until a
separate approved policy explicitly authorizes any corrective action.

### 100.13. STATUS

`TRADING_CORE_V2_MULTI_VENUE_ADAPTER_ARCHITECTURE — DESIGN VERIFIED / DONE`

Evidence tag:

`TRADING_CORE_V2_MULTI_VENUE_ADAPTER_ARCHITECTURE_OK`

### 100.14. PRIMARY NEXT STEP

Design the missing canonical Phase 3 observation contracts for:

- venue positions;
- venue fills/trades.

Do not implement BingXVenueAdapter until those shared contracts are
defined, so the first adapter becomes the reusable template for all
later venues.

Target:

`TRADING_CORE_V2_RECONCILIATION_OBSERVATION_CONTRACTS_OK`

## NEXUS V2 Phase 0 — Architecture / Roadmap Transition — 2026-09-03

### FACT

NEXUS V2 development has started as a new canonical architecture/repository.

The legacy `nexus-engine` remains:
- temporary production/runtime host;
- source of verified legacy behavior;
- migration/parity reference.

Legacy is not being converted in-place into V2.

New local V2 repository:

`C:\Projects\nexus-v2`

GitHub remote:

`git@github.com:gon4arenkoe-eng/nexus-v2.git`

Initial governance baseline commit:

`afe4449 chore: bootstrap NEXUS V2 governance baseline`

The baseline commit contains only:

- `NEXUS_V2_MASTER_PLAN.md`
- `NEXUS_V2_FUNCTIONAL_INVENTORY.md`
- `NEXUS_PROJECT_AUDIT.md`

### CHECK

Verified locally:

- Git installation available;
- GitHub SSH authentication successful;
- new `nexus-v2` repository initialized/cloned;
- `origin` points to `git@github.com:gon4arenkoe-eng/nexus-v2.git`;
- branch is `main`;
- canonical governance documents are present;
- only the three canonical documents were included in the root commit;
- public-repository secret pattern check returned no matches;
- production host was not modified;
- no legacy source tree was copied into V2.

### EVIDENCE

- `LOCAL_GIT_OK`
- `GITHUB_SSH_AUTH_OK`
- `NEXUS_V2_LOCAL_REPO_OK`
- `NEXUS_V2_REMOTE_OK`
- `CANONICAL_DOCS_PRESENT_OK`
- `CANONICAL_FILES_ONLY_OK`
- `PUBLIC_REPO_SECRET_CHECK_OK`
- `NEXUS_V2_GOVERNANCE_BASELINE_COMMIT_OK`
- Git commit: `afe4449`

### PLAN DEVIATION

Original `NEXUS_V2_MASTER_PLAN.md` Phase 0 specifies a private GitHub monorepo.

Private repository creation was unavailable in the selected GitHub setup.

User explicitly approved:

`Public GitHub repository for NEXUS V2`

Therefore:

`PLAN DEVIATION APPROVED — PUBLIC REPOSITORY`

Public repository safety requirement:

- `.env` prohibited;
- credentials prohibited;
- API/exchange secrets prohibited;
- private keys prohibited;
- production DB dumps prohibited;
- sensitive logs/backups prohibited;
- secret-bearing history prohibited.

This approved deviation does not grant permission to change any other Master Plan requirement.

### STATUS

`ARCHITECTURE/ROADMAP APPROVED`

Phase 0 is **IN PROGRESS**.

This status does not mean Phase 0 implementation is DONE.

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

### GAP

Still required for Phase 0:

- register this Audit transition in Git history;
- publish verified governance baseline to GitHub;
- establish repository/directory/contracts policy;
- establish CI skeleton;
- establish local development baseline;
- keep production unchanged.

### NEXT STEP

Publish the audited governance baseline to the approved GitHub repository after committing this Audit update.

Production remains unchanged.

Live authority remains disabled according to NEXUS V2 production safety policy.

## NEXUS V2 Phase 0 — Directory Baseline — 2026-09-03

### FACT

The approved NEXUS V2 monorepo directory baseline has been materialized locally.

Created canonical areas:

- `apps/core`
- `apps/intelligence`
- `apps/aiea`
- `apps/web`
- `workers/aiea_research`
- `packages/contracts`
- `packages/testkit`
- `packages/observability`
- `adapters/bingx`
- `adapters/binance`
- `adapters/bybit`
- `adapters/okx`
- `infra/compose`
- `infra/migrations`
- `infra/github`
- `infra/deploy`
- `docs/architecture`
- `docs/runbooks`
- `docs/adr`

Only `.gitkeep` placeholder files were introduced.

No implementation code, legacy source, runtime configuration, CI configuration, Docker configuration, credentials, or production files were added.

### CHECK

Verified locally:

- all 19 approved directories are present;
- all 19 tracked files are `.gitkeep`;
- staged scope contained only the approved directory baseline;
- `git diff --cached --check` returned clean;
- no legacy source tree was copied;
- production was not modified.

### EVIDENCE

- `NEXUS_V2_DIRECTORY_BASELINE_PRESENT`
- `NEXUS_V2_DIRECTORY_SCOPE_OK`
- `NEXUS_V2_DIRECTORY_DIFF_CHECK_OK`
- `NEXUS_V2_DIRECTORY_BASELINE_COMMIT_OK`
- Git commit: `d5c9a33`

### STATUS

Phase 0 remains **IN PROGRESS**.

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

Directory baseline is complete.

Contracts/dependency policy, CI skeleton, and local development baseline remain open.

### NEXT STEP

Establish the NEXUS V2 contracts and dependency-boundary policy before implementation code is introduced.

Production remains unchanged.

## NEXUS V2 Phase 0 — Dependency Boundaries Policy — 2026-09-03

### FACT

The NEXUS V2 dependency-boundary architecture policy has been established before implementation code is introduced.

Canonical policy file:

`docs/architecture/DEPENDENCY_BOUNDARIES.md`

The policy defines:

- repository ownership boundaries;
- canonical dependency direction;
- forbidden dependencies;
- canonical execution ownership;
- VenueAdapter boundary;
- multi-user ownership boundary;
- Grid ownership boundary;
- reconciliation boundary;
- shared contract-change rules;
- future enforcement requirements for Phase 1.

### CHECK

Verified locally:

- only `docs/architecture/DEPENDENCY_BOUNDARIES.md` was staged;
- staged read-back contained the approved architecture policy;
- the file contains 307 lines;
- `git diff --cached --check` returned clean;
- no implementation code was introduced;
- no legacy source was copied;
- production was not modified.

### EVIDENCE

- `NEXUS_V2_DEPENDENCY_POLICY_PRESENT`
- `NEXUS_V2_DEPENDENCY_POLICY_SCOPE_OK`
- `NEXUS_V2_DEPENDENCY_POLICY_READBACK_OK`
- `NEXUS_V2_DEPENDENCY_POLICY_DIFF_OK`
- `NEXUS_V2_DEPENDENCY_POLICY_COMMIT_OK`
- Git commit: `5ba54fc`

### STATUS

Dependency-boundary policy is established.

Phase 0 remains **IN PROGRESS**.

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

Still open in Phase 0:

- CI skeleton;
- local development baseline;
- explicit repository line-ending/config policy;
- final Phase 0 verification and Audit closure.

### NEXT STEP

Publish the dependency-boundary policy commit and its Audit evidence, then proceed to the CI skeleton.

Production remains unchanged.

## NEXUS V2 Phase 0 — Dependency Policy GitHub Publication — 2026-09-03

### FACT

The NEXUS V2 dependency-boundary policy and its Audit evidence have been published to the approved GitHub repository.

Published commits:

- `5ba54fc docs: establish NEXUS V2 dependency boundaries`
- `20cbec1 docs: register NEXUS V2 dependency policy evidence`

### CHECK

Verified after push:

- `main` successfully pushed to `origin`;
- local `main` tracks `origin/main`;
- local HEAD and `origin/main` both resolve to `20cbec1`;
- working tree is clean;
- no production host changes were made.

### EVIDENCE

- `DEPENDENCY_POLICY_PUSH_OK`
- `GITHUB_SYNC_OK_AFTER_DEPENDENCY_POLICY`
- `CLEAN_WORKTREE_OK`
- HEAD: `20cbec1`
- origin/main: `20cbec1`

### STATUS

Dependency-boundary policy cycle is complete.

Phase 0 remains **IN PROGRESS**.

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

Remaining Phase 0 work includes:

- CI skeleton;
- local development baseline;
- repository/line-ending configuration baseline;
- final Phase 0 verification and Audit closure.

### NEXT STEP

Establish the NEXUS V2 CI skeleton without introducing production deployment authority.

Production remains unchanged.

## NEXUS V2 Phase 0 — CI Baseline — 2026-09-03

### FACT

The Phase 0 CI and repository configuration baseline has been established.

Created:

- `.github/workflows/ci.yml`
- `.gitattributes`
- `.editorconfig`
- `.gitignore`
- `infra/github/repo_baseline_check.py`

Implementation commit:

`140ca6e ci: establish NEXUS V2 Phase 0 CI baseline`

### CHECK

Verified locally:

- repository baseline check passed;
- 8 required files were present;
- 19 required directories were present;
- no forbidden deployment-authority markers were present in Phase 0 CI;
- no forbidden secret-sensitive paths were detected;
- staged scope contained exactly 5 CI/repository baseline files;
- `git diff --cached --check` returned clean;
- no production deploy workflow was introduced;
- no production host modification occurred.

### EVIDENCE

- `NEXUS_V2_CI_SKELETON_PRESENT`
- `NEXUS_V2_PHASE0_REPO_BASELINE_CHECK_OK`
- `NEXUS_V2_REPO_CONFIG_BASELINE_OK`
- `NEXUS_V2_CI_NO_DEPLOY_AUTHORITY_OK`
- `NEXUS_V2_SECRET_SENSITIVE_PATH_CHECK_OK`
- `NEXUS_V2_CI_SCOPE_OK`
- `NEXUS_V2_CI_DIFF_CHECK_OK`
- `NEXUS_V2_CI_BASELINE_COMMIT_OK`
- Git commit: `140ca6e`

### STATUS

Phase 0 CI skeleton is locally verified.

Gate remains:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

Remaining Phase 0 work:

- local development baseline;
- final Phase 0 verification;
- final Audit closure.

### NEXT STEP

Publish the CI baseline and verify the GitHub Actions run.

Production remains unchanged.

## NEXUS V2 Phase 0 — Local Development Baseline — 2026-09-03

### FACT

The Phase 0 local development/devcontainer baseline has been established and locally verified.

Created or updated:

- `.devcontainer/devcontainer.json`
- `.python-version`
- `pyproject.toml`
- `scripts/dev_check.py`
- `docs/runbooks/LOCAL_DEVELOPMENT.md`
- `.github/workflows/ci.yml`
- `infra/github/repo_baseline_check.py`

### CHECK

Verified locally with Python 3.13.14:

- `NEXUS_V2_PHASE0_LOCAL_DEV_BASELINE_OK`;
- Python contract is 3.13;
- devcontainer environment is `development`;
- live authority is disabled;
- production build authority is disabled;
- production deploy authority is disabled;
- repository baseline check passed;
- 13 required files are present;
- 19 required directories are present;
- no deployment authority is present in Phase 0 CI;
- no forbidden secret-sensitive paths were detected;
- `git diff --cached --check` returned clean.

### EVIDENCE

- `NEXUS_V2_LOCAL_DEV_FILES_PRESENT`
- `NEXUS_V2_PYTHON_313_CONTRACT_OK`
- `NEXUS_V2_DEVCONTAINER_BASELINE_OK`
- `NEXUS_V2_LOCAL_DEV_NO_LIVE_AUTHORITY_OK`
- `NEXUS_V2_LOCAL_DEV_NO_PROD_BUILD_OK`
- `NEXUS_V2_PHASE0_LOCAL_DEV_BASELINE_OK`
- `NEXUS_V2_PHASE0_REPO_BASELINE_CHECK_OK`
- `NEXUS_V2_LOCAL_DEV_DIFF_CHECK_OK`

### CI EVIDENCE

The corrected Phase 0 GitHub Actions workflow for commit `f3449fc` passed on the hosted GitHub runner.

Verified hosted steps:

- `actions/checkout@v7` — PASS;
- `actions/setup-python@v7` — PASS;
- `python infra/github/repo_baseline_check.py` — PASS;
- `git diff --check HEAD^ HEAD` — PASS.

Evidence:

- `GITHUB_ACTIONS_CI_RUN_OK`
- `NEXUS_V2_CI_BASELINE — TEST VERIFIED`

### STATUS

Phase 0 remains **IN PROGRESS** pending final gate verification.

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — OPEN`

### NEXT STEP

Publish the local development baseline and run final Phase 0 verification against the Master Plan, Audit, Inventory, repository state, and hosted CI.

Production remains unchanged.

## NEXUS V2 Phase 0 — FOUNDATION GATE CLOSURE — 2026-09-03

### FACT

NEXUS V2 Phase 0 — Architecture/repository foundation has completed its required implementation and verification scope.

Canonical Phase 0 foundation now includes:

- approved NEXUS V2 roadmap/governance baseline;
- frozen functional inventory baseline;
- public GitHub monorepo;
- canonical directory baseline;
- dependency-boundary policy;
- Phase 0 CI skeleton;
- repository configuration baseline;
- Python 3.13 local development contract;
- reproducible devcontainer baseline;
- local development runbook;
- repository and local-development verification scripts.

### FULL AUDIT CHECK

Verified against the Phase 0 Master Plan requirements:

- repository bootstrap — VERIFIED;
- canonical V2 directory baseline — VERIFIED;
- dependency/contracts boundary policy — VERIFIED;
- CI skeleton — TEST VERIFIED;
- local/devcontainer environment — TEST VERIFIED;
- repository baseline verification — TEST VERIFIED;
- no production build/deploy authority introduced — VERIFIED;
- production runtime unchanged — VERIFIED.

Functional Inventory remains the mandatory parity source for future legacy → V2 migration.

No legacy implementation was copied wholesale into V2.

### FINAL TEST EVIDENCE

Current repository state:

`HEAD = origin/main = 8bce024f4d1e4b0eebdd75f92c3d24b9cca16903`

Final local verification:

- `NEXUS_V2_PHASE0_REPO_BASELINE_CHECK_OK`;
- `NEXUS_V2_PHASE0_LOCAL_DEV_BASELINE_OK`;
- Python `3.13.14`;
- required files = `13`;
- required directories = `19`;
- no Phase 0 deployment authority;
- no forbidden secret-sensitive paths;
- live authority disabled;
- production build/deploy authority false;
- `git diff --check` clean;
- working tree clean;
- local HEAD equals `origin/main`.

Final hosted GitHub Actions run for current main:

- repository checkout — PASS;
- Python setup — PASS;
- repository baseline check — PASS;
- local development baseline check — PASS;
- Git whitespace check — PASS.

Evidence:

- `FINAL_PHASE0_LOCAL_RECHECK_OK`
- `CURRENT_MAIN_HOSTED_CI_OK`
- `NEXUS_V2_PHASE0_REPO_BASELINE_CHECK_OK`
- `NEXUS_V2_PHASE0_LOCAL_DEV_BASELINE_OK`
- `NEXUS_V2_PYTHON_313_CONTRACT_OK`
- `NEXUS_V2_DEVCONTAINER_BASELINE_OK`
- `NEXUS_V2_CI_BASELINE_TEST_VERIFIED`
- `NEXUS_V2_NO_PRODUCTION_CHANGE_OK`
- `NEXUS_V2_FOUNDATION_PLAN_OK`

### STATUS

`Phase 0 — DONE / TEST VERIFIED`

Gate:

`NEXUS_V2_FOUNDATION_PLAN_OK — CLOSED`

The project may proceed to:

`Phase 1 — Shared contracts/testkit`

Production safety remains unchanged.

### NEXT STEP

Begin Phase 1 with a FACT/CHECK of the canonical shared contracts and testkit requirements before implementing the first Phase 1 contract baseline.

---

## 2026-09-05 — NEXUS V2 Product Architecture Additions

**Status:** DESIGN APPROVED / GIT VERIFIED

Approved architecture additions:

- AIEA Product Moat Spec;
- Product Entitlements / Subscriptions / Quotas;
- NEXUS Trading Workspace Composer.

Canonical documents updated:

- `NEXUS_V2_MASTER_PLAN.md` → v1.2-draft;
- `NEXUS_V2_FUNCTIONAL_INVENTORY.md` → v1.1-draft.

Git evidence:

- commit: `79329d6`
- message: `docs: add AIEA moat entitlements and workspace composer`
- branch: `main`
- remote: `origin/main`
- local/remote synchronization: VERIFIED

Evidence tags:

- `NEXUS_V2_AIEA_MOAT_SPEC_DESIGN_APPROVED`
- `NEXUS_V2_ENTITLEMENT_ARCHITECTURE_DESIGN_APPROVED`
- `NEXUS_V2_WORKSPACE_COMPOSER_DESIGN_APPROVED`
- `NEXUS_V2_PRODUCT_ARCHITECTURE_GIT_VERIFIED_OK`

Important status boundary:

- architecture/design = APPROVED;
- implementation = NOT DONE;
- no Phase 9/10/11 implementation status is promoted by this documentation change;
- production authority is unchanged.

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Canonical Identity Contracts

**Status:** TEST VERIFIED

Implemented canonical shared identity contracts in the V2 monorepo:

- `packages/contracts/identities.py`
- `packages/contracts/__init__.py`
- `tests/test_contract_identities.py`
- `tests/__init__.py`

Implemented contracts:

- `AssetClass`
- `InstrumentType`
- `VenueId`
- `AccountId`
- `InstrumentId`

Verified invariants:

- identities are immutable;
- `VenueId` is non-empty and normalized;
- `AccountId` is venue-aware and requires a positive integer identity;
- `InstrumentId` is venue-aware;
- native symbol is non-empty and normalized;
- instrument type is part of identity;
- asset class is part of identity;
- the same native ticker on different venues produces different `InstrumentId` values;
- no exchange SDK / SQLAlchemy / FastAPI / HTTP client dependency exists in `packages/contracts`.

Verification evidence:

- Python: `3.13.14`
- focused pytest: `16 passed`
- compile: PASS
- `scripts/dev_check.py`: PASS
- staged diff check: PASS
- EOF newline check: PASS
- forbidden-import check: PASS

Evidence tag:

- `TRADING_CORE_V2_IDENTITY_CONTRACTS_OK`

Important scope boundary:

- TradeIntent was NOT implemented in this step;
- no SQLAlchemy models or migrations changed;
- no exchange adapters changed;
- no production permissions changed;
- no live authority expanded.

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Numeric / Time Conventions

**Status:** TEST VERIFIED

Implemented canonical shared numeric and time conventions:

- `packages/contracts/primitives.py`
- `tests/test_contract_primitives.py`

Numeric conventions verified:

- canonical financial validation accepts `Decimal` only;
- binary float is not accepted as canonical financial input;
- non-finite Decimal values fail closed;
- positive Decimal validation rejects zero and negative values;
- non-negative Decimal validation permits zero and rejects negative values;
- no venue tick-size / lot-size rounding is performed;
- no venue-native numeric conversion is performed.

Time conventions verified:

- canonical datetime input must be timezone-aware;
- naive datetime fails closed;
- timezone-aware datetime is normalized to UTC;
- already-UTC datetime remains UTC.

Verification evidence:

- Python: `3.13.14`
- focused primitives pytest: `18 passed`
- identity regression pytest: `16 passed`
- full current pytest suite: `34 passed`
- compile: PASS
- `scripts/dev_check.py`: PASS
- staged diff check: PASS
- forbidden-import check: PASS

Scope boundary:

- no `Money`, `Price`, or `Quantity` wrapper classes introduced;
- no Clock implementation introduced;
- no EventEnvelope introduced;
- no TradeIntent or Core Phase 2 contracts changed;
- no adapter or exchange rounding introduced;
- no production authority changed.

Evidence tag:

- `NEXUS_V2_NUMERIC_TIME_CONVENTIONS_OK`

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Typed Event Envelope

**Status:** TEST VERIFIED

Implemented reusable shared typed event envelope:

- `packages/contracts/events.py`
- `tests/test_contract_events.py`

Canonical shared event semantics verified:

- immutable/frozen `EventEnvelope`;
- generic typed payload;
- required `event_id`;
- required `event_type`;
- positive integer `event_version`;
- required `source`;
- required timezone-aware `occurred_at`;
- required timezone-aware `recorded_at`;
- event timestamps normalize to UTC;
- `occurred_at` and `recorded_at` remain semantically distinct;
- optional `correlation_id`;
- optional `causation_id`;
- empty required/optional lineage text fails closed.

Scope boundary:

- no execution-specific lineage added to shared contracts;
- no `user_id`, `execution_plan_id`, group/leg/order/fill/account/venue ownership added here;
- no EventType enum introduced;
- no automatic event ID generation introduced;
- no automatic clock / `recorded_at` generation introduced;
- no event sequence/reconnect delivery semantics introduced;
- no WebSocket/Event Gateway implementation introduced;
- no SQLAlchemy/FastAPI/exchange SDK dependency introduced.

Compatibility with verified Ledger semantics:

- preserves `event_id`;
- preserves `event_type`;
- preserves `event_version`;
- preserves `source`;
- preserves `occurred_at`;
- preserves `recorded_at`;
- preserves `correlation_id`;
- preserves `causation_id`;
- preserves generic payload boundary.

Verification evidence:

- Python: `3.13.14`
- focused event tests: `18 passed`
- all contract tests: `52 passed`
- full current pytest suite: `52 passed`
- compile: PASS
- `scripts/dev_check.py`: PASS
- staged diff check: PASS
- forbidden-import check: PASS

Evidence tag:

- `NEXUS_V2_TYPED_EVENT_ENVELOPE_OK`

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Error / Result Contracts

**Status:** TEST VERIFIED

Implemented canonical shared operational result contracts:

- `packages/contracts/results.py`
- `tests/test_contract_results.py`

Implemented shared contracts:

- immutable `ErrorInfo`;
- immutable generic `Success[T]`;
- immutable `Failure`;
- typed `Result[T] = Success[T] | Failure`.

Verified `ErrorInfo` semantics:

- required stable machine-readable `code`;
- required human-readable `message`;
- explicit boolean `retryable`;
- required text is normalized by trimming;
- empty required text fails closed;
- invalid `retryable` types fail closed.

Verified result semantics:

- `Success[T]` preserves typed values;
- `Success(None)` is valid;
- `Failure` requires canonical `ErrorInfo`;
- result objects are immutable.

Scope boundary:

- no FastAPI dependency;
- no `HTTPException`;
- no HTTP status ownership;
- no headers/transport semantics;
- no Core execution ownership;
- no exception serialization;
- no automatic logging behavior;
- invariant validation continues to use fail-fast exceptions where appropriate.

Canonical separation:

- invariant/programming violation → exception;
- expected operational failure → `Failure(ErrorInfo)`;
- expected success → `Success[T]`;
- HTTP/API representation remains adapter/API-layer responsibility.

Verification evidence:

- focused result tests: `22 passed`;
- all contract tests: `74 passed`;
- full current pytest suite: `74 passed`;
- compile: PASS;
- `scripts/dev_check.py`: PASS;
- forbidden-import check: PASS;
- staged diff check: PASS.

Evidence tag:

- `NEXUS_V2_ERROR_RESULT_CONTRACTS_OK`

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Deterministic Clock / ID Providers

**Status:** TEST VERIFIED

Implemented shared provider contracts:

- `packages/contracts/providers.py`
  - `Clock`
  - `IdProvider`

Implemented deterministic testkit providers:

- `packages/testkit/deterministic.py`
  - `DeterministicClock`
  - `SequenceIdProvider`
- `packages/testkit/__init__.py`
- `tests/test_deterministic_providers.py`

Clock contract and deterministic semantics verified:

- `Clock.now()` is dependency-supplied;
- deterministic clock requires timezone-aware datetime;
- time normalizes to UTC;
- deterministic time can be explicitly set;
- deterministic time can be advanced by an exact timedelta;
- zero advance is valid;
- negative advance fails closed;
- non-timedelta advance fails closed.

ID provider semantics verified:

- `IdProvider.next_id()` is dependency-supplied;
- deterministic sequence preserves explicit ID order;
- repeated identical sequences produce identical IDs;
- IDs are normalized by trimming;
- empty/non-string IDs fail closed;
- exhausted deterministic sequence fails explicitly;
- no random/UUID generation occurs inside the deterministic provider.

Architecture boundary:

- provider interfaces live in shared contracts;
- deterministic mutable implementations live in testkit;
- no production clock implementation introduced;
- no production ID-generation strategy introduced;
- no generic provider defines Ledger event-ID derivation;
- domain-specific deterministic Ledger identity rules remain separate;
- no wall-clock ownership introduced into contracts/testkit;
- no SQLAlchemy/FastAPI/exchange SDK dependency introduced.

Explicitly absent from this changeset:

- `datetime.now()`;
- `datetime.utcnow()`;
- `time.time()`;
- `uuid4()`;
- random ID generation.

Verification evidence:

- focused deterministic-provider tests: `18 passed`;
- full current pytest suite: `92 passed`;
- compile: PASS;
- `scripts/dev_check.py`: PASS;
- forbidden dependency scan: PASS;
- nondeterministic source scan: PASS;
- staged diff check: PASS.

Evidence tag:

- `NEXUS_V2_DETERMINISTIC_CLOCK_ID_PROVIDERS_OK`

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Fake Venue Testkit

**Status:** TEST VERIFIED

Implemented deterministic generic fake venue test infrastructure:

- `packages/testkit/fake_venue.py`
- `tests/test_fake_venue.py`

Implemented behavior:

- scripted FIFO submit outcomes;
- scripted FIFO cancel outcomes;
- deterministic submit call recording;
- deterministic cancel call recording;
- immutable recorded-call views;
- explicit failure when scripted result sequence is exhausted;
- attempted submit/cancel is recorded before missing-result failure;
- cancel `client_order_id` is normalized by trimming;
- invalid cancel identity fails closed;
- fake venue preserves arbitrary scripted outcomes without interpreting venue lifecycle semantics.

Architecture boundary:

- FakeVenue lives in `packages/testkit`;
- no exchange SDK dependency;
- no SQLAlchemy/FastAPI dependency;
- no canonical VenueAdapter DTO was redefined;
- no `VenueOrderState`;
- no `VenueOrderRequest`;
- no `VenueOrderResult`;
- no `VenuePosition`;
- no `VenueFill`;
- no Reconciliation ownership;
- no ExecutionCoordinator ownership;
- no production exchange access.

Scope intent:

- FakeVenue is a deterministic programmable test boundary only;
- verified legacy VenueAdapter semantics remain migration input for Phase 2;
- Phase 3 position/fill observation contracts are not pulled forward;
- unknown-outcome/recovery policy remains owned by later execution/reconciliation phases.

Verification evidence:

- focused FakeVenue tests: `17 passed`;
- full current pytest suite: `109 passed`;
- compile: PASS;
- `scripts/dev_check.py`: PASS;
- precise forbidden-import check: PASS;
- premature canonical-contract check: PASS;
- staged diff check: PASS.

Evidence tag:

- `NEXUS_V2_FAKE_VENUE_TESTKIT_OK`

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

---

## 2026-09-05 — Phase 1 Shared Contracts Gate Closure

**Status:** GIT PUBLISHED / HOSTED CI VERIFIED

### FACT

Phase 1 shared-contract and testkit scope is complete locally.

The canonical shared baseline includes:

- identity, numeric/time, event-envelope and error/result contracts;
- deterministic clock/ID providers and generic FakeVenue testkit;
- stable product-access contracts: `FeatureKey`, `EntitlementDecision`,
  `QuotaResult`;
- typed, presentation-only workspace contracts: `WidgetManifest`,
  `WidgetSize`, `WidgetPlacement`, `WorkspaceLayout`, `WidgetContext` and
  `ContextKey`;
- public-contract compatibility tests for all Phase 1 contract surfaces.

The product-access contracts are tenant-scoped decisions only. They do not
model commercial plan names, payment providers, RBAC, billing, usage-counter
mutation, Risk permissions or live-trading authority. Workspace contracts are
layout/context metadata only; they do not execute trades or mutate Core state.

### CHECK

- full shared-contract suite: `144 passed` on Python `3.13.14`;
- Phase 1 local development verification: PASS;
- repository foundation verification: PASS;
- whitespace verification: PASS;
- precise external dependency import scan across `packages/contracts` and
  `packages/testkit`: PASS;
- CI now installs `pytest` and executes the full shared-contract suite;
- `tool.nexus.phase` is `1`;
- production build/deploy authority remains `false`;
- devcontainer live authority remains `disabled`.

### EVIDENCE

- `NEXUS_V2_SHARED_CONTRACTS_OK`
- `NEXUS_V2_PHASE1_LOCAL_DEV_BASELINE_OK`
- `NEXUS_V2_PHASE1_COMPATIBILITY_TESTS_OK`
- `NEXUS_V2_PRODUCT_ACCESS_CONTRACTS_OK`
- `NEXUS_V2_WORKSPACE_COMPOSER_CONTRACTS_OK`
- `NEXUS_V2_PHASE1_NO_PRODUCTION_AUTHORITY_OK`

### STATUS

`Phase 1 — DONE / TEST VERIFIED`

Gate:

`NEXUS_V2_SHARED_CONTRACTS_OK — CLOSED`

Implementation commit `1473bf5` was pushed to `origin/main`; local `HEAD` and
`origin/main` resolve to the same commit. The user confirmed the GitHub Actions
workflow for the published Phase 1 changes completed green.

Hosted CI evidence:

- repository baseline — PASS;
- Phase 1 local development baseline — PASS;
- shared contract suite — PASS;
- Git whitespace check — PASS.

### NEXT STEP

Publish the Phase 1 closure changes, verify the hosted CI run, then begin
Phase 2 with a FACT/CHECK of the verified existing Core V2 foundation before
migrating any TradeIntent, Venue, Ledger or execution contract.
---

## 2026-09-05 — Phase 2 TradeIntent Migration

**Phase:** 2 — Import and harden existing Core V2 foundation

**Status:** TEST VERIFIED

Migrated the previously verified canonical TradeIntent semantics into the
new NEXUS V2 monorepo Core domain without recreating the contract design.

Implemented:

- `apps/core/__init__.py`
- `apps/core/domain/__init__.py`
- `apps/core/domain/intents.py`
- `tests/test_core_trade_intents.py`

Canonical contracts:

- `TradeIntentKind`
- `TradeIntentShape`
- `TradeSide`
- `TradeLegIntent`
- `TradeIntent`

Preserved verified semantics:

- OPEN / CLOSE / REDUCE / REBALANCE intent kinds;
- SINGLE_LEG / PAIR / BASKET shapes;
- BUY / SELL sides;
- SINGLE_LEG requires exactly one leg;
- PAIR requires exactly two legs;
- BASKET requires at least two legs;
- leg IDs must be unique;
- optional quantity remains supported;
- provided quantity must be positive;
- account venue must match instrument venue;
- cross-venue PAIR remains supported through per-leg ownership;
- TradeIntent remains immutable;
- empty intent identity fails closed;
- metadata is copied into an immutable mapping;
- created_at uses canonical UTC normalization.

Shared Phase 1 contracts are reused:

- `VenueId`
- `AccountId`
- `InstrumentId`
- `AssetClass`
- `InstrumentType`
- numeric/time primitives

No duplicate identity contracts were introduced.

Architectural boundary verified:

- Core domain does not import SQLAlchemy;
- Core domain does not import FastAPI;
- Core domain does not import exchange SDK/client implementations;
- TradeIntent does not call VenueAdapter;
- TradeIntent does not own reconciliation;
- TradeIntent does not own ExecutionCoordinator behavior;
- no Phase 3/4 execution capability was pulled forward.

Verification:

- focused TradeIntent tests: `13 passed`;
- full repository test suite: `157 passed`;
- Python compileall: PASS;
- forbidden Core import check: PASS;
- premature Phase 3/4 ownership guard: PASS;
- `git diff --check`: PASS.

Migration principle:

Verified legacy/Core V2 behavior was preserved while the implementation
was placed cleanly inside the new canonical V2 architecture.

No production execution authority was introduced.

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.

Historical source evidence remains:

`TRADING_CORE_V2_TRADE_INTENT_CONTRACTS_OK`

New V2 migration evidence:

`NEXUS_V2_TRADE_INTENT_MIGRATION_OK`

The Phase 2 aggregate gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
---

## 2026-09-05 — Phase 2 Venue Order Contracts Migration

**Phase:** 2 — Import and harden existing Core V2 foundation

**Status:** TEST VERIFIED

Migrated and hardened the previously verified canonical Venue order
contracts into the new NEXUS V2 Core port layer.

Implemented:

- `apps/core/ports/__init__.py`
- `apps/core/ports/venue.py`
- `tests/test_core_venue_contracts.py`

Canonical contracts:

- `VenueCapability`
- `VenueCapabilities`
- `VenueOrderState`
- `VenueOrderSide`
- `VenueOrderType`
- `VenueOrderRequest`
- `VenueOrderResult`
- abstract `VenueAdapter`

Preserved verified behavior:

- supported capabilities pass;
- unsupported capabilities fail closed;
- unknown capabilities fail closed;
- MARKET orders reject limit_price;
- LIMIT orders require positive limit_price;
- account venue must match instrument venue;
- order request remains immutable;
- partial fills remain explicitly supported;
- FILLED requires full requested quantity;
- REJECTED requires a rejection reason;
- UNKNOWN remains an explicit order state.

Approved V2 hardening:

- canonical order quantities use `Decimal`;
- canonical limit prices use `Decimal`;
- requested and filled quantities use `Decimal`;
- average fill price uses `Decimal`;
- float quantity input fails closed;
- venue-native numeric conversion is deferred to adapter implementations.

Architectural boundary verified:

- no SQLAlchemy in Core port;
- no FastAPI in Core port;
- no exchange SDK/client dependency in Core port;
- no raw venue payload ownership in canonical contract;
- no reconciliation ownership introduced;
- no VenuePosition / VenueAccountState / VenueFill observation contract
  pulled forward from Phase 3;
- no ExecutionCoordinator implementation introduced.

Verification:

- focused Venue contract tests: `16 passed`;
- adjacent TradeIntent + Venue tests: `29 passed`;
- full repository suite: `173 passed`;
- Python compileall: PASS;
- Decimal ownership check: PASS;
- forbidden Core dependency check: PASS;
- Phase 3 leakage check: PASS;
- `git diff --check`: PASS.

Historical source evidence:

`TRADING_CORE_V2_VENUE_ADAPTER_CONTRACTS_OK`

New migration evidence:

`NEXUS_V2_VENUE_ORDER_CONTRACTS_MIGRATION_OK`

Phase 2 aggregate gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`

No production execution authority was introduced.

Production safety remains:

- Strategy Decision Engine AI path = SHADOW-ONLY;
- Advisory = OBSERVE_ONLY;
- Restricted Live = DISABLED;
- Full Live = DISABLED;
- AI direct exchange access = BLOCKED.
## 2026-09-05 — Phase 2 Canonical Order Types Domain Ownership

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Scope:
- corrected canonical ownership of generic order side/type semantics;
- removed VenueOrderSide;
- removed VenueOrderType;
- introduced apps/core/domain/orders.py;
- canonical OrderSide values: BUY, SELL;
- canonical OrderType values: MARKET, LIMIT;
- updated VenueOrderRequest to consume canonical Core Domain types directly;
- updated venue contract tests to consume canonical Core Domain types directly.

Architecture:
- OrderSide and OrderType are generic Core trading semantics, not venue-owned semantics;
- Core Domain does not import apps.core.ports;
- Venue port imports canonical domain order types;
- no compatibility aliases or temporary duplicate order enums remain;
- venue-specific adapters remain responsible for future canonical-to-native mapping;
- no Phase 3 reconciliation logic added;
- no Phase 4 ExecutionCoordinator logic added;
- production authority unchanged.

Verification:
- old VenueOrderSide/VenueOrderType references: 0;
- domain -> ports dependency scan: clean;
- focused venue contracts: 16 passed;
- adjacent TradeIntent + Venue contracts: 29 passed;
- full suite: 173 passed;
- Python compileall: exit 0;
- flake8 changed files: exit 0;
- mypy apps/core --explicit-package-bases --ignore-missing-imports:
  Success: no issues found in 6 source files;
- canonical Python import verified as apps.core.domain.orders;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_CANONICAL_ORDER_TYPES_OWNERSHIP_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`

Primary next requirement:
- migrate the verified immutable ExecutionPlan / ExecutionLegPlan domain contract using canonical Core Domain OrderType without domain -> port dependency.
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
## 2026-09-05 — Phase 2 PositionGroup / PositionLeg V2 migration and hardening

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Legacy behavior preserved:
- PositionGroup remains canonical owner of logical SINGLE_LEG / PAIR / BASKET position lifecycle;
- PositionGroup preserves plan, user, strategy, strategy_version and trade-source lineage;
- PositionLeg remains canonical per-leg position projection inside PositionGroup;
- PositionLeg preserves account/instrument identity, side, target quantity, filled quantity, average entry/exit price and lifecycle state;
- initial legacy semantics remain PENDING with filled_quantity = 0;
- PositionLeg derived state remains based on validated execution evidence rather than independently invented execution semantics.

Approved V2 hardening:
- PositionGroupStatus: PENDING, OPENING, OPEN, CLOSING, CLOSED;
- PositionLegStatus: PENDING, OPEN, CLOSED;
- PositionLeg adds current_quantity as canonical current-exposure projection;
- canonical AccountId and InstrumentId replace duplicated raw venue identity fields in Core Domain;
- created/opened/closed/updated timestamps are timezone-aware and normalized to UTC;
- quantities and prices use finite Decimal contracts;
- lifecycle consistency is fail-closed;
- no fill interpretation, average-price calculation or lifecycle-transition engine is embedded in the immutable domain contracts.

Architecture:
- Core Domain does not import ports;
- no VenueAdapter dependency;
- no SQLAlchemy/FastAPI dependency;
- no ExecutionCoordinator dependency;
- no Reconciliation implementation;
- no ExecutionOrder/ExecutionFill implementation added in this slice;
- production authority unchanged.

Verification:
- focused position tests: 17 passed;
- adjacent TradeIntent + ExecutionPlan + Position tests: 61 passed;
- full suite: 221 passed;
- flake8: exit 0;
- mypy apps/core --explicit-package-bases --ignore-missing-imports: exit 0;
- compileall: exit 0;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_POSITION_GROUP_LEG_MIGRATION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 ExecutionOrder / ExecutionFill V2 migration and hardening

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Legacy behavior preserved:
- ExecutionOrder remains the canonical order lifecycle projection;
- ExecutionOrder preserves canonical order identity, execution-plan ownership, position-leg ownership, account/instrument identity, client/venue order identities, side/type, requested/filled quantities, average fill price, optional limit price, reduce_only, rejection reason and lifecycle timestamps;
- client_order_id remains the canonical order idempotency boundary;
- ExecutionFill remains immutable fill-level execution evidence;
- ExecutionFill preserves canonical fill_id, execution-order ownership, optional venue_fill_id, quantity, price, fee, fee currency, executed_at and created_at;
- ExecutionOrder filled quantities and average fill prices remain projections derived from persisted fill evidence;
- nullable venue_fill_id does not itself provide deduplication;
- deterministic canonical fill_id generation for fills without venue_fill_id remains owned by application/reconciliation logic and must be stable across retries/restarts.

Approved V2 hardening:
- ExecutionOrderStatus: PENDING, SUBMITTED, ACCEPTED, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, UNKNOWN;
- ExecutionOrderStatus remains distinct from venue-adapter observation state;
- canonical AccountId and InstrumentId are used in Core Domain;
- requested_quantity uses finite positive Decimal;
- filled_quantity uses finite non-negative Decimal and cannot exceed requested_quantity;
- positive filled_quantity requires average_fill_price;
- MARKET forbids limit_price and LIMIT requires positive limit_price;
- PARTIALLY_FILLED requires strict partial quantity;
- FILLED requires filled_quantity == requested_quantity;
- CANCELLED may preserve partial fill projection;
- UNKNOWN supports fail-closed restart/reconciliation recovery state;
- rejection_reason is reserved for REJECTED state;
- timestamps are timezone-aware, UTC-normalized and checked for chronological consistency;
- ExecutionFill quantity/price are positive finite Decimal;
- ExecutionFill fee is non-negative finite Decimal;
- positive fee requires fee_currency;
- ExecutionFill remains immutable;
- domain objects do not generate random or unstable idempotency identities.

Architecture:
- Core Domain does not import ports;
- no VenueAdapter dependency;
- no SQLAlchemy/FastAPI dependency;
- no repository implementation;
- no Reconciliation implementation;
- no ExecutionCoordinator implementation;
- no transaction ownership added;
- production authority unchanged.

Verification:
- focused ExecutionOrder/ExecutionFill tests: 20 passed;
- adjacent execution-plan/position/order/fill/venue tests: 84 passed;
- full suite: 241 passed;
- flake8: exit 0;
- mypy apps/core --explicit-package-bases --ignore-missing-imports: exit 0;
- compileall: exit 0;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_EXECUTION_ORDER_FILL_MIGRATION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Execution Ledger Domain migration and hardening

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Historical Ledger contract preserved:
- ExecutionLedgerEvent is the canonical immutable execution/position lifecycle evidence contract;
- ledger events are append-only historical evidence and remain separate from mutable materialized current state;
- canonical event_id is the deterministic immutable idempotency identity;
- duplicate ingestion of the same canonical immutable event may resolve to the same event;
- conflicting data under the same event_id fails closed;
- event_version is explicit and supports future payload evolution;
- every event has user ownership and execution-plan lineage;
- group, leg, order, fill, account and venue lineage may be attached where applicable;
- occurred_at represents fact occurrence time;
- recorded_at represents NEXUS persistence/recording time;
- correlation_id and causation_id remain explicit workflow/evidence lineage;
- payload contains structured event-specific immutable evidence;
- core identifiers are not hidden only inside payload;
- no venue-specific event types are canonical.

Canonical event families implemented:
- PLAN_CREATED;
- GROUP_CREATED;
- GROUP_STATE_CHANGED;
- LEG_CREATED;
- LEG_STATE_CHANGED;
- ORDER_CREATED;
- ORDER_SUBMITTED;
- ORDER_ACCEPTED;
- ORDER_PARTIALLY_FILLED;
- ORDER_FILLED;
- ORDER_REJECTED;
- ORDER_CANCELLED;
- FILL_RECORDED;
- RECOVERY_STARTED;
- RECOVERY_COMPLETED;
- RECONCILIATION_DISCREPANCY;
- RECONCILIATION_RESOLVED.

Approved V2 hardening:
- ExecutionLedgerEvent is frozen/immutable;
- event_id/source/required lineage text is non-empty and fail-closed;
- event_version and user ownership are positive integers;
- occurred_at and recorded_at are timezone-aware and normalized to UTC;
- recorded_at cannot precede occurred_at;
- payload must be a JSON-serializable object;
- NaN/Infinity and Python-specific unserializable payload values fail closed;
- payload is defensively copied and exposed as immutable Mapping;
- deterministic replay normalization collapses exact duplicate events;
- same event_id with conflicting immutable evidence fails closed;
- replay normalization uses deterministic occurred_at, recorded_at, event_id ordering;
- this replay helper is not a lifecycle/state reducer and does not infer execution transitions.

Local / venue / evidence separation:
- ExecutionOrder and Position state remain mutable materialized local projections;
- VenueOrderState remains venue observation contract;
- ExecutionLedgerEvent remains immutable historical evidence;
- Ledger Domain does not query venues;
- actual venue truth and discrepancy interpretation remain Phase 3 Reconciliation responsibilities.

Architecture:
- Core Domain does not import ports;
- no VenueAdapter dependency;
- no ExecutionCoordinator implementation;
- no Reconciliation engine implementation;
- no SQLAlchemy/FastAPI/AsyncSession dependency;
- no repository implementation;
- no commit/rollback ownership;
- production authority unchanged.

Verification:
- focused ledger tests: 13 passed;
- adjacent order/fill/position/ledger/venue tests: 66 passed;
- full suite: 254 passed;
- flake8: exit 0;
- mypy apps/core --explicit-package-bases --ignore-missing-imports: exit 0;
- compileall: exit 0;
- corrected architecture guards: clean;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_EXECUTION_LEDGER_DOMAIN_MIGRATION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 V2 Persistence Foundation

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Purpose:
- establish the infrastructure substrate required to migrate the historically verified durable Core V2 Ledger persistence without introducing persistence dependencies into Core Domain.

Implemented:
- explicit Python packaging/build configuration for the NEXUS V2 monorepo;
- declared SQLAlchemy 2.x dependency;
- declared Alembic dependency;
- declared asyncpg PostgreSQL driver dependency;
- declared aiosqlite test dependency;
- explicit setuptools package discovery for apps/packages/infra/adapters/workers;
- canonical infra.persistence.PersistenceBase;
- async SQLAlchemy engine factory;
- async_sessionmaker factory;
- async session scope helper;
- Alembic scaffold under infra/persistence/migrations;
- Alembic target_metadata = PersistenceBase.metadata;
- Alembic versions directory preserved in Git;
- generated *.egg-info artifacts ignored.

Database safety:
- alembic.ini contains no default database target;
- online Alembic requires explicit NEXUS_DATABASE_URL;
- missing NEXUS_DATABASE_URL fails closed with non-zero exit;
- no database credentials are stored in repository configuration;
- no migration revision exists yet;
- no database schema was applied;
- no production database was contacted.

Architecture:
- Core Domain remains free of SQLAlchemy/Alembic/persistence imports;
- persistence implementation is owned by infra/persistence;
- no Ledger ORM model added yet;
- no ExecutionRepository added yet;
- no Reconciliation implementation;
- no ExecutionCoordinator implementation;
- no venue calls;
- no runtime execution behavior changed;
- production authority unchanged.

Verification:
- persistence focused tests: 4 passed;
- adjacent persistence/ledger/order/venue suite: 53 passed;
- full suite before final structural .gitkeep: 258 passed;
- final full suite rerun performed before closure;
- compileall: exit 0;
- flake8: exit 0;
- mypy: exit 0;
- alembic heads: exit 0 with no revisions;
- online migration without NEXUS_DATABASE_URL: fail-closed verified;
- hard-coded credential/default target guards: clean;
- Core Domain persistence dependency guard: clean;
- git diff --check: clean.

Known metadata discrepancy:
- pyproject.toml still contains [tool.nexus] phase = 1 while current project work is Phase 2;
- this value was preserved intentionally and was not silently changed;
- its ownership/automation meaning requires a separate FACT check before modification.

Evidence tag:

`NEXUS_V2_PERSISTENCE_FOUNDATION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Core V2 Persistence Model

Status: DESIGN APPROVED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Decision:
- V2 persistence does not copy historical storage shape blindly;
- verified historical behavior is a minimum parity baseline, not a design ceiling;
- new persistence may contain richer first-class ownership, lineage, provenance, lifecycle and evidence fields when those improve correctness, replay, recovery, reconciliation readiness, auditability or analytics.

Canonical identity rule:
- Core business identities remain canonical;
- ExecutionPlan → plan_id;
- PositionGroup → group_id;
- PositionLeg → (group_id, leg_id);
- ExecutionOrder → order_id;
- ExecutionFill → fill_id;
- venue request idempotency → client_order_id;
- AccountId → (venue_id, account_value);
- persistence MAY use internal BIGINT surrogate keys only as infrastructure details;
- surrogate keys do not cross the Core boundary and do not define idempotency.

Historical schema correction:
- historical account_id → exchanges.id semantics are explicitly NOT adopted as canonical V2 account identity;
- legacy Integer PK/FK structure may be retained internally only where technically justified and must never replace canonical identifiers.

Approved durable model:
- execution_plans;
- execution_plan_legs;
- position_groups;
- position_legs;
- execution_orders;
- execution_fills;
- execution_ledger_events.

Rich-data rule:
- integrity-critical ownership, lineage, replay and query dimensions are typed first-class columns;
- event-specific/evolving evidence belongs in JSONB;
- critical identity/ownership must not exist only in JSONB.

Execution evidence:
- execution_plan_legs preserves original planned execution;
- execution_orders separates canonical local state from last-known venue observation;
- execution_fills are immutable evidence;
- execution_ledger_events are immutable evidence;
- Ledger corrections are new events, never update/delete.

Transaction boundary:
- append Ledger event + mutate materialized projection + flush occur in one caller-owned transaction;
- repositories do not commit;
- repositories do not rollback;
- repositories do not infer lifecycle;
- repositories do not access venues;
- repositories do not perform reconciliation.

Phase boundary:
- Phase 2 may persist canonical state, immutable events and last-known venue observations;
- Phase 2 does not implement discrepancy detection/correction, startup reconciliation or continuous reconciliation;
- those remain Phase 3 responsibilities;
- ExecutionCoordinator remains Phase 4.

Multi-user:
- user ownership must be preserved through durable execution lineage;
- cross-user lineage must fail closed;
- Workspace/Tenant persistence is not invented before its canonical roadmap contract exists.

Verification:
- document UTF-8 byte validation: passed;
- UTF-8 em dash/arrow semantic verification: passed;
- required contract guards: passed;
- out-of-phase implementation guard: passed;
- git diff --check: passed;
- document diff: 371 insertions / 0 deletions.

Implementation order:
1. harden Ledger AccountId/VenueId domain identity;
2. canonical ORM models;
3. additive initial migration;
4. PostgreSQL schema/SQL verification;
5. append/read repositories;
6. atomic Ledger application service;
7. deterministic replay verification;
8. remaining Phase 2 gate evidence.

Production authority:
- unchanged;
- AI promotion remains SHADOW-ONLY;
- Advisory remains OBSERVE_ONLY;
- Restricted Live remains DISABLED;
- Full Live remains DISABLED;
- AI direct exchange access remains BLOCKED.

Evidence tag:

`NEXUS_V2_CORE_PERSISTENCE_MODEL_DESIGN_APPROVED`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Ledger Canonical Identity Hardening

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Scope:
- harden ExecutionLedgerEvent account/venue identity to canonical shared contracts;
- no ORM;
- no migration;
- no repository;
- no reconciliation;
- no ExecutionCoordinator;
- no venue access.

Implemented:
- ExecutionLedgerEvent.account_id changed from int | None to AccountId | None;
- ExecutionLedgerEvent.venue_id changed from str | None to VenueId | None;
- raw int account identity rejected;
- raw string venue identity rejected;
- when both account_id and venue_id are present, venues must match;
- account_id may exist without redundant venue_id evidence;
- removed legacy account_id positive-int coercion;
- removed legacy venue_id generic text normalization;
- tests use canonical AccountId/VenueId fixtures.

Canonical semantics:
- AccountId remains (VenueId, positive account value);
- VenueId remains canonical typed venue identity;
- historical account_id integer semantics are not retained;
- Core Domain remains infrastructure-free.

Verification:
- focused Ledger tests: 18 passed;
- adjacent Ledger/Order/ExecutionPlan/Position tests: 86 passed;
- full suite: 263 passed;
- flake8: passed;
- mypy: passed;
- compileall: passed;
- legacy identity semantics guard: clean;
- Core Domain persistence dependency guard: clean;
- git diff --check: clean.

Production authority:
- unchanged;
- AI promotion remains SHADOW-ONLY;
- Advisory remains OBSERVE_ONLY;
- Restricted Live remains DISABLED;
- Full Live remains DISABLED;
- AI direct exchange access remains BLOCKED.

Evidence tag:

`NEXUS_V2_LEDGER_CANONICAL_IDENTITY_HARDENING_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Execution Plan ORM Slice

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Scope:
- canonical persistence ORM for execution_plans;
- canonical persistence ORM for execution_plan_legs;
- no Alembic revision yet;
- no repository;
- no reconciliation;
- no ExecutionCoordinator;
- no venue access.

Implemented:
- execution_plans registered on PersistenceBase metadata;
- execution_plan_legs registered on PersistenceBase metadata;
- persistence-internal BIGINT surrogate primary keys;
- canonical plan_id retained as unique business identity;
- execution_plan_legs FK targets execution_plans.plan_id;
- UNIQUE(plan_id, leg_id);
- UNIQUE(order_id);
- UNIQUE(client_order_id);
- canonical AccountId flattened to venue_id + account_value;
- InstrumentId flattened to venue/native_symbol/instrument_type/asset_class;
- Decimal quantity and limit_price use NUMERIC(38,18);
- created_at/recorded_at use timezone-aware SQLAlchemy DateTime;
- PostgreSQL metadata column compiles as JSONB;
- rich plan fields include recorded_at/schema_version/metadata;
- persistence source models are tracked despite generic models/ ignore;
- generated __pycache__/pyc artifacts remain ignored.

Architecture:
- Core Domain has no SQLAlchemy/Alembic/infra.persistence dependency;
- canonical business identities remain authoritative;
- database surrogate IDs remain persistence-only;
- no migration/schema applied yet.

Verification:
- focused ORM tests: 10 passed;
- adjacent persistence/execution/identity tests: 77 passed;
- full suite: 273 passed;
- flake8: passed;
- mypy: passed;
- compileall: passed;
- domain dependency guard: clean;
- migration guard: clean;
- generated-artifact Git visibility guard: clean;
- git diff --check: clean.

Production authority:
- unchanged;
- AI promotion remains SHADOW-ONLY;
- Advisory remains OBSERVE_ONLY;
- Restricted Live remains DISABLED;
- Full Live remains DISABLED;
- AI direct exchange access remains BLOCKED.

Evidence tag:

`NEXUS_V2_EXECUTION_PLAN_ORM_SLICE_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Persistence state_version design correction

Status: DESIGN CORRECTED / FACT VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Fact:
- state_version existed only in CORE_V2_PERSISTENCE_MODEL.md;
- no current Core Domain contract owns state_version;
- no repository/application runtime increments or compares state_version;
- no optimistic-concurrency contract currently exists;
- no replay implementation uses state_version;
- no historical implementation evidence establishes required semantics.

Decision:
- remove mandatory state_version from position_groups;
- remove mandatory state_version from position_legs;
- remove mandatory state_version from execution_orders;
- do not add a persistence field with undefined ownership merely to match an earlier design document.

Canonical model:
- immutable Ledger/fill evidence remains historical truth;
- PositionGroup / PositionLeg / ExecutionOrder remain materialized current-state projections;
- repository remains persistence-only / flush-only;
- application-owned transactions remain responsible for validated projection mutation plus immutable Ledger evidence.

Future concurrency:
- an explicit projection revision / optimistic concurrency mechanism may be introduced only when a real concurrency contract defines:
  - owner;
  - compare/increment semantics;
  - transaction boundary;
  - replay behavior;
  - failure handling;
  - tests.

Reason:
- unused version columns create false concurrency guarantees and schema complexity without providing correctness.

Evidence tag:

`NEXUS_V2_PERSISTENCE_STATE_VERSION_DESIGN_CORRECTION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 PositionGroup / PositionLeg Persistence ORM Slice

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Scope:
- canonical persistence ORM for position_groups;
- canonical persistence ORM for position_legs;
- persistence model registry update;
- execution metadata regression test corrected for extensible shared metadata;
- no Alembic revision;
- no repository;
- no application writer;
- no reconciliation;
- no ExecutionCoordinator;
- no venue access.

PositionGroup persistence:
- persistence-internal BIGINT surrogate primary key;
- canonical group_id unique business identity;
- canonical plan_id FK to execution_plans.plan_id;
- user ownership;
- shape / strategy / strategy_version / trade_source lineage;
- materialized lifecycle status;
- opened_at / closed_at / created_at / updated_at timezone-aware timestamps.

PositionLeg persistence:
- persistence-internal BIGINT surrogate primary key;
- canonical identity UNIQUE(group_id, leg_id);
- canonical group_id FK to position_groups.group_id;
- AccountId flattened to venue_id + account_value;
- InstrumentId flattened to instrument_venue_id + native_symbol + instrument_type + asset_class;
- side;
- target_quantity;
- filled_quantity;
- current_quantity;
- average_entry_price;
- average_exit_price;
- materialized lifecycle status;
- opened_at / closed_at / created_at / updated_at timezone-aware timestamps.

Database guards:
- account_value > 0;
- account venue equals instrument venue;
- target_quantity > 0;
- filled_quantity >= 0;
- current_quantity >= 0;
- average entry/exit prices nullable or positive;
- quantities/prices use NUMERIC(38,18).

Architecture:
- PositionGroup / PositionLeg remain materialized current-state projections;
- immutable Ledger / Fill evidence remains historical truth;
- no unowned state_version field;
- Core Domain remains persistence-free;
- canonical business IDs remain authoritative;
- surrogate database IDs remain infrastructure-only.

Test correction:
- previous execution persistence test incorrectly required PersistenceBase metadata to contain exactly two tables;
- it now verifies execution tables are present as a subset of shared extensible metadata;
- position persistence tests verify the full currently expected metadata set;
- no production semantics were weakened.

Verification:
- execution persistence focused: 10 passed;
- position persistence focused: 14 passed;
- adjacent persistence/domain/identity suite: 108 passed;
- full suite: 287 passed;
- flake8: passed;
- mypy: passed;
- compileall: passed;
- metadata proof: passed;
- Core dependency guard: clean;
- state_version guard: clean;
- migration guard: clean;
- generated artifact guard: clean;
- git diff --check: clean.

Production authority:
- unchanged;
- AI promotion remains SHADOW-ONLY;
- Advisory remains OBSERVE_ONLY;
- Restricted Live remains DISABLED;
- Full Live remains DISABLED;
- AI direct exchange access remains BLOCKED.

Evidence tag:

`NEXUS_V2_POSITION_PERSISTENCE_ORM_SLICE_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 Hosted CI project dependency bootstrap repair

Status: FIX VERIFIED LOCALLY / HOSTED CI PENDING

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Fact:
- hosted CI workflow created a clean Python 3.13 environment;
- repository baseline and dev baseline passed;
- workflow installed only pytest before running the full test suite;
- project dependencies from pyproject.toml were not installed;
- clean CI reproduction showed sqlalchemy, alembic and asyncpg unavailable;
- pytest collection failed with ModuleNotFoundError for sqlalchemy.

Root cause:
- .github/workflows/ci.yml did not install the project or its declared dependencies before running tests.

Fix:
- replace pytest-only bootstrap with:
  python -m pip install --disable-pip-version-check ".[test]" pytest

Dependency ownership:
- pyproject.toml remains the canonical project dependency source;
- CI does not duplicate SQLAlchemy/Alembic/asyncpg version constraints;
- test extra supplies aiosqlite;
- pytest remains explicitly installed by CI in this repair scope.

Clean-environment verification:
- Python 3.13.14;
- repository baseline: passed;
- local dev baseline: passed;
- SQLAlchemy 2.0.52 installed;
- alembic 1.19.2 installed;
- asyncpg 0.31.0 installed;
- aiosqlite 0.22.1 installed;
- pytest 9.1.1 installed;
- full suite: 287 passed;
- git diff --check: clean.

Scope:
- CI dependency bootstrap only;
- no domain behavior change;
- no persistence schema change;
- no migration;
- no runtime execution authority change.

Hosted CI:
- not yet declared verified;
- GitHub Actions result must be checked after push.

Evidence tag:

`NEXUS_V2_CI_PROJECT_DEPENDENCY_BOOTSTRAP_FIX_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 ExecutionOrder → PositionLeg canonical ownership correction

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Fact:
- canonical PositionLeg identity is `(group_id, leg_id)`;
- ExecutionOrder previously carried `plan_id + leg_id` but not `group_id`;
- PositionGroup.plan_id is not unique;
- no one-PositionGroup-per-ExecutionPlan invariant exists;
- therefore `plan_id + leg_id` alone could not prove canonical PositionLeg ownership.

Historical verified behavior:
- legacy/current historical Core maintained explicit ExecutionOrder → PositionLeg ownership through persistence `position_leg_id`;
- fill-ingestion lineage checks required owning PositionLeg existence;
- cross-plan / cross-leg ownership conflicts failed closed.

Correction:
- ExecutionOrder now carries required `group_id`;
- `group_id` is validated as non-empty first-class ownership lineage;
- canonical ExecutionOrder identity remains `order_id`;
- canonical PositionLeg identity remains `(group_id, leg_id)`;
- persistence design now requires:
  - FK `plan_id → execution_plans(plan_id)`;
  - composite FK `(group_id, leg_id) → position_legs(group_id, leg_id)`;
- no PositionGroup.plan_id uniqueness was invented;
- no PositionLeg identity redesign was introduced.

Verification:
- focused ExecutionOrder/ExecutionFill tests: 22 passed;
- adjacent Core tests: 120 passed;
- full regression: 289 passed;
- flake8: passed;
- mypy: passed;
- compileall: passed;
- Core Domain persistence boundary: clean;
- no ExecutionOrder/ExecutionFill ORM introduced in this correction;
- no migration introduced;
- git diff --check: clean.

Scope:
- domain ownership lineage correction;
- persistence design correction;
- focused tests only;
- no reconciliation;
- no ExecutionCoordinator;
- no venue write access;
- no production authority change.

Evidence tag:

`NEXUS_V2_EXECUTION_ORDER_POSITION_LEG_OWNERSHIP_CORRECTION_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
## 2026-09-05 — Phase 2 ExecutionOrder / ExecutionFill ORM persistence slice

Status: DONE / TEST VERIFIED

Phase:
- Phase 2 — Import and harden existing Core V2 foundation.

Implemented:
- ExecutionOrderModel;
- ExecutionFillModel;
- persistence registry updated to expose/register all canonical execution/position models.

ExecutionOrder persistence:
- canonical `order_id` retained;
- `plan_id → execution_plans.plan_id`;
- canonical PositionLeg ownership through composite `(group_id, leg_id)`;
- unique `order_id`;
- unique `client_order_id`;
- canonical AccountId flattened to `venue_id + account_value`;
- InstrumentId flattened to venue/native-symbol/type/asset-class fields;
- local state stored as `local_status`;
- last-known venue observation stored separately as:
  - `last_venue_status`;
  - `last_venue_observed_at`;
  - `venue_observation_source`;
- requested/fill quantities and prices use `NUMERIC(38,18)`;
- no `state_version`.

ExecutionFill persistence:
- canonical `fill_id` independently unique;
- `order_id → execution_orders.order_id`;
- canonical user/venue/account ownership persisted;
- venue fill dedup scoped by `(venue_id, account_value, venue_fill_id)`;
- nullable `venue_fill_id` is not globally unique;
- quantity/price/fee use `NUMERIC(38,18)`;
- rich evidence fields include:
  - `executed_at`;
  - `received_at`;
  - `created_at`;
  - `source`;
  - `raw_evidence_hash`.

Database guards:
- positive user/account ownership;
- matching account/instrument venue;
- positive requested quantity;
- non-negative fill quantity;
- filled quantity cannot exceed requested;
- positive prices where present;
- positive fill quantity and price;
- non-negative fee;
- positive fee requires fee currency.

Architecture:
- Core Domain remains independent of SQLAlchemy/Alembic/persistence;
- no migration created;
- no repository created;
- no reconciliation logic;
- no ExecutionCoordinator logic;
- no venue access;
- no production authority change.

Verification:
- focused persistence: 44 passed;
- adjacent Core + persistence: 132 passed;
- full regression: 305 passed;
- flake8: passed;
- mypy: passed;
- compileall: passed;
- PostgreSQL DDL compilation tests: passed;
- persistence metadata contains exactly:
  - execution_plans;
  - execution_plan_legs;
  - position_groups;
  - position_legs;
  - execution_orders;
  - execution_fills;
- git diff --check: clean.

Evidence tag:

`NEXUS_V2_EXECUTION_ORDER_FILL_ORM_SLICE_OK`

Aggregate Phase 2 gate remains OPEN:

`NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK`
