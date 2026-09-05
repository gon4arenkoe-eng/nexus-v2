from __future__ import annotations

from dataclasses import dataclass

import pytest

from packages.testkit.fake_venue import FakeVenue


@dataclass(frozen=True, slots=True)
class Request:
    client_order_id: str


@dataclass(frozen=True, slots=True)
class SubmitResult:
    state: str


@dataclass(frozen=True, slots=True)
class CancelResult:
    cancelled: bool


def test_submit_returns_scripted_result() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    result = SubmitResult(state="ACCEPTED")
    venue.queue_submit_result(result)

    request = Request(client_order_id="order-001")

    assert venue.submit_order(request) is result


def test_submit_records_request() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    venue.queue_submit_result(
        SubmitResult(state="ACCEPTED")
    )

    request = Request(client_order_id="order-001")

    venue.submit_order(request)

    assert venue.submitted_requests == (request,)


def test_submit_preserves_call_order() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    venue.queue_submit_result(
        SubmitResult(state="ACCEPTED")
    )
    venue.queue_submit_result(
        SubmitResult(state="REJECTED")
    )

    first = Request(client_order_id="order-001")
    second = Request(client_order_id="order-002")

    venue.submit_order(first)
    venue.submit_order(second)

    assert venue.submitted_requests == (
        first,
        second,
    )


def test_submit_results_are_fifo() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    accepted = SubmitResult(state="ACCEPTED")
    rejected = SubmitResult(state="REJECTED")

    venue.queue_submit_result(accepted)
    venue.queue_submit_result(rejected)

    first = venue.submit_order(
        Request(client_order_id="order-001")
    )
    second = venue.submit_order(
        Request(client_order_id="order-002")
    )

    assert first is accepted
    assert second is rejected


def test_submit_fails_when_sequence_exhausted() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    with pytest.raises(
        RuntimeError,
        match="submit result sequence exhausted",
    ):
        venue.submit_order(
            Request(client_order_id="order-001")
        )


def test_exhausted_submit_still_records_attempt() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    request = Request(client_order_id="order-001")

    with pytest.raises(RuntimeError):
        venue.submit_order(request)

    assert venue.submitted_requests == (request,)


def test_cancel_returns_scripted_result() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    result = CancelResult(cancelled=True)
    venue.queue_cancel_result(result)

    assert venue.cancel_order("order-001") is result


def test_cancel_records_normalized_id() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    venue.queue_cancel_result(
        CancelResult(cancelled=True)
    )

    venue.cancel_order("  order-001  ")

    assert venue.cancelled_order_ids == (
        "order-001",
    )


def test_cancel_results_are_fifo() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    first_result = CancelResult(cancelled=True)
    second_result = CancelResult(cancelled=False)

    venue.queue_cancel_result(first_result)
    venue.queue_cancel_result(second_result)

    assert venue.cancel_order("order-001") is first_result
    assert venue.cancel_order("order-002") is second_result


def test_cancel_fails_when_sequence_exhausted() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    with pytest.raises(
        RuntimeError,
        match="cancel result sequence exhausted",
    ):
        venue.cancel_order("order-001")


def test_exhausted_cancel_still_records_attempt() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    with pytest.raises(RuntimeError):
        venue.cancel_order("order-001")

    assert venue.cancelled_order_ids == (
        "order-001",
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        123,
        None,
    ],
)
def test_cancel_rejects_invalid_client_order_id(
    value: object,
) -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    venue.queue_cancel_result(
        CancelResult(cancelled=True)
    )

    with pytest.raises(ValueError):
        venue.cancel_order(value)  # type: ignore[arg-type]

    assert venue.cancelled_order_ids == ()


def test_recorded_call_views_are_immutable() -> None:
    venue = FakeVenue[
        Request,
        SubmitResult,
        CancelResult,
    ]()

    venue.queue_submit_result(
        SubmitResult(state="ACCEPTED")
    )
    venue.queue_cancel_result(
        CancelResult(cancelled=True)
    )

    venue.submit_order(
        Request(client_order_id="order-001")
    )
    venue.cancel_order("order-001")

    assert isinstance(
        venue.submitted_requests,
        tuple,
    )
    assert isinstance(
        venue.cancelled_order_ids,
        tuple,
    )


def test_fake_venue_does_not_interpret_outcomes() -> None:
    venue = FakeVenue[
        Request,
        dict[str, object],
        dict[str, object],
    ]()

    submit_result = {
        "arbitrary": "submit-value",
    }
    cancel_result = {
        "arbitrary": "cancel-value",
    }

    venue.queue_submit_result(submit_result)
    venue.queue_cancel_result(cancel_result)

    assert (
        venue.submit_order(
            Request(client_order_id="order-001")
        )
        is submit_result
    )
    assert (
        venue.cancel_order("order-001")
        is cancel_result
    )
