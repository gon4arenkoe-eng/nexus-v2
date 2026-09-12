"""Deterministic persisted execution Ledger replay tests."""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime, timedelta

import pytest

from infra.persistence.application import (
    ExecutionLedgerReplayService,
    LedgerReplayConflictError,
    project_ledger_events,
)
from infra.persistence.models import ExecutionLedgerEventModel


class FakeReplayRepository:
    def __init__(
        self,
        events: tuple[ExecutionLedgerEventModel, ...],
    ) -> None:
        self.events = events
        self.calls: list[tuple[int, str]] = []

    async def list_for_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        self.calls.append((user_id, plan_id))

        return tuple(
            event
            for event in self.events
            if event.user_id == user_id
            and event.plan_id == plan_id
        )


def _event(
    *,
    event_id: str,
    event_type: str,
    second: int,
    payload: dict[str, object] | None = None,
    surrogate_id: int | None = None,
) -> ExecutionLedgerEventModel:
    base = datetime(
        2026,
        9,
        10,
        18,
        0,
        tzinfo=UTC,
    )

    event = ExecutionLedgerEventModel(
        event_id=event_id,
        event_type=event_type,
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
        source="replay-test",
        correlation_id="corr-1",
        causation_id="cause-1",
        occurred_at=base + timedelta(seconds=second),
        recorded_at=base + timedelta(seconds=second, microseconds=1),
        sequence_no=second,
        evidence_source="APPLICATION",
        evidence_quality="CANONICAL",
        schema_version=1,
        payload=payload or {"status": event_type},
    )

    if surrogate_id is not None:
        event.id = surrogate_id

    return event


def test_replay_is_independent_of_input_order() -> None:
    events = (
        _event(
            event_id="evt-1",
            event_type="ORDER_CREATED",
            second=1,
        ),
        _event(
            event_id="evt-2",
            event_type="ORDER_ACCEPTED",
            second=2,
        ),
        _event(
            event_id="evt-3",
            event_type="ORDER_FILLED",
            second=3,
        ),
    )

    forward = project_ledger_events(events)
    shuffled = project_ledger_events(
        (events[2], events[0], events[1])
    )

    assert forward == shuffled
    assert forward.ordered_event_ids == (
        "evt-1",
        "evt-2",
        "evt-3",
    )


def test_surrogate_database_id_does_not_change_replay() -> None:
    left = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
        surrogate_id=10,
    )
    right = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
        surrogate_id=999,
    )

    assert project_ledger_events((left,)) == project_ledger_events(
        (right,)
    )


def test_exact_duplicate_collapses_idempotently() -> None:
    first = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
    )
    duplicate = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
    )

    projection = project_ledger_events(
        (first, duplicate)
    )

    assert projection.event_count == 1
    assert projection.ordered_event_ids == ("evt-1",)


def test_conflicting_duplicate_fails_closed() -> None:
    first = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
    )
    conflicting = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
        payload={"status": "CONFLICT"},
    )

    with pytest.raises(LedgerReplayConflictError):
        project_ledger_events(
            (first, conflicting)
        )


def test_payload_key_order_does_not_change_digest() -> None:
    left = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
        payload={
            "status": "PENDING",
            "attempt": 1,
        },
    )
    right = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
        payload={
            "attempt": 1,
            "status": "PENDING",
        },
    )

    assert (
        project_ledger_events((left,)).digest
        == project_ledger_events((right,)).digest
    )


def test_replay_rebuilds_latest_lineage_heads() -> None:
    projection = project_ledger_events(
        (
            _event(
                event_id="evt-3",
                event_type="ORDER_FILLED",
                second=3,
            ),
            _event(
                event_id="evt-1",
                event_type="ORDER_CREATED",
                second=1,
            ),
            _event(
                event_id="evt-2",
                event_type="ORDER_ACCEPTED",
                second=2,
            ),
        )
    )

    expected = (
        "order-1",
        "ORDER_FILLED",
        "evt-3",
    )

    assert projection.order_heads == (expected,)
    assert projection.plan_heads == (
        (
            "plan-1",
            "ORDER_FILLED",
            "evt-3",
        ),
    )
    assert projection.group_heads == (
        (
            "group-1",
            "ORDER_FILLED",
            "evt-3",
        ),
    )


def test_replay_service_preserves_user_plan_scope() -> None:
    async def scenario() -> None:
        repository = FakeReplayRepository(
            (
                _event(
                    event_id="evt-1",
                    event_type="ORDER_CREATED",
                    second=1,
                ),
            )
        )

        service = ExecutionLedgerReplayService(
            repository
        )

        projection = await service.replay_plan(
            user_id=11,
            plan_id="plan-1",
        )

        assert repository.calls == [(11, "plan-1")]
        assert projection.event_count == 1

    asyncio.run(scenario())


def test_naive_timestamp_fails_closed() -> None:
    event = _event(
        event_id="evt-1",
        event_type="ORDER_CREATED",
        second=1,
    )
    event.occurred_at = event.occurred_at.replace(
        tzinfo=None
    )

    with pytest.raises(ValueError):
        project_ledger_events((event,))


def test_replay_has_no_execution_or_transaction_authority() -> None:
    source = inspect.getsource(
        ExecutionLedgerReplayService
    )

    forbidden = (
        ".commit(",
        ".rollback(",
        "VenueAdapter",
        "ExecutionCoordinator",
        "place_order",
        "submit_order",
        "reconcile(",
    )

    assert not any(
        value in source
        for value in forbidden
    )
