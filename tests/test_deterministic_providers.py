from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from packages.contracts.providers import Clock, IdProvider
from packages.testkit.deterministic import (
    DeterministicClock,
    SequenceIdProvider,
)


def test_deterministic_clock_satisfies_clock_protocol() -> None:
    clock: Clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    assert clock.now() == datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=UTC,
    )


def test_clock_normalizes_initial_time_to_utc() -> None:
    source_tz = timezone(timedelta(hours=3))

    clock = DeterministicClock(
        datetime(2026, 9, 5, 15, 0, tzinfo=source_tz)
    )

    assert clock.now() == datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=UTC,
    )


def test_clock_rejects_naive_initial_time() -> None:
    with pytest.raises(ValueError):
        DeterministicClock(
            datetime(2026, 9, 5, 12, 0)
        )


def test_clock_set_is_deterministic() -> None:
    clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    clock.set(
        datetime(2026, 9, 6, 8, 30, tzinfo=UTC)
    )

    assert clock.now() == datetime(
        2026,
        9,
        6,
        8,
        30,
        tzinfo=UTC,
    )


def test_clock_set_rejects_naive_time() -> None:
    clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    with pytest.raises(ValueError):
        clock.set(
            datetime(2026, 9, 6, 8, 30)
        )


def test_clock_advances_exactly() -> None:
    clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    clock.advance(timedelta(seconds=90))

    assert clock.now() == datetime(
        2026,
        9,
        5,
        12,
        1,
        30,
        tzinfo=UTC,
    )


def test_clock_allows_zero_advance() -> None:
    start = datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=UTC,
    )
    clock = DeterministicClock(start)

    clock.advance(timedelta(0))

    assert clock.now() == start


def test_clock_rejects_negative_advance() -> None:
    clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    with pytest.raises(ValueError):
        clock.advance(timedelta(seconds=-1))


def test_clock_rejects_non_timedelta_advance() -> None:
    clock = DeterministicClock(
        datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    )

    with pytest.raises(ValueError):
        clock.advance(1)  # type: ignore[arg-type]


def test_sequence_id_provider_satisfies_protocol() -> None:
    provider: IdProvider = SequenceIdProvider(
        ["evt-001", "evt-002"]
    )

    assert provider.next_id() == "evt-001"
    assert provider.next_id() == "evt-002"


def test_sequence_id_provider_is_repeatable() -> None:
    first = SequenceIdProvider(["a", "b", "c"])
    second = SequenceIdProvider(["a", "b", "c"])

    assert [first.next_id() for _ in range(3)] == [
        second.next_id() for _ in range(3)
    ]


def test_sequence_id_provider_trims_values() -> None:
    provider = SequenceIdProvider(
        ["  evt-001  "]
    )

    assert provider.next_id() == "evt-001"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        123,
        None,
    ],
)
def test_sequence_id_provider_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        SequenceIdProvider([value])  # type: ignore[list-item]


def test_sequence_id_provider_fails_when_exhausted() -> None:
    provider = SequenceIdProvider(["evt-001"])

    assert provider.next_id() == "evt-001"

    with pytest.raises(
        RuntimeError,
        match="deterministic ID sequence exhausted",
    ):
        provider.next_id()


def test_providers_do_not_generate_random_ids() -> None:
    provider = SequenceIdProvider(["known-id"])

    assert provider.next_id() == "known-id"
