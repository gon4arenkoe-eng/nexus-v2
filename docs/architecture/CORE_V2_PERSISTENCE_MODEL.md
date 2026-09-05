# NEXUS V2 Core Persistence Model

Status: DESIGN APPROVED FOR PHASE 2 IMPLEMENTATION
Phase: 2 — Import and harden existing Core V2 foundation
Gate: NEXUS_V2_CORE_FOUNDATION_MIGRATED_OK

## 1. Purpose

Define the canonical durable persistence model for:

TradeIntent
→ ExecutionPlan
→ ExecutionPlanLeg
→ PositionGroup
→ PositionLeg
→ ExecutionOrder
→ ExecutionFill
→ ExecutionLedgerEvent

The model preserves verified historical behavior while removing legacy
storage-identity ambiguity and extending evidence, lineage, replay,
recovery, multi-user ownership and analytical quality.

This document defines storage architecture only.

It does not implement:
- Reconciliation Engine;
- Execution Coordinator;
- venue write access;
- runtime execution;
- destructive state correction;
- production authority changes.

## 2. Identity Rule

Canonical Core identities are business identities.

Persistence MAY use internal BIGINT surrogate primary keys for database
performance and FK efficiency.

Surrogate database IDs:
- are persistence implementation details;
- never become canonical Core identities;
- never cross the Core domain boundary;
- never replace canonical IDs;
- never define idempotency.

Canonical identities:

- ExecutionPlan: plan_id
- PositionGroup: group_id
- PositionLeg: (group_id, leg_id)
- ExecutionOrder: order_id
- ExecutionFill: fill_id
- venue request idempotency: client_order_id
- AccountId: (venue_id, account_value)

Historical account_id → exchanges.id semantics are NOT canonical V2
identity semantics and must not be copied.

## 3. Rich-data rule

Important ownership, lineage, integrity, replay and query fields are
first-class typed columns.

Event-specific or evolving evidence belongs in JSONB payload.

Do not put critical identity/ownership fields only into JSONB.

Do not duplicate mutable state without an explicit purpose.

## 4. execution_plans

Required columns:

- id BIGINT primary key, persistence-internal;
- plan_id VARCHAR unique not null;
- intent_id VARCHAR not null;
- user_id BIGINT not null;
- shape VARCHAR not null;
- strategy VARCHAR not null;
- strategy_version VARCHAR nullable;
- source VARCHAR not null;
- created_at TIMESTAMPTZ not null;
- recorded_at TIMESTAMPTZ not null;
- schema_version INTEGER not null;
- metadata JSONB not null.

plan_id is the canonical identity.

## 5. execution_plan_legs

This table persists what was originally planned and prevents historical
execution intent from having to be reconstructed from mutable order or
position projections.

Required columns:

- id BIGINT primary key;
- plan_id VARCHAR not null;
- leg_id VARCHAR not null;
- order_id VARCHAR not null;
- client_order_id VARCHAR not null;
- venue_id VARCHAR not null;
- account_value BIGINT not null;
- instrument_venue_id VARCHAR not null;
- native_symbol VARCHAR not null;
- instrument_type VARCHAR not null;
- asset_class VARCHAR not null;
- side VARCHAR not null;
- quantity NUMERIC not null;
- order_type VARCHAR not null;
- limit_price NUMERIC nullable;
- reduce_only BOOLEAN not null;
- created_at TIMESTAMPTZ not null.

Required uniqueness:

- UNIQUE(plan_id, leg_id);
- UNIQUE(order_id);
- UNIQUE(client_order_id).

## 6. position_groups

Required columns:

- id BIGINT primary key;
- group_id VARCHAR unique not null;
- plan_id VARCHAR not null;
- user_id BIGINT not null;
- shape VARCHAR not null;
- strategy VARCHAR not null;
- strategy_version VARCHAR nullable;
- trade_source VARCHAR not null;
- status VARCHAR not null;
- opened_at TIMESTAMPTZ nullable;
- closed_at TIMESTAMPTZ nullable;
- created_at TIMESTAMPTZ not null;
- updated_at TIMESTAMPTZ not null.

group_id is the canonical pair/basket ownership identity.

## 7. position_legs

Required columns:

- id BIGINT primary key;
- group_id VARCHAR not null;
- leg_id VARCHAR not null;
- venue_id VARCHAR not null;
- account_value BIGINT not null;
- instrument_venue_id VARCHAR not null;
- native_symbol VARCHAR not null;
- instrument_type VARCHAR not null;
- asset_class VARCHAR not null;
- side VARCHAR not null;
- target_quantity NUMERIC not null;
- filled_quantity NUMERIC not null;
- current_quantity NUMERIC not null;
- average_entry_price NUMERIC nullable;
- average_exit_price NUMERIC nullable;
- status VARCHAR not null;
- opened_at TIMESTAMPTZ nullable;
- closed_at TIMESTAMPTZ nullable;
- created_at TIMESTAMPTZ not null;
- updated_at TIMESTAMPTZ not null.

Required uniqueness:

- UNIQUE(group_id, leg_id).

## 8. execution_orders

Required columns:

- id BIGINT primary key;
- order_id VARCHAR unique not null;
- plan_id VARCHAR not null;
- group_id VARCHAR not null;
- leg_id VARCHAR not null;
- user_id BIGINT not null;
- venue_id VARCHAR not null;
- account_value BIGINT not null;
- instrument_venue_id VARCHAR not null;
- native_symbol VARCHAR not null;
- instrument_type VARCHAR not null;
- asset_class VARCHAR not null;
- client_order_id VARCHAR unique not null;
- venue_order_id VARCHAR nullable;
- side VARCHAR not null;
- order_type VARCHAR not null;
- reduce_only BOOLEAN not null;
- requested_quantity NUMERIC not null;
- filled_quantity NUMERIC not null;
- average_fill_price NUMERIC nullable;
- limit_price NUMERIC nullable;
- local_status VARCHAR not null;
- last_venue_status VARCHAR nullable;
- last_venue_observed_at TIMESTAMPTZ nullable;
- venue_observation_source VARCHAR nullable;
- rejection_reason TEXT nullable;
- submitted_at TIMESTAMPTZ nullable;
- accepted_at TIMESTAMPTZ nullable;
- filled_at TIMESTAMPTZ nullable;
- cancelled_at TIMESTAMPTZ nullable;
- created_at TIMESTAMPTZ not null;
- updated_at TIMESTAMPTZ not null.

Required ownership constraints:

- FOREIGN KEY (plan_id) REFERENCES execution_plans(plan_id) ON DELETE RESTRICT;
- FOREIGN KEY (group_id, leg_id) REFERENCES position_legs(group_id, leg_id) ON DELETE RESTRICT.

`group_id` is first-class PositionGroup / PositionLeg ownership lineage.
It does not become part of canonical ExecutionOrder identity; `order_id` remains
the canonical order identity.

Local state and last-known venue observation are explicitly distinct.

These venue-observation fields do NOT implement Phase 3 reconciliation.

## 9. execution_fills

ExecutionFill persistence is immutable evidence.

Required columns:

- id BIGINT primary key;
- fill_id VARCHAR unique not null;
- order_id VARCHAR not null;
- user_id BIGINT not null;
- venue_id VARCHAR not null;
- account_value BIGINT not null;
- venue_fill_id VARCHAR nullable;
- quantity NUMERIC not null;
- price NUMERIC not null;
- fee NUMERIC not null;
- fee_currency VARCHAR nullable;
- executed_at TIMESTAMPTZ not null;
- received_at TIMESTAMPTZ not null;
- created_at TIMESTAMPTZ not null;
- source VARCHAR not null;
- raw_evidence_hash VARCHAR nullable.

venue_fill_id deduplication must be scoped by canonical venue/account
ownership when venue_fill_id exists.

Canonical fill_id remains independently unique.

## 10. execution_ledger_events

Ledger events are immutable historical evidence.

Required columns:

- id BIGINT primary key;
- event_id VARCHAR unique not null;
- event_type VARCHAR not null;
- event_version INTEGER not null;
- user_id BIGINT not null;
- plan_id VARCHAR not null;
- group_id VARCHAR nullable;
- leg_id VARCHAR nullable;
- order_id VARCHAR nullable;
- fill_id VARCHAR nullable;
- venue_id VARCHAR nullable;
- account_value BIGINT nullable;
- instrument_venue_id VARCHAR nullable;
- native_symbol VARCHAR nullable;
- instrument_type VARCHAR nullable;
- asset_class VARCHAR nullable;
- source VARCHAR not null;
- correlation_id VARCHAR nullable;
- causation_id VARCHAR nullable;
- occurred_at TIMESTAMPTZ not null;
- recorded_at TIMESTAMPTZ not null;
- sequence_no BIGINT nullable;
- evidence_source VARCHAR nullable;
- evidence_quality VARCHAR nullable;
- schema_version INTEGER not null;
- payload JSONB not null.

event_id is the canonical deterministic idempotency identity.

Corrections are represented by new events.

No update/delete Ledger API is allowed.

## 11. Transaction rule

Application transaction ownership remains outside repositories.

Required atomic pattern:

append immutable Ledger event
+ mutate corresponding materialized projection
+ flush
→ one caller-owned transaction.

Repositories:
- add/read/query/flush;
- no commit;
- no rollback;
- no lifecycle inference;
- no venue access;
- no reconciliation.

## 12. Replay and recovery

Durability must support:

- deterministic event ordering;
- exact duplicate event collapse;
- conflicting same-event-id evidence fail closed;
- replay of local state;
- restart recovery;
- comparison of materialized state with immutable history.

Runtime recovery policy belongs to later application/Execution Coordinator
work where specified by the Master Plan.

## 13. Phase boundary

Phase 2 may persist:
- canonical current state;
- immutable events;
- last-known venue observations.

Phase 2 must NOT implement:
- reconciliation discrepancy detection;
- reconciliation correction policy;
- startup venue reconciliation workflow;
- continuous reconciliation.

Those belong to Phase 3.

The Ledger event vocabulary may already contain reconciliation event types
for compatibility and future evidence.

## 14. Multi-user boundary

Every execution root and durable evidence path must preserve user
ownership.

Cross-user lineage is invalid and must fail closed at application and
repository boundaries.

Workspace/Tenant storage is intentionally not invented here before its
canonical shared contract is established by the approved roadmap.

Future workspace ownership must be additive without changing canonical
execution identities.

## 15. Production safety

This persistence design:
- does not submit orders;
- does not invoke VenueAdapter;
- does not enable reconciliation;
- does not enable ExecutionCoordinator;
- does not enable Restricted Live;
- does not enable Full Live;
- does not grant AI exchange access.

## 16. Implementation order

1. harden Ledger AccountId/VenueId domain identity;
2. implement canonical ORM models;
3. create additive first migration;
4. verify PostgreSQL SQL/schema;
5. implement append/read repositories;
6. implement atomic Ledger application service;
7. deterministic replay verification;
8. close remaining Phase 2 gate evidence.

Design evidence tag:

NEXUS_V2_CORE_PERSISTENCE_MODEL_DESIGN_APPROVED
