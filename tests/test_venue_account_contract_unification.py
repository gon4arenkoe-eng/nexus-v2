"""Single canonical venue account contract regression."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

import apps.core.ports.venue as venue
import apps.core.ports.venue_account as canonical
from packages.contracts.identities import AccountId, VenueId


NOW = datetime(2026, 9, 16, 18, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BYBIT"), 7)


def test_venue_port_reexports_canonical_account_classes() -> None:
    assert venue.VenueBalance is canonical.VenueBalance
    assert venue.VenueAccountState is canonical.VenueAccountState
    assert (
        venue.VenueAccountObservationState
        is canonical.VenueAccountObservationState
    )


def test_balance_asset_is_canonical_and_normalized() -> None:
    balance = venue.VenueBalance(
        asset="usdt",
        total=Decimal("100"),
        available=Decimal("80"),
    )

    assert balance.asset == "USDT"
    assert balance.currency == "USDT"


def test_account_quality_is_explicit_not_defaulted() -> None:
    with pytest.raises(TypeError):
        venue.VenueAccountState(
            account_id=ACCOUNT,
            balances=(),
            observed_at=NOW,
        )


def test_unavailable_account_cannot_carry_balance() -> None:
    with pytest.raises(
        ValueError,
        match="cannot carry balances",
    ):
        venue.VenueAccountState(
            account_id=ACCOUNT,
            state=(
                venue.VenueAccountObservationState
                .UNAVAILABLE
            ),
            observed_at=NOW,
            balances=(
                venue.VenueBalance(
                    asset="USDT",
                    total=Decimal("100"),
                    available=Decimal("80"),
                ),
            ),
        )
