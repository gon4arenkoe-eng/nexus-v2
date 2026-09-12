"""Ports for Grid Trading Desk ownership boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from apps.core.domain.grid_trading import (
    GridFillAttribution,
    GridInstance,
    GridLevel,
    GridReconciliationState,
)


@dataclass(frozen=True, slots=True)
class GridOrderOutcome:
    client_order_ref: str
    accepted: bool
    unknown: bool = False


class GridInstanceStore(Protocol):
    async def load(self, *, user_id: int, instance_id: str) -> GridInstance | None:  # noqa: E501
        ...

    async def checkpoint(self, instance: GridInstance) -> None:
        ...

    async def list_for_user(self, *, user_id: int) -> tuple[GridInstance, ...]:
        ...


class GridExecutionBoundary(Protocol):
    async def place_level(
        self,
        *,
        instance: GridInstance,
        level: GridLevel,
        now: datetime,
    ) -> GridOrderOutcome:
        ...

    async def cancel_level(
        self,
        *,
        instance: GridInstance,
        level: GridLevel,
        now: datetime,
    ) -> GridOrderOutcome:
        ...

    async def reduce_inventory(
        self,
        *,
        instance: GridInstance,
        quantity: Decimal,
        now: datetime,
    ) -> GridOrderOutcome:
        ...


class GridCapitalRiskPort(Protocol):
    async def reserve(self, *, instance: GridInstance) -> bool:
        ...

    async def release(self, *, instance: GridInstance) -> None:
        ...


class GridLedgerReader(Protocol):
    async def fills_for_instance(
        self,
        *,
        user_id: int,
        instance_id: str,
    ) -> tuple[GridFillAttribution, ...]:
        ...


class GridReconciliationPort(Protocol):
    async def state_for_instance(
        self,
        *,
        instance: GridInstance,
    ) -> GridReconciliationState:
        ...
