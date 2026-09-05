"""Canonical NEXUS V2 identity contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssetClass(StrEnum):
    CRYPTO = "CRYPTO"
    EQUITY = "EQUITY"
    ETF = "ETF"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    BOND = "BOND"
    INDEX = "INDEX"
    CFD = "CFD"


class InstrumentType(StrEnum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    STOCK = "STOCK"
    ETF = "ETF"
    FX_PAIR = "FX_PAIR"
    CFD = "CFD"


def _canonical_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip().upper()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class VenueId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _canonical_text(self.value, field_name="venue_id"),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AccountId:
    venue_id: VenueId
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.venue_id, VenueId):
            raise ValueError("venue_id must be a VenueId")

        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise ValueError("account_id value must be an integer")

        if self.value <= 0:
            raise ValueError("account_id value must be positive")


@dataclass(frozen=True, slots=True)
class InstrumentId:
    venue_id: VenueId
    native_symbol: str
    instrument_type: InstrumentType
    asset_class: AssetClass

    def __post_init__(self) -> None:
        if not isinstance(self.venue_id, VenueId):
            raise ValueError("venue_id must be a VenueId")

        object.__setattr__(
            self,
            "native_symbol",
            _canonical_text(
                self.native_symbol,
                field_name="native_symbol",
            ),
        )

        if not isinstance(self.instrument_type, InstrumentType):
            raise ValueError("instrument_type must be an InstrumentType")

        if not isinstance(self.asset_class, AssetClass):
            raise ValueError("asset_class must be an AssetClass")
