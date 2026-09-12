"""Ports for durable pair and basket execution coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.intents import TradeIntentShape
from apps.core.domain.multi_leg_execution import (
    MultiLegExecutionState,
    MultiLegRecoveryPolicy,
)
from packages.contracts.identities import OrderId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


@dataclass(frozen=True, slots=True)
class MultiLegCheckpoint:
    leg_id: str
    order_id: OrderId
    state: ExecutionCoordinatorState
    requested_quantity: Decimal
    filled_quantity: Decimal
    reduce_only: bool

    def __post_init__(self) -> None:
        if not isinstance(self.leg_id, str) or not self.leg_id.strip():
            raise ValueError("leg_id must be non-empty")
        if not isinstance(self.order_id, OrderId):
            raise ValueError("order_id must be an OrderId")
        if not isinstance(self.state, ExecutionCoordinatorState):
            raise ValueError("state must be an ExecutionCoordinatorState")
        object.__setattr__(
            self,
            "requested_quantity",
            require_positive_decimal(
                self.requested_quantity,
                field_name="requested_quantity",
            ),
        )
        object.__setattr__(
            self,
            "filled_quantity",
            require_non_negative_decimal(
                self.filled_quantity,
                field_name="filled_quantity",
            ),
        )
        if self.filled_quantity > self.requested_quantity:
            raise ValueError("filled_quantity exceeds requested_quantity")
        if not isinstance(self.reduce_only, bool):
            raise ValueError("reduce_only must be boolean")


@dataclass(frozen=True, slots=True)
class MultiLegExecutionStateRecord:
    user_id: int
    plan_id: str
    group_id: str
    shape: TradeIntentShape
    state: MultiLegExecutionState
    recovery_policy: MultiLegRecoveryPolicy
    legs: tuple[MultiLegCheckpoint, ...]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")
        for name in ("plan_id", "group_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.shape, TradeIntentShape):
            raise ValueError("shape must be a TradeIntentShape")
        if self.shape is TradeIntentShape.SINGLE_LEG:
            raise ValueError("multi-leg state cannot own SINGLE_LEG shape")
        if not isinstance(self.state, MultiLegExecutionState):
            raise ValueError("state must be a MultiLegExecutionState")
        if not isinstance(self.recovery_policy, MultiLegRecoveryPolicy):
            raise ValueError("invalid recovery_policy")
        if not isinstance(self.legs, tuple) or len(self.legs) < 2:
            raise ValueError("multi-leg state requires at least two legs")
        if not all(isinstance(item, MultiLegCheckpoint) for item in self.legs):
            raise ValueError("legs must contain MultiLegCheckpoint values")
        ids = tuple(item.leg_id for item in self.legs)
        if len(ids) != len(set(ids)):
            raise ValueError("multi-leg checkpoint leg IDs must be unique")
        created_at = normalize_utc_datetime(
            self.created_at,
            field_name="created_at",
        )
        updated_at = normalize_utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )
        if updated_at < created_at:
            raise ValueError("updated_at must not precede created_at")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


class MultiLegExecutionStateStore(Protocol):
    async def load(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> MultiLegExecutionStateRecord | None:
        ...

    async def checkpoint(
        self,
        record: MultiLegExecutionStateRecord,
    ) -> None:
        ...
