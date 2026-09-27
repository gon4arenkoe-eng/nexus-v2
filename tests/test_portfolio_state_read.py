from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from apps.core.application.portfolio_state_read import project_portfolio_state
from apps.core.domain.portfolio_risk import (
    PortfolioExposure,
    PortfolioRiskLimits,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)

NOW = datetime(2026, 9, 27, 19, 0, tzinfo=UTC)


def _exposure(*, group: str, symbol: str, notional: str, margin: str) -> PortfolioExposure:
    venue = VenueId("BINGX")
    return PortfolioExposure(
        position_group_id=group,
        account_id=AccountId(venue_id=venue, value=7),
        instrument_id=InstrumentId(
            venue_id=venue,
            native_symbol=symbol,
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        ),
        strategy="trend",
        settlement_currency="USDT",
        correlation_cluster="CRYPTO-MAJOR",
        signed_notional=Decimal(notional),
        margin_used=Decimal(margin),
    )


def _limits() -> PortfolioRiskLimits:
    return PortfolioRiskLimits(
        max_open_position_groups=10,
        max_gross_exposure=Decimal("20000"),
        max_net_exposure=Decimal("10000"),
        max_account_exposure=Decimal("15000"),
        max_venue_exposure=Decimal("18000"),
        max_strategy_exposure=Decimal("12000"),
        max_instrument_exposure=Decimal("10000"),
        max_currency_concentration=Decimal("1"),
        max_correlation_cluster_exposure=Decimal("18000"),
        max_leverage=Decimal("2"),
        max_margin_utilization=Decimal("0.5"),
        max_daily_drawdown=Decimal("0.10"),
        max_rolling_drawdown=Decimal("0.20"),
        max_order_liquidity_ratio=Decimal("0.10"),
        max_expected_slippage_bps=Decimal("25"),
    )


def test_projection_derives_portfolio_and_risk_metrics_from_canonical_snapshot() -> None:
    snapshot = PortfolioRiskSnapshot(
        user_id=7,
        observation_state=RiskObservationState.CURRENT,
        trading_state=PortfolioRiskState.ACTIVE,
        equity=Decimal("9000"),
        daily_start_equity=Decimal("10000"),
        rolling_peak_equity=Decimal("12000"),
        exposures=(
            _exposure(group="g-1", symbol="BTC-USDT", notional="8000", margin="1000"),
            _exposure(group="g-2", symbol="ETH-USDT", notional="-3000", margin="500"),
        ),
        observed_at=NOW,
    )

    value = project_portfolio_state(snapshot=snapshot, limits=_limits())

    assert value.equity == Decimal("9000")
    assert value.daily_pnl == Decimal("-1000")
    assert value.daily_pnl_ratio == Decimal("-0.1")
    assert value.daily_drawdown_ratio == Decimal("0.1")
    assert value.rolling_drawdown_ratio == Decimal("0.25")
    assert value.gross_exposure == Decimal("11000")
    assert value.net_exposure == Decimal("5000")
    assert value.margin_used == Decimal("1500")
    assert value.leverage == Decimal("11000") / Decimal("9000")
    assert value.margin_utilization == Decimal("1500") / Decimal("9000")
    assert value.gross_exposure_utilization == Decimal("0.55")
    assert value.net_exposure_utilization == Decimal("0.5")
    assert value.leverage_utilization == (Decimal("11000") / Decimal("9000")) / Decimal("2")
    assert value.daily_drawdown_utilization == Decimal("1")
    assert value.rolling_drawdown_utilization == Decimal("1.25")
    assert value.headline_risk_utilization == Decimal("1.25")


def test_projection_preserves_non_current_state_and_zero_drawdown() -> None:
    snapshot = PortfolioRiskSnapshot(
        user_id=7,
        observation_state=RiskObservationState.STALE,
        trading_state=PortfolioRiskState.REDUCING,
        equity=Decimal("11000"),
        daily_start_equity=Decimal("10000"),
        rolling_peak_equity=Decimal("11000"),
        exposures=(),
        observed_at=NOW,
    )

    value = project_portfolio_state(snapshot=snapshot, limits=_limits())

    assert value.observation_state == "STALE"
    assert value.trading_state == "REDUCING"
    assert value.daily_pnl == Decimal("1000")
    assert value.daily_drawdown_ratio == Decimal("0")
    assert value.rolling_drawdown_ratio == Decimal("0")
    assert value.gross_exposure == Decimal("0")
    assert value.net_exposure == Decimal("0")
    assert value.headline_risk_utilization == Decimal("0")
