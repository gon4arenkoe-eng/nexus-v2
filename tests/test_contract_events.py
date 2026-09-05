from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from packages.contracts.events import EventEnvelope


def make_event(**overrides: object) -> EventEnvelope[dict[str, object]]:
    values: dict[str, object] = {
        "event_id": "evt-001",
        "event_type": "ORDER_ACCEPTED",
        "event_version": 1,
        "source": "core.execution",
        "occurred_at": datetime(2026, 9, 5, 12, 0, tzinfo=UTC),
        "recorded_at": datetime(2026, 9, 5, 12, 0, 1, tzinfo=UTC),
        "payload": {"order_id": "order-001"},
        "correlation_id": "workflow-001",
        "causation_id": "cmd-001",
    }
    values.update(overrides)
    return EventEnvelope(**values)  # type: ignore[arg-type]


def test_event_envelope_preserves_canonical_fields() -> None:
    event = make_event()

    assert event.event_id == "evt-001"
    assert event.event_type == "ORDER_ACCEPTED"
    assert event.event_version == 1
    assert event.source == "core.execution"
    assert event.payload == {"order_id": "order-001"}
    assert event.correlation_id == "workflow-001"
    assert event.causation_id == "cmd-001"


@pytest.mark.parametrize(
    "field_name",
    [
        "event_id",
        "event_type",
        "source",
    ],
)
def test_required_text_fields_reject_empty(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_event(**{field_name: "   "})


@pytest.mark.parametrize(
    "event_version",
    [0, -1, True, 1.5, "1"],
)
def test_event_version_must_be_positive_integer(
    event_version: object,
) -> None:
    with pytest.raises(ValueError):
        make_event(event_version=event_version)


def test_optional_lineage_may_be_absent() -> None:
    event = make_event(
        correlation_id=None,
        causation_id=None,
    )

    assert event.correlation_id is None
    assert event.causation_id is None


@pytest.mark.parametrize(
    "field_name",
    [
        "correlation_id",
        "causation_id",
    ],
)
def test_optional_lineage_rejects_empty_text(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_event(**{field_name: "   "})


def test_event_times_are_normalized_to_utc() -> None:
    source_tz = timezone(timedelta(hours=3))

    event = make_event(
        occurred_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            tzinfo=source_tz,
        ),
        recorded_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            1,
            tzinfo=source_tz,
        ),
    )

    assert event.occurred_at == datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=UTC,
    )
    assert event.recorded_at == datetime(
        2026,
        9,
        5,
        12,
        0,
        1,
        tzinfo=UTC,
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "occurred_at",
        "recorded_at",
    ],
)
def test_naive_event_time_fails_closed(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_event(
            **{
                field_name: datetime(
                    2026,
                    9,
                    5,
                    12,
                    0,
                )
            }
        )


def test_occurred_at_and_recorded_at_remain_distinct() -> None:
    occurred_at = datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=UTC,
    )
    recorded_at = datetime(
        2026,
        9,
        5,
        12,
        5,
        tzinfo=UTC,
    )

    event = make_event(
        occurred_at=occurred_at,
        recorded_at=recorded_at,
    )

    assert event.occurred_at == occurred_at
    assert event.recorded_at == recorded_at
    assert event.occurred_at != event.recorded_at


def test_payload_is_generic_and_not_execution_specific() -> None:
    event = EventEnvelope[str](
        event_id="evt-message-001",
        event_type="SYSTEM_NOTICE",
        event_version=1,
        source="system",
        occurred_at=datetime(2026, 9, 5, 12, 0, tzinfo=UTC),
        recorded_at=datetime(2026, 9, 5, 12, 0, tzinfo=UTC),
        payload="maintenance",
    )

    assert event.payload == "maintenance"


def test_event_envelope_is_frozen() -> None:
    event = make_event()

    with pytest.raises(AttributeError):
        event.event_type = "ORDER_FILLED"  # type: ignore[misc]
