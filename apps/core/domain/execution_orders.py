"""Canonical NEXUS V2 execution order and fill contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from apps.core.domain.orders import OrderSide, OrderType
from packages.contracts.identities import AccountId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


class ExecutionOrderStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
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


def _normalize_optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _require_non_empty_text(
        value,
        field_name=field_name,
    )


def _normalize_optional_time(
    value: datetime | None,
    *,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None

    return normalize_utc_datetime(
        value,
        field_name=field_name,
    )


def _normalize_optional_price(
    value: Decimal | None,
    *,
    field_name: str,
) -> Decimal | None:
    if value is None:
        return None

    return require_positive_decimal(
        value,
        field_name=field_name,
    )


@dataclass(frozen=True, slots=True)
class ExecutionOrder:
    order_id: str
    plan_id: str
    leg_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    client_order_id: str
    venue_order_id: str | None
    side: OrderSide
    order_type: OrderType
    requested_quantity: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    limit_price: Decimal | None
    reduce_only: bool
    status: ExecutionOrderStatus
    rejection_reason: str | None
    submitted_at: datetime | None
    accepted_at: datetime | None
    filled_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "order_id",
            "plan_id",
            "leg_id",
            "client_order_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        object.__setattr__(
            self,
            "venue_order_id",
            _normalize_optional_text(
                self.venue_order_id,
                field_name="venue_order_id",
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
            raise ValueError("order_type must be an OrderType")

        requested_quantity = require_positive_decimal(
            self.requested_quantity,
            field_name="requested_quantity",
        )
        filled_quantity = require_non_negative_decimal(
            self.filled_quantity,
            field_name="filled_quantity",
        )

        if filled_quantity > requested_quantity:
            raise ValueError(
                "filled_quantity must not exceed requested_quantity"
            )

        average_fill_price = _normalize_optional_price(
            self.average_fill_price,
            field_name="average_fill_price",
        )
        limit_price = _normalize_optional_price(
            self.limit_price,
            field_name="limit_price",
        )

        if (
            filled_quantity == Decimal("0")
            and average_fill_price is not None
        ):
            raise ValueError(
                "average_fill_price requires positive filled_quantity"
            )

        if (
            filled_quantity > Decimal("0")
            and average_fill_price is None
        ):
            raise ValueError(
                "positive filled_quantity requires average_fill_price"
            )

        if self.order_type is OrderType.MARKET:
            if limit_price is not None:
                raise ValueError(
                    "MARKET order must not have limit_price"
                )

        if self.order_type is OrderType.LIMIT:
            if limit_price is None:
                raise ValueError(
                    "LIMIT order requires limit_price"
                )

        if not isinstance(self.reduce_only, bool):
            raise ValueError("reduce_only must be a bool")

        if not isinstance(self.status, ExecutionOrderStatus):
            raise ValueError(
                "status must be an ExecutionOrderStatus"
            )

        rejection_reason = _normalize_optional_text(
            self.rejection_reason,
            field_name="rejection_reason",
        )

        if (
            self.status is ExecutionOrderStatus.REJECTED
            and rejection_reason is None
        ):
            raise ValueError(
                "REJECTED order requires rejection_reason"
            )

        if (
            self.status is not ExecutionOrderStatus.REJECTED
            and rejection_reason is not None
        ):
            raise ValueError(
                "rejection_reason is only valid for REJECTED order"
            )

        if self.status is ExecutionOrderStatus.PENDING:
            if filled_quantity != Decimal("0"):
                raise ValueError(
                    "PENDING order requires zero filled_quantity"
                )

        if self.status in (
            ExecutionOrderStatus.SUBMITTED,
            ExecutionOrderStatus.ACCEPTED,
        ):
            if filled_quantity != Decimal("0"):
                raise ValueError(
                    f"{self.status} order requires zero filled_quantity"
                )

        if self.status is ExecutionOrderStatus.PARTIALLY_FILLED:
            if not (
                Decimal("0")
                < filled_quantity
                < requested_quantity
            ):
                raise ValueError(
                    "PARTIALLY_FILLED requires "
                    "0 < filled_quantity < requested_quantity"
                )

        if self.status is ExecutionOrderStatus.FILLED:
            if filled_quantity != requested_quantity:
                raise ValueError(
                    "FILLED order requires filled_quantity "
                    "equal to requested_quantity"
                )

        submitted_at = _normalize_optional_time(
            self.submitted_at,
            field_name="submitted_at",
        )
        accepted_at = _normalize_optional_time(
            self.accepted_at,
            field_name="accepted_at",
        )
        filled_at = _normalize_optional_time(
            self.filled_at,
            field_name="filled_at",
        )
        cancelled_at = _normalize_optional_time(
            self.cancelled_at,
            field_name="cancelled_at",
        )
        created_at = normalize_utc_datetime(
            self.created_at,
            field_name="created_at",
        )
        updated_at = normalize_utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )

        if updated_at < created_at:
            raise ValueError(
                "updated_at must not precede created_at"
            )

        for field_name, value in (
            ("submitted_at", submitted_at),
            ("accepted_at", accepted_at),
            ("filled_at", filled_at),
            ("cancelled_at", cancelled_at),
        ):
            if value is not None and value < created_at:
                raise ValueError(
                    f"{field_name} must not precede created_at"
                )

        if (
            submitted_at is not None
            and accepted_at is not None
            and accepted_at < submitted_at
        ):
            raise ValueError(
                "accepted_at must not precede submitted_at"
            )

        if (
            accepted_at is not None
            and filled_at is not None
            and filled_at < accepted_at
        ):
            raise ValueError(
                "filled_at must not precede accepted_at"
            )

        if (
            submitted_at is not None
            and cancelled_at is not None
            and cancelled_at < submitted_at
        ):
            raise ValueError(
                "cancelled_at must not precede submitted_at"
            )

        if self.status is ExecutionOrderStatus.PENDING:
            if any(
                value is not None
                for value in (
                    submitted_at,
                    accepted_at,
                    filled_at,
                    cancelled_at,
                )
            ):
                raise ValueError(
                    "PENDING order must not have lifecycle timestamps"
                )

        if self.status is ExecutionOrderStatus.FILLED:
            if cancelled_at is not None:
                raise ValueError(
                    "FILLED order must not have cancelled_at"
                )

        if self.status is ExecutionOrderStatus.CANCELLED:
            if filled_at is not None:
                raise ValueError(
                    "CANCELLED order must not have filled_at"
                )

        object.__setattr__(
            self,
            "requested_quantity",
            requested_quantity,
        )
        object.__setattr__(
            self,
            "filled_quantity",
            filled_quantity,
        )
        object.__setattr__(
            self,
            "average_fill_price",
            average_fill_price,
        )
        object.__setattr__(
            self,
            "limit_price",
            limit_price,
        )
        object.__setattr__(
            self,
            "rejection_reason",
            rejection_reason,
        )
        object.__setattr__(
            self,
            "submitted_at",
            submitted_at,
        )
        object.__setattr__(
            self,
            "accepted_at",
            accepted_at,
        )
        object.__setattr__(
            self,
            "filled_at",
            filled_at,
        )
        object.__setattr__(
            self,
            "cancelled_at",
            cancelled_at,
        )
        object.__setattr__(
            self,
            "created_at",
            created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            updated_at,
        )


@dataclass(frozen=True, slots=True)
class ExecutionFill:
    fill_id: str
    order_id: str
    venue_fill_id: str | None
    quantity: Decimal
    price: Decimal
    fee: Decimal
    fee_currency: str | None
    executed_at: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fill_id",
            _require_non_empty_text(
                self.fill_id,
                field_name="fill_id",
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
            "venue_fill_id",
            _normalize_optional_text(
                self.venue_fill_id,
                field_name="venue_fill_id",
            ),
        )

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

        fee_currency = _normalize_optional_text(
            self.fee_currency,
            field_name="fee_currency",
        )

        if fee > Decimal("0") and fee_currency is None:
            raise ValueError(
                "positive fee requires fee_currency"
            )

        executed_at = normalize_utc_datetime(
            self.executed_at,
            field_name="executed_at",
        )
        created_at = normalize_utc_datetime(
            self.created_at,
            field_name="created_at",
        )

        if created_at < executed_at:
            raise ValueError(
                "created_at must not precede executed_at"
            )

        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "price", price)
        object.__setattr__(self, "fee", fee)
        object.__setattr__(
            self,
            "fee_currency",
            fee_currency,
        )
        object.__setattr__(
            self,
            "executed_at",
            executed_at,
        )
        object.__setattr__(
            self,
            "created_at",
            created_at,
        )
