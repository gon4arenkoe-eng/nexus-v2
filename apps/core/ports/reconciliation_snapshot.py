"""Canonical read-only local reconciliation snapshot contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
)
from apps.core.domain.positions import PositionLeg
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)


@dataclass(frozen=True, slots=True)
class LocalReconciliationSnapshot:
    """Canonical local truth for one user/account/instrument scope."""

    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    orders: tuple[ExecutionOrder, ...]
    fills: tuple[ExecutionFill, ...]
    positions: tuple[PositionLeg, ...]

    def __post_init__(self) -> None:
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int):
            raise ValueError("user_id must be an integer")

        if self.user_id <= 0:
            raise ValueError("user_id must be positive")

        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")

        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")

        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

        if not isinstance(self.orders, tuple):
            raise ValueError("orders must be a tuple")

        if not isinstance(self.fills, tuple):
            raise ValueError("fills must be a tuple")

        if not isinstance(self.positions, tuple):
            raise ValueError("positions must be a tuple")

        order_ids: set[str] = set()

        for order in self.orders:
            if not isinstance(order, ExecutionOrder):
                raise ValueError(
                    "orders must contain ExecutionOrder values"
                )

            if order.account_id != self.account_id:
                raise ValueError(
                    "order account outside snapshot scope"
                )

            if order.instrument_id != self.instrument_id:
                raise ValueError(
                    "order instrument outside snapshot scope"
                )

            order_id = str(order.order_id)

            if order_id in order_ids:
                raise ValueError(
                    "duplicate order identity in local snapshot"
                )

            order_ids.add(order_id)

        fill_ids: set[str] = set()

        for fill in self.fills:
            if not isinstance(fill, ExecutionFill):
                raise ValueError(
                    "fills must contain ExecutionFill values"
                )

            fill_id = str(fill.fill_id)

            if fill_id in fill_ids:
                raise ValueError(
                    "duplicate fill identity in local snapshot"
                )

            fill_ids.add(fill_id)

            if str(fill.order_id) not in order_ids:
                raise ValueError(
                    "local fill has no owning order in snapshot scope"
                )

        position_ids: set[tuple[str, str]] = set()

        for position in self.positions:
            if not isinstance(position, PositionLeg):
                raise ValueError(
                    "positions must contain PositionLeg values"
                )

            if position.account_id != self.account_id:
                raise ValueError(
                    "position account outside snapshot scope"
                )

            if position.instrument_id != self.instrument_id:
                raise ValueError(
                    "position instrument outside snapshot scope"
                )

            position_id = (
                position.group_id,
                position.leg_id,
            )

            if position_id in position_ids:
                raise ValueError(
                    "duplicate position identity in local snapshot"
                )

            position_ids.add(position_id)


class LocalReconciliationSnapshotProvider(Protocol):
    """Read canonical local reconciliation state without mutation authority."""

    async def load(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> LocalReconciliationSnapshot:
        """Return deterministic local truth for one reconciliation scope."""

        ...
