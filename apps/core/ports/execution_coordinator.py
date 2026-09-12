"""Ports for deterministic single-leg execution coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.ports.venue import VenueOrderResult
from packages.contracts.identities import (
    AccountId,
    ClientOrderId,
    InstrumentId,
    OrderId,
)
from packages.contracts.primitives import normalize_utc_datetime


@dataclass(frozen=True, slots=True)
class ExecutionCoordinatorStateRecord:
    user_id: int
    order_id: OrderId
    client_order_id: ClientOrderId
    account_id: AccountId
    instrument_id: InstrumentId
    state: ExecutionCoordinatorState
    attempt: int
    venue_order_id: str | None
    updated_at: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")

        if not isinstance(self.order_id, OrderId):
            raise ValueError("order_id must be an OrderId")
        if not isinstance(self.client_order_id, ClientOrderId):
            raise ValueError(
                "client_order_id must be a ClientOrderId"
            )
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError(
                "instrument_id must be an InstrumentId"
            )
        if not isinstance(
            self.state,
            ExecutionCoordinatorState,
        ):
            raise ValueError(
                "state must be an ExecutionCoordinatorState"
            )
        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise ValueError("attempt must be a non-negative integer")
        if (
            self.venue_order_id is not None
            and not self.venue_order_id.strip()
        ):
            raise ValueError("venue_order_id must be non-empty")
        object.__setattr__(
            self,
            "updated_at",
            normalize_utc_datetime(
                self.updated_at,
                field_name="updated_at",
            ),
        )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(
                self.created_at,
                field_name="created_at",
            ),
        )


class ExecutionCoordinatorStateStore(Protocol):
    """Durable checkpoint boundary for coordinator workflow state."""

    async def load(
        self,
        *,
        user_id: int,
        order_id: OrderId,
    ) -> ExecutionCoordinatorStateRecord | None:
        ...

    async def checkpoint(
        self,
        record: ExecutionCoordinatorStateRecord,
    ) -> None:
        ...


class ExecutionCoordinatorEventSink(Protocol):
    """Optional immutable execution lifecycle evidence sink."""

    async def record(
        self,
        *,
        order_id: OrderId,
        event_type: str,
        attempt: int,
        occurred_at: datetime,
        payload: dict[str, object],
    ) -> None:
        ...


# Keep a structural alias available for future adapters/tests.
ExecutionCoordinatorVenueResult = VenueOrderResult
