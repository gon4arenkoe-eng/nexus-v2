"""Adapter-layer contracts for venue-specific raw payload normalization.

The NEXUS Core never receives venue JSON/dicts. Each venue owns the mapping from
its raw public/private API payloads into canonical Core port values. This module
standardizes that mapper surface without attempting a universal raw parser.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from apps.core.ports.venue import (
    VenueBalance,
    VenueFill,
    VenueOrderResult,
    VenuePosition,
)
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
    VenueId,
    VenueOrderId,
)
from packages.contracts.primitives import normalize_utc_datetime


class NormalizationEntity(StrEnum):
    """Canonical entities that a venue-specific mapper may normalize."""

    INSTRUMENT = "INSTRUMENT"
    ORDER = "ORDER"
    POSITION = "POSITION"
    BALANCE = "BALANCE"
    FILL = "FILL"


@dataclass(frozen=True, slots=True)
class VenueNormalizationProfile:
    """Declared normalization coverage for one venue adapter.

    This is capability metadata only. It does not dispatch raw payloads and it
    does not imply runtime/certification status.
    """

    venue_id: VenueId
    supported: frozenset[NormalizationEntity]

    def __post_init__(self) -> None:
        if not isinstance(self.venue_id, VenueId):
            raise ValueError("venue_id must be a VenueId")
        if not isinstance(self.supported, frozenset):
            raise ValueError("supported must be a frozenset")
        if not self.supported:
            raise ValueError("supported normalization entities must be non-empty")
        if not all(isinstance(item, NormalizationEntity) for item in self.supported):
            raise ValueError("supported contains unknown normalization entity")

    def supports(self, entity: NormalizationEntity) -> bool:
        return isinstance(entity, NormalizationEntity) and entity in self.supported


@dataclass(frozen=True, slots=True)
class OrderNormalizationContext:
    """Optional canonical fallback identity for an order response."""

    fallback_venue_order_id: VenueOrderId | None = None

    def __post_init__(self) -> None:
        if self.fallback_venue_order_id is not None and not isinstance(
            self.fallback_venue_order_id, VenueOrderId
        ):
            raise ValueError("fallback_venue_order_id must be VenueOrderId or None")


@dataclass(frozen=True, slots=True)
class PositionNormalizationContext:
    """Canonical owner/time context for one raw position row."""

    account_id: AccountId
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(self.observed_at, field_name="observed_at"),
        )


@dataclass(frozen=True, slots=True)
class FillNormalizationContext:
    """Canonical owner/instrument/time context for one raw fill row."""

    account_id: AccountId
    fallback_instrument: InstrumentId
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")
        if not isinstance(self.fallback_instrument, InstrumentId):
            raise ValueError("fallback_instrument must be an InstrumentId")
        if self.account_id.venue_id != self.fallback_instrument.venue_id:
            raise ValueError("account and fallback instrument venue must match")
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(self.observed_at, field_name="observed_at"),
        )


@runtime_checkable
class InstrumentPayloadNormalizer(Protocol):
    venue_id: VenueId

    def normalize_instrument(self, raw: Mapping[str, object]) -> InstrumentId: ...


@runtime_checkable
class OrderPayloadNormalizer(Protocol):
    venue_id: VenueId

    def normalize_order(
        self,
        raw: Mapping[str, object],
        *,
        context: OrderNormalizationContext = OrderNormalizationContext(),
    ) -> VenueOrderResult: ...


@runtime_checkable
class PositionPayloadNormalizer(Protocol):
    venue_id: VenueId

    def normalize_position(
        self,
        raw: Mapping[str, object],
        *,
        context: PositionNormalizationContext,
    ) -> VenuePosition | None: ...


@runtime_checkable
class BalancePayloadNormalizer(Protocol):
    venue_id: VenueId

    def normalize_balance(self, raw: Mapping[str, object]) -> VenueBalance: ...


@runtime_checkable
class FillPayloadNormalizer(Protocol):
    venue_id: VenueId

    def normalize_fill(
        self,
        raw: Mapping[str, object],
        *,
        context: FillNormalizationContext,
    ) -> VenueFill: ...


@runtime_checkable
class VenuePayloadNormalizer(
    InstrumentPayloadNormalizer,
    OrderPayloadNormalizer,
    PositionPayloadNormalizer,
    BalancePayloadNormalizer,
    FillPayloadNormalizer,
    Protocol,
):
    """Complete venue-specific mapper surface for P0 certification targets."""

    @property
    def profile(self) -> VenueNormalizationProfile: ...
