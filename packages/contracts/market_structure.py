"""Future-ready multi-market instrument structure contracts for NEXUS V2.

These contracts extend canonical ``InstrumentId`` metadata without changing the
existing execution identity or granting any new runtime/live authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import FrozenSet

from packages.contracts.identities import (
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_positive_decimal,
)


class MarketStructureCapability(StrEnum):
    """Optional market semantics declared by an instrument/venue."""

    TRADING_SESSIONS = "TRADING_SESSIONS"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"
    SHORT_SELLING = "SHORT_SELLING"
    MARGIN = "MARGIN"
    FUNDING = "FUNDING"
    EXPIRY = "EXPIRY"
    EXERCISE = "EXERCISE"
    SETTLEMENT = "SETTLEMENT"
    CONTRACT_MULTIPLIER = "CONTRACT_MULTIPLIER"
    UNDERLYING_REFERENCE = "UNDERLYING_REFERENCE"


class SettlementType(StrEnum):
    NONE = "NONE"
    CASH = "CASH"
    PHYSICAL = "PHYSICAL"


class TradingSessionPolicy(StrEnum):
    CONTINUOUS_24_7 = "CONTINUOUS_24_7"
    CALENDAR = "CALENDAR"
    VENUE_DEFINED = "VENUE_DEFINED"


class OptionRight(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class OptionStyle(StrEnum):
    AMERICAN = "AMERICAN"
    EUROPEAN = "EUROPEAN"
    BERMUDAN = "BERMUDAN"


def _optional_currency(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or None")
    normalized = value.strip().upper()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty when provided")
    return normalized


def _optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or None")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty when provided")
    return normalized


@dataclass(frozen=True, slots=True)
class InstrumentDefinition:
    """Optional canonical properties for multiple asset classes.

    ``InstrumentId`` stays the stable execution identity. This definition adds
    market-specific properties only where they exist, avoiding crypto-only or
    equity-only assumptions in Core.
    """

    instrument_id: InstrumentId
    price_increment: Decimal
    quantity_increment: Decimal
    settlement_currency: str | None = None
    base_currency: str | None = None
    contract_multiplier: Decimal = Decimal("1")
    settlement_type: SettlementType = SettlementType.NONE
    session_policy: TradingSessionPolicy = TradingSessionPolicy.VENUE_DEFINED
    calendar_id: str | None = None
    expiry_at: datetime | None = None
    underlying_instrument_id: InstrumentId | None = None
    strike_price: Decimal | None = None
    option_right: OptionRight | None = None
    option_style: OptionStyle | None = None
    capabilities: FrozenSet[MarketStructureCapability] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")

        object.__setattr__(
            self,
            "price_increment",
            require_positive_decimal(
                self.price_increment,
                field_name="price_increment",
            ),
        )
        object.__setattr__(
            self,
            "quantity_increment",
            require_positive_decimal(
                self.quantity_increment,
                field_name="quantity_increment",
            ),
        )
        object.__setattr__(
            self,
            "contract_multiplier",
            require_positive_decimal(
                self.contract_multiplier,
                field_name="contract_multiplier",
            ),
        )

        object.__setattr__(
            self,
            "settlement_currency",
            _optional_currency(
                self.settlement_currency,
                field_name="settlement_currency",
            ),
        )
        object.__setattr__(
            self,
            "base_currency",
            _optional_currency(
                self.base_currency,
                field_name="base_currency",
            ),
        )
        object.__setattr__(
            self,
            "calendar_id",
            _optional_text(self.calendar_id, field_name="calendar_id"),
        )

        if not isinstance(self.settlement_type, SettlementType):
            raise ValueError("settlement_type must be SettlementType")
        if not isinstance(self.session_policy, TradingSessionPolicy):
            raise ValueError("session_policy must be TradingSessionPolicy")
        if not isinstance(self.capabilities, frozenset):
            raise ValueError("capabilities must be a frozenset")
        if not all(
            isinstance(value, MarketStructureCapability)
            for value in self.capabilities
        ):
            raise ValueError(
                "capabilities must contain MarketStructureCapability values"
            )

        if self.expiry_at is not None:
            object.__setattr__(
                self,
                "expiry_at",
                normalize_utc_datetime(
                    self.expiry_at,
                    field_name="expiry_at",
                ),
            )

        if self.underlying_instrument_id is not None and not isinstance(
            self.underlying_instrument_id,
            InstrumentId,
        ):
            raise ValueError(
                "underlying_instrument_id must be InstrumentId or None"
            )

        if self.strike_price is not None:
            object.__setattr__(
                self,
                "strike_price",
                require_positive_decimal(
                    self.strike_price,
                    field_name="strike_price",
                ),
            )

        option_fields = (
            self.strike_price,
            self.option_right,
            self.option_style,
        )
        has_option_metadata = any(value is not None for value in option_fields)

        if self.instrument_id.instrument_type is InstrumentType.OPTION:
            if self.expiry_at is None:
                raise ValueError("OPTION requires expiry_at")
            if self.underlying_instrument_id is None:
                raise ValueError("OPTION requires underlying_instrument_id")
            if self.strike_price is None:
                raise ValueError("OPTION requires strike_price")
            if not isinstance(self.option_right, OptionRight):
                raise ValueError("OPTION requires option_right")
            if not isinstance(self.option_style, OptionStyle):
                raise ValueError("OPTION requires option_style")
        elif has_option_metadata:
            raise ValueError(
                "option metadata is only valid for OPTION instruments"
            )

        if (
            self.session_policy is TradingSessionPolicy.CALENDAR
            and self.calendar_id is None
        ):
            raise ValueError("CALENDAR session policy requires calendar_id")


@dataclass(frozen=True, slots=True)
class VenueMarketProfile:
    """Capability declaration for a venue without transport/client coupling."""

    venue_id: VenueId
    asset_classes: FrozenSet[AssetClass]
    instrument_types: FrozenSet[InstrumentType]
    capabilities: FrozenSet[MarketStructureCapability]

    def __post_init__(self) -> None:
        if not isinstance(self.venue_id, VenueId):
            raise ValueError("venue_id must be VenueId")
        if not isinstance(self.asset_classes, frozenset) or not all(
            isinstance(value, AssetClass) for value in self.asset_classes
        ):
            raise ValueError("asset_classes must contain AssetClass values")
        if not isinstance(self.instrument_types, frozenset) or not all(
            isinstance(value, InstrumentType) for value in self.instrument_types
        ):
            raise ValueError(
                "instrument_types must contain InstrumentType values"
            )
        if not isinstance(self.capabilities, frozenset) or not all(
            isinstance(value, MarketStructureCapability)
            for value in self.capabilities
        ):
            raise ValueError(
                "capabilities must contain MarketStructureCapability values"
            )

    def supports_asset_class(self, asset_class: AssetClass) -> bool:
        return asset_class in self.asset_classes

    def supports_instrument_type(self, instrument_type: InstrumentType) -> bool:
        return instrument_type in self.instrument_types

    def supports_capability(
        self,
        capability: MarketStructureCapability,
    ) -> bool:
        return capability in self.capabilities
