"""Canonical immutable NEXUS V2 execution-plan contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.orders import OrderType
from packages.contracts.identities import AccountId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_positive_decimal,
)


def _require_non_empty_text(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class ExecutionLegPlan:
    leg_id: str
    order_id: str
    client_order_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    side: TradeSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    reduce_only: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "leg_id",
            _require_non_empty_text(
                self.leg_id,
                field_name="leg_id",
            ),
        )

        object.__setattr__(
            self,
            "order_id",
            _require_non_empty_text(
                self.order_id,
                field_name="order_id",
            ),
        )

        object.__setattr__(
            self,
            "client_order_id",
            _require_non_empty_text(
                self.client_order_id,
                field_name="client_order_id",
            ),
        )

        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")

        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError(
                "instrument_id must be an InstrumentId"
            )

        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

        if not isinstance(self.side, TradeSide):
            raise ValueError("side must be a TradeSide")

        object.__setattr__(
            self,
            "quantity",
            require_positive_decimal(
                self.quantity,
                field_name="quantity",
            ),
        )

        if not isinstance(self.order_type, OrderType):
            raise ValueError("order_type must be an OrderType")

        if self.order_type is OrderType.MARKET:
            if self.limit_price is not None:
                raise ValueError(
                    "MARKET order must not define limit_price"
                )

        elif self.order_type is OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError(
                    "LIMIT order requires limit_price"
                )

            object.__setattr__(
                self,
                "limit_price",
                require_positive_decimal(
                    self.limit_price,
                    field_name="limit_price",
                ),
            )

        if not isinstance(self.reduce_only, bool):
            raise ValueError("reduce_only must be boolean")


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    plan_id: str
    intent_id: str
    user_id: int
    shape: TradeIntentShape
    strategy: str
    strategy_version: str | None
    source: str
    legs: tuple[ExecutionLegPlan, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "plan_id",
            _require_non_empty_text(
                self.plan_id,
                field_name="plan_id",
            ),
        )

        object.__setattr__(
            self,
            "intent_id",
            _require_non_empty_text(
                self.intent_id,
                field_name="intent_id",
            ),
        )

        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")

        if not isinstance(self.shape, TradeIntentShape):
            raise ValueError("shape must be a TradeIntentShape")

        object.__setattr__(
            self,
            "strategy",
            _require_non_empty_text(
                self.strategy,
                field_name="strategy",
            ),
        )

        if self.strategy_version is not None:
            object.__setattr__(
                self,
                "strategy_version",
                _require_non_empty_text(
                    self.strategy_version,
                    field_name="strategy_version",
                ),
            )

        object.__setattr__(
            self,
            "source",
            _require_non_empty_text(
                self.source,
                field_name="source",
            ),
        )

        if not isinstance(self.legs, tuple):
            raise ValueError("legs must be a tuple")

        if not self.legs:
            raise ValueError(
                "execution plan must contain at least one leg"
            )

        if not all(
            isinstance(leg, ExecutionLegPlan)
            for leg in self.legs
        ):
            raise ValueError(
                "legs must contain only ExecutionLegPlan values"
            )

        leg_ids = [leg.leg_id for leg in self.legs]
        order_ids = [leg.order_id for leg in self.legs]
        client_order_ids = [
            leg.client_order_id
            for leg in self.legs
        ]

        if len(set(leg_ids)) != len(leg_ids):
            raise ValueError("leg_id values must be unique")

        if len(set(order_ids)) != len(order_ids):
            raise ValueError("order_id values must be unique")

        if len(set(client_order_ids)) != len(client_order_ids):
            raise ValueError(
                "client_order_id values must be unique"
            )

        leg_count = len(self.legs)

        if (
            self.shape is TradeIntentShape.SINGLE_LEG
            and leg_count != 1
        ):
            raise ValueError(
                "SINGLE_LEG execution plan requires exactly one leg"
            )

        if (
            self.shape is TradeIntentShape.PAIR
            and leg_count != 2
        ):
            raise ValueError(
                "PAIR execution plan requires exactly two legs"
            )

        if (
            self.shape is TradeIntentShape.BASKET
            and leg_count < 2
        ):
            raise ValueError(
                "BASKET execution plan requires at least two legs"
            )

        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(
                self.created_at,
                field_name="created_at",
            ),
        )
