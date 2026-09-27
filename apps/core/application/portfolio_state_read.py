"""Deterministic read projection over canonical Portfolio Risk snapshots.

The projection is presentation/read-only state. It does not mutate risk state,
place orders, or infer missing valuation inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.core.domain.portfolio_risk import (
    PortfolioRiskLimits,
    PortfolioRiskSnapshot,
)


_ZERO = Decimal("0")
_ONE = Decimal("1")


def _loss_ratio(reference: Decimal, current: Decimal) -> Decimal:
    if current >= reference:
        return _ZERO
    return (reference - current) / reference


def _utilization(value: Decimal, limit: Decimal) -> Decimal:
    if limit > _ZERO:
        return value / limit
    return _ZERO if value == _ZERO else _ONE


@dataclass(frozen=True, slots=True)
class PortfolioStateReadModel:
    user_id: int
    observation_state: str
    trading_state: str
    equity: Decimal
    daily_start_equity: Decimal
    rolling_peak_equity: Decimal
    daily_pnl: Decimal
    daily_pnl_ratio: Decimal
    daily_drawdown_ratio: Decimal
    rolling_drawdown_ratio: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    margin_used: Decimal
    leverage: Decimal
    margin_utilization: Decimal
    headline_risk_utilization: Decimal
    gross_exposure_utilization: Decimal
    net_exposure_utilization: Decimal
    leverage_utilization: Decimal
    margin_limit_utilization: Decimal
    daily_drawdown_utilization: Decimal
    rolling_drawdown_utilization: Decimal
    observed_at: datetime


def project_portfolio_state(
    *,
    snapshot: PortfolioRiskSnapshot,
    limits: PortfolioRiskLimits,
) -> PortfolioStateReadModel:
    """Project one canonical risk snapshot without inventing missing inputs."""

    signed_notionals = tuple(
        item.signed_notional for item in snapshot.exposures
    )
    gross_exposure = sum(
        (abs(value) for value in signed_notionals),
        _ZERO,
    )
    net_exposure = abs(sum(signed_notionals, _ZERO))
    margin_used = sum(
        (item.margin_used for item in snapshot.exposures),
        _ZERO,
    )
    leverage = gross_exposure / snapshot.equity
    margin_utilization = margin_used / snapshot.equity
    daily_pnl = snapshot.equity - snapshot.daily_start_equity
    daily_pnl_ratio = daily_pnl / snapshot.daily_start_equity
    daily_drawdown_ratio = _loss_ratio(
        snapshot.daily_start_equity,
        snapshot.equity,
    )
    rolling_drawdown_ratio = _loss_ratio(
        snapshot.rolling_peak_equity,
        snapshot.equity,
    )

    gross_exposure_utilization = _utilization(
        gross_exposure,
        limits.max_gross_exposure,
    )
    net_exposure_utilization = _utilization(
        net_exposure,
        limits.max_net_exposure,
    )
    leverage_utilization = _utilization(
        leverage,
        limits.max_leverage,
    )
    margin_limit_utilization = _utilization(
        margin_utilization,
        limits.max_margin_utilization,
    )
    daily_drawdown_utilization = _utilization(
        daily_drawdown_ratio,
        limits.max_daily_drawdown,
    )
    rolling_drawdown_utilization = _utilization(
        rolling_drawdown_ratio,
        limits.max_rolling_drawdown,
    )
    headline_risk_utilization = max(
        gross_exposure_utilization,
        net_exposure_utilization,
        leverage_utilization,
        margin_limit_utilization,
        daily_drawdown_utilization,
        rolling_drawdown_utilization,
    )

    return PortfolioStateReadModel(
        user_id=snapshot.user_id,
        observation_state=snapshot.observation_state.value,
        trading_state=snapshot.trading_state.value,
        equity=snapshot.equity,
        daily_start_equity=snapshot.daily_start_equity,
        rolling_peak_equity=snapshot.rolling_peak_equity,
        daily_pnl=daily_pnl,
        daily_pnl_ratio=daily_pnl_ratio,
        daily_drawdown_ratio=daily_drawdown_ratio,
        rolling_drawdown_ratio=rolling_drawdown_ratio,
        gross_exposure=gross_exposure,
        net_exposure=net_exposure,
        margin_used=margin_used,
        leverage=leverage,
        margin_utilization=margin_utilization,
        headline_risk_utilization=headline_risk_utilization,
        gross_exposure_utilization=gross_exposure_utilization,
        net_exposure_utilization=net_exposure_utilization,
        leverage_utilization=leverage_utilization,
        margin_limit_utilization=margin_limit_utilization,
        daily_drawdown_utilization=daily_drawdown_utilization,
        rolling_drawdown_utilization=rolling_drawdown_utilization,
        observed_at=snapshot.observed_at,
    )
