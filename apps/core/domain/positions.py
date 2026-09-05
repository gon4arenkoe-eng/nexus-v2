"""Canonical NEXUS V2 position ownership and lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from apps.core.domain.intents import TradeIntentShape, TradeSide
from packages.contracts.identities import AccountId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


class PositionGroupStatus(StrEnum):
    PENDING = "PENDING"
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class PositionLegStatus(StrEnum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


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
class PositionGroup:
    group_id: str
    plan_id: str
    user_id: int
    shape: TradeIntentShape
    strategy: str
    strategy_version: str | None
    trade_source: str
    status: PositionGroupStatus
    opened_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "group_id",
            _require_non_empty_text(
                self.group_id,
                field_name="group_id",
            ),
        )
        object.__setattr__(
            self,
            "plan_id",
            _require_non_empty_text(
                self.plan_id,
                field_name="plan_id",
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
            "trade_source",
            _require_non_empty_text(
                self.trade_source,
                field_name="trade_source",
            ),
        )

        if not isinstance(self.status, PositionGroupStatus):
            raise ValueError(
                "status must be a PositionGroupStatus"
            )

        created_at = normalize_utc_datetime(
            self.created_at,
            field_name="created_at",
        )
        updated_at = normalize_utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )
        opened_at = _normalize_optional_time(
            self.opened_at,
            field_name="opened_at",
        )
        closed_at = _normalize_optional_time(
            self.closed_at,
            field_name="closed_at",
        )

        if updated_at < created_at:
            raise ValueError(
                "updated_at must not precede created_at"
            )

        if opened_at is not None and opened_at < created_at:
            raise ValueError(
                "opened_at must not precede created_at"
            )

        if closed_at is not None:
            if opened_at is None:
                raise ValueError(
                    "closed_at requires opened_at"
                )

            if closed_at < opened_at:
                raise ValueError(
                    "closed_at must not precede opened_at"
                )

        if self.status is PositionGroupStatus.PENDING:
            if opened_at is not None or closed_at is not None:
                raise ValueError(
                    "PENDING group must not have lifecycle timestamps"
                )

        if self.status in (
            PositionGroupStatus.OPEN,
            PositionGroupStatus.CLOSING,
        ):
            if opened_at is None:
                raise ValueError(
                    f"{self.status} group requires opened_at"
                )

            if closed_at is not None:
                raise ValueError(
                    f"{self.status} group must not have closed_at"
                )

        if self.status is PositionGroupStatus.CLOSED:
            if opened_at is None or closed_at is None:
                raise ValueError(
                    "CLOSED group requires opened_at and closed_at"
                )

        if (
            self.status is PositionGroupStatus.OPENING
            and closed_at is not None
        ):
            raise ValueError(
                "OPENING group must not have closed_at"
            )

        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "opened_at", opened_at)
        object.__setattr__(self, "closed_at", closed_at)


@dataclass(frozen=True, slots=True)
class PositionLeg:
    group_id: str
    leg_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    side: TradeSide
    target_quantity: Decimal
    filled_quantity: Decimal
    current_quantity: Decimal
    average_entry_price: Decimal | None
    average_exit_price: Decimal | None
    status: PositionLegStatus
    opened_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "group_id",
            _require_non_empty_text(
                self.group_id,
                field_name="group_id",
            ),
        )
        object.__setattr__(
            self,
            "leg_id",
            _require_non_empty_text(
                self.leg_id,
                field_name="leg_id",
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

        target_quantity = require_positive_decimal(
            self.target_quantity,
            field_name="target_quantity",
        )
        filled_quantity = require_non_negative_decimal(
            self.filled_quantity,
            field_name="filled_quantity",
        )
        current_quantity = require_non_negative_decimal(
            self.current_quantity,
            field_name="current_quantity",
        )

        average_entry_price = _normalize_optional_price(
            self.average_entry_price,
            field_name="average_entry_price",
        )
        average_exit_price = _normalize_optional_price(
            self.average_exit_price,
            field_name="average_exit_price",
        )

        if not isinstance(self.status, PositionLegStatus):
            raise ValueError("status must be a PositionLegStatus")

        created_at = normalize_utc_datetime(
            self.created_at,
            field_name="created_at",
        )
        updated_at = normalize_utc_datetime(
            self.updated_at,
            field_name="updated_at",
        )
        opened_at = _normalize_optional_time(
            self.opened_at,
            field_name="opened_at",
        )
        closed_at = _normalize_optional_time(
            self.closed_at,
            field_name="closed_at",
        )

        if updated_at < created_at:
            raise ValueError(
                "updated_at must not precede created_at"
            )

        if opened_at is not None and opened_at < created_at:
            raise ValueError(
                "opened_at must not precede created_at"
            )

        if closed_at is not None:
            if opened_at is None:
                raise ValueError(
                    "closed_at requires opened_at"
                )

            if closed_at < opened_at:
                raise ValueError(
                    "closed_at must not precede opened_at"
                )

        if self.status is PositionLegStatus.PENDING:
            if (
                filled_quantity != Decimal("0")
                or current_quantity != Decimal("0")
                or average_entry_price is not None
                or average_exit_price is not None
                or opened_at is not None
                or closed_at is not None
            ):
                raise ValueError(
                    "PENDING leg must have no execution projection"
                )

        if self.status is PositionLegStatus.OPEN:
            if filled_quantity <= Decimal("0"):
                raise ValueError(
                    "OPEN leg requires positive filled_quantity"
                )

            if current_quantity <= Decimal("0"):
                raise ValueError(
                    "OPEN leg requires positive current_quantity"
                )

            if average_entry_price is None:
                raise ValueError(
                    "OPEN leg requires average_entry_price"
                )

            if opened_at is None:
                raise ValueError(
                    "OPEN leg requires opened_at"
                )

            if closed_at is not None:
                raise ValueError(
                    "OPEN leg must not have closed_at"
                )

        if self.status is PositionLegStatus.CLOSED:
            if filled_quantity <= Decimal("0"):
                raise ValueError(
                    "CLOSED leg requires positive filled_quantity"
                )

            if current_quantity != Decimal("0"):
                raise ValueError(
                    "CLOSED leg requires zero current_quantity"
                )

            if average_entry_price is None:
                raise ValueError(
                    "CLOSED leg requires average_entry_price"
                )

            if average_exit_price is None:
                raise ValueError(
                    "CLOSED leg requires average_exit_price"
                )

            if opened_at is None or closed_at is None:
                raise ValueError(
                    "CLOSED leg requires opened_at and closed_at"
                )

        object.__setattr__(
            self,
            "target_quantity",
            target_quantity,
        )
        object.__setattr__(
            self,
            "filled_quantity",
            filled_quantity,
        )
        object.__setattr__(
            self,
            "current_quantity",
            current_quantity,
        )
        object.__setattr__(
            self,
            "average_entry_price",
            average_entry_price,
        )
        object.__setattr__(
            self,
            "average_exit_price",
            average_exit_price,
        )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "opened_at", opened_at)
        object.__setattr__(self, "closed_at", closed_at)
