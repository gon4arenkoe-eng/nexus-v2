from __future__ import annotations

from datetime import UTC, datetime

import pytest

from adapters.common.normalization import (
    FillNormalizationContext,
    NormalizationEntity,
    PositionNormalizationContext,
    VenueNormalizationProfile,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)
from packages.testkit.venue_normalization_contracts import assert_profile_covers


VENUE = VenueId("BINANCE")
ACCOUNT = AccountId(venue_id=VENUE, value=1)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


def test_profile_declares_supported_normalization_entities() -> None:
    profile = VenueNormalizationProfile(
        venue_id=VENUE,
        supported=frozenset(
            {
                NormalizationEntity.INSTRUMENT,
                NormalizationEntity.ORDER,
                NormalizationEntity.POSITION,
                NormalizationEntity.BALANCE,
                NormalizationEntity.FILL,
            }
        ),
    )
    assert_profile_covers(profile, tuple(NormalizationEntity))


def test_empty_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        VenueNormalizationProfile(venue_id=VENUE, supported=frozenset())


def test_position_context_normalizes_time_to_utc() -> None:
    context = PositionNormalizationContext(account_id=ACCOUNT, observed_at=NOW)
    assert context.observed_at == NOW


def test_fill_context_rejects_cross_venue_fallback() -> None:
    other = InstrumentId(
        venue_id=VenueId("BYBIT"),
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )
    with pytest.raises(ValueError, match="venue must match"):
        FillNormalizationContext(
            account_id=ACCOUNT,
            fallback_instrument=other,
            observed_at=NOW,
        )


def test_fill_context_accepts_same_venue_identity() -> None:
    context = FillNormalizationContext(
        account_id=ACCOUNT,
        fallback_instrument=INSTRUMENT,
        observed_at=NOW,
    )
    assert context.fallback_instrument == INSTRUMENT
