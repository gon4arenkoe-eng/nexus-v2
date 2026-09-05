from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from apps.core.domain.ledger import (
    ExecutionLedgerEvent,
    ExecutionLedgerEventType,
    ledger_events_equivalent,
    sort_ledger_events_for_replay,
)


T1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 5, 12, 1, tzinfo=timezone.utc)
T3 = datetime(2026, 9, 5, 12, 2, tzinfo=timezone.utc)


def _event(
    *,
    event_id: str = "event-1",
    event_type: ExecutionLedgerEventType = (
        ExecutionLedgerEventType.ORDER_CREATED
    ),
    occurred_at: datetime = T1,
    recorded_at: datetime = T2,
    payload: dict[str, object] | None = None,
) -> ExecutionLedgerEvent:
    return ExecutionLedgerEvent(
        event_id=event_id,
        event_type=event_type,
        event_version=1,
        user_id=1,
        execution_plan_id="plan-1",
        position_group_id="group-1",
        position_leg_id="leg-1",
        execution_order_id="order-1",
        execution_fill_id=None,
        account_id=1,
        venue_id="BINGX",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        source="execution",
        correlation_id="corr-1",
        causation_id=None,
        payload=payload or {},
    )


def test_ledger_event_is_immutable() -> None:
    event = _event()

    with pytest.raises(FrozenInstanceError):
        event.event_id = "changed"  # type: ignore[misc]


def test_payload_is_copied_and_immutable() -> None:
    payload = {
        "previous_status": "PENDING",
        "new_status": "SUBMITTED",
    }

    event = _event(payload=payload)

    payload["new_status"] = "FILLED"

    assert event.payload["new_status"] == "SUBMITTED"

    with pytest.raises(TypeError):
        event.payload["x"] = "y"  # type: ignore[index]


@pytest.mark.parametrize(
    "payload",
    [
        {"bad": object()},
        {"bad": float("nan")},
        {"bad": float("inf")},
    ],
)
def test_payload_must_be_json_serializable(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        _event(payload=payload)


def test_event_times_normalize_to_utc() -> None:
    plus_three = timezone(timedelta(hours=3))

    event = _event(
        occurred_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            tzinfo=plus_three,
        ),
        recorded_at=datetime(
            2026,
            9,
            5,
            15,
            1,
            tzinfo=plus_three,
        ),
    )

    assert event.occurred_at == T1
    assert event.recorded_at == T2


def test_recorded_at_cannot_precede_occurred_at() -> None:
    with pytest.raises(ValueError):
        _event(
            occurred_at=T2,
            recorded_at=T1,
        )


def test_event_version_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ExecutionLedgerEvent(
            event_id="event-1",
            event_type=ExecutionLedgerEventType.PLAN_CREATED,
            event_version=0,
            user_id=1,
            execution_plan_id="plan-1",
            position_group_id=None,
            position_leg_id=None,
            execution_order_id=None,
            execution_fill_id=None,
            account_id=None,
            venue_id=None,
            occurred_at=T1,
            recorded_at=T1,
            source="execution",
            correlation_id=None,
            causation_id=None,
            payload={},
        )


def test_same_event_id_and_same_event_are_equivalent() -> None:
    left = _event()
    right = _event()

    assert ledger_events_equivalent(left, right)


def test_same_event_id_with_different_payload_conflicts() -> None:
    left = _event(payload={"state": "PENDING"})
    right = _event(payload={"state": "FILLED"})

    assert not ledger_events_equivalent(left, right)

    with pytest.raises(ValueError):
        sort_ledger_events_for_replay(
            [left, right]
        )


def test_exact_duplicate_is_idempotently_collapsed() -> None:
    event = _event()

    replay = sort_ledger_events_for_replay(
        [event, event]
    )

    assert replay == (event,)


def test_replay_order_is_deterministic() -> None:
    late = _event(
        event_id="event-3",
        occurred_at=T3,
        recorded_at=T3,
    )
    first = _event(
        event_id="event-1",
        occurred_at=T1,
        recorded_at=T2,
    )
    second = _event(
        event_id="event-2",
        occurred_at=T1,
        recorded_at=T3,
    )

    replay = sort_ledger_events_for_replay(
        [late, second, first]
    )

    assert tuple(
        event.event_id for event in replay
    ) == (
        "event-1",
        "event-2",
        "event-3",
    )


def test_all_initial_event_types_are_canonical() -> None:
    assert {
        event_type.value
        for event_type in ExecutionLedgerEventType
    } == {
        "PLAN_CREATED",
        "GROUP_CREATED",
        "GROUP_STATE_CHANGED",
        "LEG_CREATED",
        "LEG_STATE_CHANGED",
        "ORDER_CREATED",
        "ORDER_SUBMITTED",
        "ORDER_ACCEPTED",
        "ORDER_PARTIALLY_FILLED",
        "ORDER_FILLED",
        "ORDER_REJECTED",
        "ORDER_CANCELLED",
        "FILL_RECORDED",
        "RECOVERY_STARTED",
        "RECOVERY_COMPLETED",
        "RECONCILIATION_DISCREPANCY",
        "RECONCILIATION_RESOLVED",
    }
