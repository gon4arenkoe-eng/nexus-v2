"""Canonical NEXUS V2 TradeIntent domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from packages.contracts.identities import AccountId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_positive_decimal,
)


class TradeIntentKind(StrEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    REDUCE = "REDUCE"
    REBALANCE = "REBALANCE"


class TradeIntentShape(StrEnum):
    SINGLE_LEG = "SINGLE_LEG"
    PAIR = "PAIR"
    BASKET = "BASKET"


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


def _require_non_empty_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class TradeLegIntent:
    leg_id: str
    instrument_id: InstrumentId
    account_id: AccountId
    side: TradeSide
    quantity: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "leg_id",
            _require_non_empty_text(
                self.leg_id,
                field_name="leg_id",
            ),
        )

        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")

        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")

        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

        if not isinstance(self.side, TradeSide):
            raise ValueError("side must be a TradeSide")

        if self.quantity is not None:
            object.__setattr__(
                self,
                "quantity",
                require_positive_decimal(
                    self.quantity,
                    field_name="quantity",
                ),
            )


@dataclass(frozen=True, slots=True)
class TradeIntent:
    intent_id: str
    user_id: int
    strategy: str
    strategy_version: str
    source: str
    kind: TradeIntentKind
    shape: TradeIntentShape
    legs: tuple[TradeLegIntent, ...]
    created_at: datetime
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "intent_id",
            _require_non_empty_text(
                self.intent_id,
                field_name="intent_id",
            ),
        )

        if isinstance(self.user_id, bool) or not isinstance(
            self.user_id,
            int,
        ):
            raise ValueError("user_id must be an integer")

        if self.user_id <= 0:
            raise ValueError("user_id must be positive")

        for field_name in (
            "strategy",
            "strategy_version",
            "source",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if not isinstance(self.kind, TradeIntentKind):
            raise ValueError("kind must be a TradeIntentKind")

        if not isinstance(self.shape, TradeIntentShape):
            raise ValueError("shape must be a TradeIntentShape")

        if not isinstance(self.legs, tuple):
            raise ValueError("legs must be a tuple")

        if not all(
            isinstance(leg, TradeLegIntent)
            for leg in self.legs
        ):
            raise ValueError(
                "all legs must be TradeLegIntent"
            )

        if self.shape is TradeIntentShape.SINGLE_LEG:
            required_leg_count = len(self.legs) == 1
        elif self.shape is TradeIntentShape.PAIR:
            required_leg_count = len(self.legs) == 2
        else:
            required_leg_count = len(self.legs) >= 2

        if not required_leg_count:
            raise ValueError(
                f"invalid leg count for {self.shape.value}"
            )

        leg_ids = tuple(leg.leg_id for leg in self.legs)
        if len(set(leg_ids)) != len(leg_ids):
            raise ValueError("leg IDs must be unique")

        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(
                self.created_at,
                field_name="created_at",
            ),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
