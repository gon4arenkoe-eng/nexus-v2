"""Tests for atomic immutable Ledger persistence boundary."""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.application import (
    ExecutionLedgerPersistenceService,
    LedgerEventConflictError,
    LedgerPersistDisposition,
)
from infra.persistence.models import ExecutionLedgerEventModel


class FakeLedgerRepository:
    def __init__(self) -> None:
        self.events: dict[str, ExecutionLedgerEventModel] = {}
        self.add_calls = 0
        self.get_calls = 0

    async def add(
        self,
        event: ExecutionLedgerEventModel,
    ) -> ExecutionLedgerEventModel:
        self.add_calls += 1
        self.events[event.event_id] = event
        return event

    async def get_by_event_id(
        self,
        *,
        user_id: int,
        event_id: str,
    ) -> ExecutionLedgerEventModel | None:
        self.get_calls += 1

        event = self.events.get(event_id)

        if event is None or event.user_id != user_id:
            return None

        return event


def _event(
    *,
    event_id: str = "evt-1",
    source: str = "core-test",
    payload: dict[str, object] | None = None,
) -> ExecutionLedgerEventModel:
    occurred_at = datetime(
        2026,
        9,
        10,
        18,
        0,
        tzinfo=UTC,
    )
    recorded_at = datetime(
        2026,
        9,
        10,
        18,
        0,
        1,
        tzinfo=UTC,
    )

    return ExecutionLedgerEventModel(
        event_id=event_id,
        event_type="ORDER_CREATED",
        event_version=1,
        user_id=11,
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        order_id="order-1",
        fill_id=None,
        venue_id="BINANCE",
        account_value=7,
        instrument_venue_id="BINANCE",
        native_symbol="BTCUSDT",
        instrument_type="PERPETUAL",
        asset_class="CRYPTO",
        source=source,
        correlation_id="corr-1",
        causation_id="cause-1",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        sequence_no=3,
        evidence_source="APPLICATION",
        evidence_quality="CANONICAL",
        schema_version=1,
        payload=payload or {"status": "PENDING"},
    )


def test_new_event_mutates_projection_then_appends() -> None:
    async def scenario() -> None:
        session = cast(AsyncSession, object())
        repository = FakeLedgerRepository()

        service = ExecutionLedgerPersistenceService(
            session,
            repository=repository,
        )

        mutation_sessions: list[AsyncSession] = []

        async def mutate(received: AsyncSession) -> None:
            mutation_sessions.append(received)

        event = _event()

        result = await service.persist(
            event=event,
            mutate_projection=mutate,
        )

        assert result.disposition is LedgerPersistDisposition.APPENDED
        assert result.event is event
        assert mutation_sessions == [session]
        assert repository.add_calls == 1
        assert repository.events[event.event_id] is event

    asyncio.run(scenario())


def test_exact_duplicate_is_idempotent_and_skips_projection() -> None:
    async def scenario() -> None:
        session = cast(AsyncSession, object())
        repository = FakeLedgerRepository()

        existing = _event()
        repository.events[existing.event_id] = existing

        service = ExecutionLedgerPersistenceService(
            session,
            repository=repository,
        )

        mutation_count = 0

        async def mutate(_: AsyncSession) -> None:
            nonlocal mutation_count
            mutation_count += 1

        duplicate = _event()

        result = await service.persist(
            event=duplicate,
            mutate_projection=mutate,
        )

        assert result.disposition is LedgerPersistDisposition.DUPLICATE
        assert result.event is existing
        assert mutation_count == 0
        assert repository.add_calls == 0

    asyncio.run(scenario())


def test_payload_mapping_order_does_not_create_conflict() -> None:
    async def scenario() -> None:
        session = cast(AsyncSession, object())
        repository = FakeLedgerRepository()

        existing = _event(
            payload={
                "status": "PENDING",
                "attempt": 1,
            }
        )
        repository.events[existing.event_id] = existing

        service = ExecutionLedgerPersistenceService(
            session,
            repository=repository,
        )

        async def mutate(_: AsyncSession) -> None:
            raise AssertionError(
                "duplicate must not mutate projection"
            )

        duplicate = _event(
            payload={
                "attempt": 1,
                "status": "PENDING",
            }
        )

        result = await service.persist(
            event=duplicate,
            mutate_projection=mutate,
        )

        assert result.disposition is LedgerPersistDisposition.DUPLICATE

    asyncio.run(scenario())


def test_conflicting_same_event_id_fails_closed() -> None:
    async def scenario() -> None:
        session = cast(AsyncSession, object())
        repository = FakeLedgerRepository()

        existing = _event()
        repository.events[existing.event_id] = existing

        service = ExecutionLedgerPersistenceService(
            session,
            repository=repository,
        )

        mutation_count = 0

        async def mutate(_: AsyncSession) -> None:
            nonlocal mutation_count
            mutation_count += 1

        conflicting = _event(source="different-source")

        with pytest.raises(LedgerEventConflictError):
            await service.persist(
                event=conflicting,
                mutate_projection=mutate,
            )

        assert mutation_count == 0
        assert repository.add_calls == 0

    asyncio.run(scenario())


def test_service_does_not_own_transaction_commit_or_rollback() -> None:
    source = inspect.getsource(ExecutionLedgerPersistenceService)

    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_service_has_no_execution_or_reconciliation_dependency() -> None:
    source = inspect.getsource(ExecutionLedgerPersistenceService)

    forbidden = (
        "VenueAdapter",
        "ExecutionCoordinator",
        "place_order",
        "submit_order",
        "reconcile(",
    )

    assert not any(value in source for value in forbidden)
