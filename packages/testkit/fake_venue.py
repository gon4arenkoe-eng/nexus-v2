"""Deterministic generic fake venue for NEXUS V2 tests."""

from __future__ import annotations

from collections import deque
from typing import Generic, TypeVar


SubmitRequestT = TypeVar("SubmitRequestT")
SubmitResultT = TypeVar("SubmitResultT")
CancelResultT = TypeVar("CancelResultT")


class FakeVenue(
    Generic[
        SubmitRequestT,
        SubmitResultT,
        CancelResultT,
    ]
):
    """Scripted deterministic venue boundary for tests."""

    def __init__(self) -> None:
        self._submit_results: deque[SubmitResultT] = deque()
        self._cancel_results: deque[CancelResultT] = deque()

        self._submitted_requests: list[SubmitRequestT] = []
        self._cancelled_order_ids: list[str] = []

    @property
    def submitted_requests(self) -> tuple[SubmitRequestT, ...]:
        return tuple(self._submitted_requests)

    @property
    def cancelled_order_ids(self) -> tuple[str, ...]:
        return tuple(self._cancelled_order_ids)

    def queue_submit_result(
        self,
        result: SubmitResultT,
    ) -> None:
        self._submit_results.append(result)

    def queue_cancel_result(
        self,
        result: CancelResultT,
    ) -> None:
        self._cancel_results.append(result)

    def submit_order(
        self,
        request: SubmitRequestT,
    ) -> SubmitResultT:
        self._submitted_requests.append(request)

        if not self._submit_results:
            raise RuntimeError(
                "fake venue submit result sequence exhausted"
            )

        return self._submit_results.popleft()

    def cancel_order(
        self,
        client_order_id: str,
    ) -> CancelResultT:
        normalized_id = self._normalize_client_order_id(
            client_order_id
        )
        self._cancelled_order_ids.append(normalized_id)

        if not self._cancel_results:
            raise RuntimeError(
                "fake venue cancel result sequence exhausted"
            )

        return self._cancel_results.popleft()

    @staticmethod
    def _normalize_client_order_id(
        value: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "client_order_id must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "client_order_id must be non-empty"
            )

        return normalized
