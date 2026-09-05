"""Canonical NEXUS V2 venue execution contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import FrozenSet

from apps.core.domain.orders import OrderSide, OrderType

from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)
from packages.contracts.primitives import require_positive_decimal


class VenueCapability(StrEnum):
    MARKET_DATA = "MARKET_DATA"
    HISTORICAL_CANDLES = "HISTORICAL_CANDLES"
    LEVERAGE = "LEVERAGE"
    HEDGE_MODE = "HEDGE_MODE"
    NATIVE_STOP_LOSS = "NATIVE_STOP_LOSS"
    NATIVE_TAKE_PROFIT = "NATIVE_TAKE_PROFIT"
    FUNDING_HISTORY = "FUNDING_HISTORY"
    ORDER_QUERY = "ORDER_QUERY"
    OPEN_ORDER_QUERY = "OPEN_ORDER_QUERY"


@dataclass(frozen=True, slots=True)
class VenueCapabilities:
    supported: FrozenSet[VenueCapability]

    def supports(self, capability: VenueCapability) -> bool:
        if not isinstance(capability, VenueCapability):
            return False
        return capability in self.supported

    def require(self, capability: VenueCapability) -> None:
        if not isinstance(capability, VenueCapability):
            raise ValueError("unknown venue capability")
        if capability not in self.supported:
            raise ValueError(
                f"unsupported venue capability: {capability.value}"
            )


class VenueOrderState(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


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
class VenueOrderRequest:
    client_order_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    reduce_only: bool = False

    def __post_init__(self) -> None:
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

        if not isinstance(self.side, OrderSide):
            raise ValueError("side must be an OrderSide")

        if not isinstance(self.order_type, OrderType):
            raise ValueError(
                "order_type must be an OrderType"
            )

        object.__setattr__(
            self,
            "quantity",
            require_positive_decimal(
                self.quantity,
                field_name="quantity",
            ),
        )

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
class VenueOrderResult:
    client_order_id: str
    venue_order_id: str | None
    state: VenueOrderState
    requested_quantity: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal | None = None
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "client_order_id",
            _require_non_empty_text(
                self.client_order_id,
                field_name="client_order_id",
            ),
        )

        if self.venue_order_id is not None:
            object.__setattr__(
                self,
                "venue_order_id",
                _require_non_empty_text(
                    self.venue_order_id,
                    field_name="venue_order_id",
                ),
            )

        if not isinstance(self.state, VenueOrderState):
            raise ValueError(
                "state must be a VenueOrderState"
            )

        object.__setattr__(
            self,
            "requested_quantity",
            require_positive_decimal(
                self.requested_quantity,
                field_name="requested_quantity",
            ),
        )

        if not isinstance(self.filled_quantity, Decimal):
            raise ValueError(
                "filled_quantity must be Decimal"
            )

        if not self.filled_quantity.is_finite():
            raise ValueError(
                "filled_quantity must be finite"
            )

        if self.filled_quantity < Decimal("0"):
            raise ValueError(
                "filled_quantity must not be negative"
            )

        if self.filled_quantity > self.requested_quantity:
            raise ValueError(
                "filled_quantity exceeds requested_quantity"
            )

        if self.average_fill_price is not None:
            object.__setattr__(
                self,
                "average_fill_price",
                require_positive_decimal(
                    self.average_fill_price,
                    field_name="average_fill_price",
                ),
            )

        if (
            self.filled_quantity > Decimal("0")
            and self.average_fill_price is None
        ):
            raise ValueError(
                "filled order quantity requires average_fill_price"
            )

        if self.state is VenueOrderState.FILLED:
            if self.filled_quantity != self.requested_quantity:
                raise ValueError(
                    "FILLED state requires full requested quantity"
                )

        if self.state is VenueOrderState.PARTIALLY_FILLED:
            if not (
                Decimal("0")
                < self.filled_quantity
                < self.requested_quantity
            ):
                raise ValueError(
                    "PARTIALLY_FILLED requires partial quantity"
                )

        if self.state is VenueOrderState.REJECTED:
            if not isinstance(self.rejection_reason, str):
                raise ValueError(
                    "REJECTED state requires rejection_reason"
                )

            object.__setattr__(
                self,
                "rejection_reason",
                _require_non_empty_text(
                    self.rejection_reason,
                    field_name="rejection_reason",
                ),
            )


class VenueAdapter(ABC):
    @property
    @abstractmethod
    def capabilities(self) -> VenueCapabilities:
        """Return explicitly supported venue capabilities."""

    @abstractmethod
    async def submit_order(
        self,
        request: VenueOrderRequest,
    ) -> VenueOrderResult:
        """Submit one normalized order request."""

    @abstractmethod
    async def cancel_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: str,
    ) -> VenueOrderResult:
        """Cancel one normalized venue order."""

    @abstractmethod
    async def get_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: str,
    ) -> VenueOrderResult:
        """Query one normalized venue order."""
