"""Canonical NEXUS V2 venue execution contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import FrozenSet

from apps.core.domain.orders import OrderSide, OrderType

from packages.contracts.identities import (
    AccountId,
    ClientOrderId,
    InstrumentId,
    VenueFillId,
    VenueOrderId,
)
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


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
    POSITION_QUERY = "POSITION_QUERY"
    ACCOUNT_QUERY = "ACCOUNT_QUERY"
    FILL_QUERY = "FILL_QUERY"


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
    client_order_id: ClientOrderId
    account_id: AccountId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    reduce_only: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.client_order_id,
            ClientOrderId,
        ):
            raise ValueError(
                "client_order_id must be a ClientOrderId"
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
    client_order_id: ClientOrderId
    venue_order_id: VenueOrderId | None
    state: VenueOrderState
    requested_quantity: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal | None = None
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.client_order_id,
            ClientOrderId,
        ):
            raise ValueError(
                "client_order_id must be a ClientOrderId"
            )

        if self.venue_order_id is not None and not isinstance(
            self.venue_order_id,
            VenueOrderId,
        ):
            raise ValueError(
                "venue_order_id must be a VenueOrderId"
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


class VenuePositionSide(StrEnum):
    """Canonical venue position direction."""

    LONG = "LONG"
    SHORT = "SHORT"


def _require_finite_decimal(
    value: Decimal,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be Decimal")

    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return value


from apps.core.ports.venue_account import (
    VenueAccountObservationState,
    VenueAccountState,
    VenueBalance,
)


@dataclass(frozen=True, slots=True)
class VenuePosition:
    """Canonical venue position observation."""

    account_id: AccountId
    instrument_id: InstrumentId
    side: VenuePositionSide
    quantity: Decimal
    entry_price: Decimal | None
    observed_at: datetime

    def __post_init__(self) -> None:
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

        if not isinstance(self.side, VenuePositionSide):
            raise ValueError(
                "side must be a VenuePositionSide"
            )

        quantity = require_non_negative_decimal(
            self.quantity,
            field_name="quantity",
        )

        entry_price = self.entry_price

        if quantity == Decimal("0"):
            if entry_price is not None:
                raise ValueError(
                    "flat venue position must not define entry_price"
                )
        else:
            if entry_price is None:
                raise ValueError(
                    "open venue position requires entry_price"
                )

            entry_price = require_positive_decimal(
                entry_price,
                field_name="entry_price",
            )

        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "entry_price", entry_price)
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class VenueFill:
    """Canonical immutable venue fill observation."""

    account_id: AccountId
    instrument_id: InstrumentId
    venue_fill_id: VenueFillId | None
    venue_order_id: VenueOrderId | None
    client_order_id: ClientOrderId | None
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    fee_currency: str | None
    executed_at: datetime
    observed_at: datetime

    def __post_init__(self) -> None:
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

        if self.venue_fill_id is not None and not isinstance(
            self.venue_fill_id,
            VenueFillId,
        ):
            raise ValueError(
                "venue_fill_id must be a VenueFillId"
            )

        if self.venue_order_id is not None and not isinstance(
            self.venue_order_id,
            VenueOrderId,
        ):
            raise ValueError(
                "venue_order_id must be a VenueOrderId"
            )

        if self.client_order_id is not None and not isinstance(
            self.client_order_id,
            ClientOrderId,
        ):
            raise ValueError(
                "client_order_id must be a ClientOrderId"
            )

        if not isinstance(self.side, OrderSide):
            raise ValueError("side must be an OrderSide")

        quantity = require_positive_decimal(
            self.quantity,
            field_name="quantity",
        )
        price = require_positive_decimal(
            self.price,
            field_name="price",
        )
        fee = require_non_negative_decimal(
            self.fee,
            field_name="fee",
        )

        fee_currency = self.fee_currency

        if fee_currency is not None:
            fee_currency = _require_non_empty_text(
                fee_currency,
                field_name="fee_currency",
            ).upper()

        if fee > Decimal("0") and fee_currency is None:
            raise ValueError(
                "positive fee requires fee_currency"
            )

        executed_at = normalize_utc_datetime(
            self.executed_at,
            field_name="executed_at",
        )
        observed_at = normalize_utc_datetime(
            self.observed_at,
            field_name="observed_at",
        )

        if observed_at < executed_at:
            raise ValueError(
                "observed_at must not precede executed_at"
            )

        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "price", price)
        object.__setattr__(self, "fee", fee)
        object.__setattr__(
            self,
            "fee_currency",
            fee_currency,
        )
        object.__setattr__(self, "executed_at", executed_at)
        object.__setattr__(self, "observed_at", observed_at)


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
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        """Cancel one normalized venue order."""

    @abstractmethod
    async def get_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        """Query one normalized venue order."""

    @abstractmethod
    async def get_open_orders(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
    ) -> tuple[VenueOrderResult, ...]:
        """Read normalized open venue orders."""

    @abstractmethod
    async def get_positions(
        self,
        *,
        account_id: AccountId,
    ) -> tuple[VenuePosition, ...]:
        """Read normalized venue positions."""

    @abstractmethod
    async def get_account_state(
        self,
        *,
        account_id: AccountId,
    ) -> VenueAccountState:
        """Read normalized account and balance state."""

    @abstractmethod
    async def get_fills(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
        since: datetime | None = None,
    ) -> tuple[VenueFill, ...]:
        """Read normalized immutable venue fill observations."""
