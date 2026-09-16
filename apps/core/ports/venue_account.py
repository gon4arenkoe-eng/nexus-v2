"""Canonical venue account and balance observation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from packages.contracts.identities import AccountId
from packages.contracts.primitives import normalize_utc_datetime


class VenueAccountObservationState(StrEnum):
    """Quality state of one canonical venue account observation."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


def _require_decimal(
    value: Decimal,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(
            f"{field_name} must be a Decimal"
        )

    if not value.is_finite():
        raise ValueError(
            f"{field_name} must be finite"
        )

    return value


def _require_asset(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("asset must be a string")

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError("asset must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class VenueBalance:
    """Canonical balance observation for one venue asset."""

    asset: str
    total: Decimal
    available: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _require_asset(self.asset),
        )

        object.__setattr__(
            self,
            "total",
            _require_decimal(
                self.total,
                field_name="total",
            ),
        )

        object.__setattr__(
            self,
            "available",
            _require_decimal(
                self.available,
                field_name="available",
            ),
        )

    @property
    def currency(self) -> str:
        """Compatibility alias; canonical identity is asset."""

        return self.asset


@dataclass(frozen=True, slots=True)
class VenueAccountState:
    """Canonical account/balance observation from one venue account."""

    account_id: AccountId
    state: VenueAccountObservationState
    observed_at: datetime
    balances: tuple[VenueBalance, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.account_id,
            AccountId,
        ):
            raise ValueError(
                "account_id must be an AccountId"
            )

        if not isinstance(
            self.state,
            VenueAccountObservationState,
        ):
            raise ValueError(
                "state must be a VenueAccountObservationState"
            )

        if not isinstance(self.balances, tuple):
            raise ValueError(
                "balances must be a tuple"
            )

        for balance in self.balances:
            if not isinstance(balance, VenueBalance):
                raise ValueError(
                    "balances must contain VenueBalance values"
                )

        ordered = tuple(
            sorted(
                self.balances,
                key=lambda balance: balance.asset,
            )
        )

        assets = tuple(
            balance.asset
            for balance in ordered
        )

        if len(assets) != len(set(assets)):
            raise ValueError(
                "duplicate asset in venue account balances"
            )

        if (
            self.state
            is VenueAccountObservationState.UNAVAILABLE
            and ordered
        ):
            raise ValueError(
                "unavailable account observation cannot carry balances"
            )

        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )

        object.__setattr__(
            self,
            "balances",
            ordered,
        )
