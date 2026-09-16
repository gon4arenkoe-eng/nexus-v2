# Phase 13 Local Reconciliation Snapshot Provider v1

Status: CANDIDATE / NOT AUDIT-CLOSED

## Purpose

Provide the missing persistence-backed local truth read surface required by
canonical reconciliation.

Scope:

`(user_id, AccountId, InstrumentId) -> ExecutionOrder / ExecutionFill / PositionLeg`

This capability is venue-agnostic. It is not a Bybit-specific store.

## Architecture

Dependency direction remains:

`Core port <- infrastructure persistence implementation`

Core does not import SQLAlchemy.

The provider is read-only and has:

- no venue dependency;
- no exchange credentials;
- no order submit/cancel authority;
- no persistence mutation methods;
- no destructive reconciliation behavior.

## Ownership / isolation

Orders are filtered directly by:

- user_id;
- venue/account;
- instrument identity.

Fills are filtered by their own user/account/venue ownership and joined to the
owning ExecutionOrder for instrument identity.

PositionLeg ownership is resolved through PositionGroup.user_id because
PositionLegModel intentionally has no direct user_id column.

## Determinism

Queries use explicit stable ordering before domain hydration.

## Hydration

Persisted materialized state is restored into canonical domain objects.
Canonical constructors re-validate domain invariants.

Timezone-naive persistence values are restored as UTC, matching existing
repository conventions.

## Not included

- venue observations;
- reconciliation execution;
- discrepancy persistence;
- startup activation;
- continuous reconciliation;
- Bybit runtime wiring;
- writes or live authority.

After this provider is verified, the next Phase 13 slice may compose it with a
read-only VenueAdapter and the existing ReconciliationPassOrchestrator.
