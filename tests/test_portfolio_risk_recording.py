from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.core.application.portfolio_risk_recording import (
    PortfolioRiskRecordingInputError,
    build_portfolio_risk_snapshot,
)
from apps.core.domain.portfolio_risk import (
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from apps.core.ports.venue import VenuePosition, VenuePositionSide
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
    VenueAccountState,
    VenueBalance,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)

NOW = datetime(2026, 9, 27, 20, 0, tzinfo=UTC)
VENUE = VenueId("BINGX")
ACCOUNT = AccountId(venue_id=VENUE, value=7)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _account(
    *,
    total: str = "100000",
    state: VenueAccountObservationState = VenueAccountObservationState.CURRENT,
    observed_at: datetime = NOW,
) -> VenueAccountState:
    return VenueAccountState(
        account_id=ACCOUNT,
        state=state,
        observed_at=observed_at,
        balances=(
            VenueBalance(
                asset="VST",
                total=Decimal(total),
                available=Decimal("90000"),
            ),
        ),
    )


def _position(
    *,
    side: VenuePositionSide = VenuePositionSide.LONG,
    mark_price: Decimal | None = Decimal("62000"),
    leverage: Decimal | None = Decimal("10"),
    observed_at: datetime = NOW,
) -> VenuePosition:
    return VenuePosition(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=side,
        quantity=Decimal("0.5"),
        entry_price=Decimal("60000"),
        observed_at=observed_at,
        mark_price=mark_price,
        leverage=leverage,
    )


def test_first_real_observation_builds_degraded_snapshot_without_fake_values() -> None:
    snapshot = build_portfolio_risk_snapshot(
        user_id=7,
        account_state=_account(),
        positions=(_position(),),
        equity_asset="VST",
        trading_state=PortfolioRiskState.HALTED,
        now=NOW,
        stale_after=timedelta(seconds=90),
    )

    assert snapshot.observation_state is RiskObservationState.DEGRADED
    assert snapshot.trading_state is PortfolioRiskState.HALTED
    assert snapshot.equity == Decimal("100000")
    assert snapshot.daily_start_equity == Decimal("100000")
    assert snapshot.rolling_peak_equity == Decimal("100000")
    assert len(snapshot.exposures) == 1
    exposure = snapshot.exposures[0]
    assert exposure.signed_notional == Decimal("31000.0")
    assert exposure.margin_used == Decimal("3100.0")
    assert exposure.strategy == "VENUE_OBSERVED"
    assert exposure.settlement_currency == "VST"
    assert exposure.correlation_cluster == "CRYPTO"


def test_second_same_day_observation_preserves_daily_baseline_and_becomes_current() -> None:
    previous = PortfolioRiskSnapshot(
        user_id=7,
        observation_state=RiskObservationState.DEGRADED,
        trading_state=PortfolioRiskState.HALTED,
        equity=Decimal("100000"),
        daily_start_equity=Decimal("100000"),
        rolling_peak_equity=Decimal("100000"),
        exposures=(),
        observed_at=NOW - timedelta(minutes=1),
    )
    snapshot = build_portfolio_risk_snapshot(
        user_id=7,
        account_state=_account(total="101000"),
        positions=(_position(),),
        equity_asset="VST",
        trading_state=PortfolioRiskState.HALTED,
        now=NOW,
        stale_after=timedelta(seconds=90),
        previous_snapshot=previous,
    )

    assert snapshot.observation_state is RiskObservationState.CURRENT
    assert snapshot.equity == Decimal("101000")
    assert snapshot.daily_start_equity == Decimal("100000")
    assert snapshot.rolling_peak_equity == Decimal("101000")


def test_stale_source_remains_explicit_stale() -> None:
    old = NOW - timedelta(minutes=5)
    snapshot = build_portfolio_risk_snapshot(
        user_id=7,
        account_state=_account(observed_at=old),
        positions=(_position(observed_at=old),),
        equity_asset="VST",
        trading_state=PortfolioRiskState.HALTED,
        now=NOW,
        stale_after=timedelta(seconds=90),
    )
    assert snapshot.observation_state is RiskObservationState.STALE


def test_missing_mark_or_leverage_fails_closed() -> None:
    with pytest.raises(PortfolioRiskRecordingInputError, match="mark price"):
        build_portfolio_risk_snapshot(
            user_id=7,
            account_state=_account(),
            positions=(_position(mark_price=None),),
            equity_asset="VST",
            trading_state=PortfolioRiskState.HALTED,
            now=NOW,
            stale_after=timedelta(seconds=90),
        )

    with pytest.raises(PortfolioRiskRecordingInputError, match="leverage"):
        build_portfolio_risk_snapshot(
            user_id=7,
            account_state=_account(),
            positions=(_position(leverage=None),),
            equity_asset="VST",
            trading_state=PortfolioRiskState.HALTED,
            now=NOW,
            stale_after=timedelta(seconds=90),
        )


def test_missing_equity_asset_fails_closed() -> None:
    with pytest.raises(
        PortfolioRiskRecordingInputError,
        match="exactly one equity balance",
    ):
        build_portfolio_risk_snapshot(
            user_id=7,
            account_state=_account(),
            positions=(),
            equity_asset="USDT",
            trading_state=PortfolioRiskState.HALTED,
            now=NOW,
            stale_after=timedelta(seconds=90),
        )
