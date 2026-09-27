"""Build canonical Portfolio Risk snapshots from authoritative observations.

This application service is deliberately read-only with respect to venues. It
normalizes already-canonical account/position observations into the existing
PortfolioRiskSnapshot domain contract. Missing valuation inputs fail closed;
entry price is never substituted for mark price.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from apps.core.domain.portfolio_risk import (
    PortfolioExposure,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from apps.core.ports.venue import VenuePosition, VenuePositionSide
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
    VenueAccountState,
)
from packages.contracts.primitives import normalize_utc_datetime


class PortfolioRiskRecordingInputError(ValueError):
    """Required authoritative valuation input is absent or inconsistent."""


def _required_asset(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioRiskRecordingInputError(
            "equity_asset must be non-empty"
        )
    return value.strip().upper()


def _position_group_id(position: VenuePosition) -> str:
    return ":".join(
        (
            "venue-observed",
            str(position.account_id.venue_id),
            str(position.account_id.value),
            position.instrument_id.native_symbol,
            position.side.value,
        )
    )


def _source_observed_at(
    *,
    account_state: VenueAccountState,
    positions: tuple[VenuePosition, ...],
) -> datetime:
    values = [account_state.observed_at]
    values.extend(position.observed_at for position in positions)
    return min(values)


def build_portfolio_risk_snapshot(
    *,
    user_id: int,
    account_state: VenueAccountState,
    positions: tuple[VenuePosition, ...],
    equity_asset: str,
    trading_state: PortfolioRiskState,
    now: datetime,
    stale_after: timedelta,
    previous_snapshot: PortfolioRiskSnapshot | None = None,
) -> PortfolioRiskSnapshot:
    """Build one snapshot or fail closed when valuation is incomplete.

    The current producer scope is intentionally one venue account. Multi-account
    and cross-currency valuation remain a separate canonical capability.
    """

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise PortfolioRiskRecordingInputError(
            "user_id must be a positive integer"
        )
    if not isinstance(account_state, VenueAccountState):
        raise PortfolioRiskRecordingInputError(
            "account_state must be VenueAccountState"
        )
    if not isinstance(positions, tuple) or not all(
        isinstance(position, VenuePosition) for position in positions
    ):
        raise PortfolioRiskRecordingInputError(
            "positions must contain VenuePosition values"
        )
    if not isinstance(trading_state, PortfolioRiskState):
        raise PortfolioRiskRecordingInputError(
            "trading_state must be PortfolioRiskState"
        )
    now = normalize_utc_datetime(now, field_name="now")
    if not isinstance(stale_after, timedelta) or stale_after <= timedelta(0):
        raise PortfolioRiskRecordingInputError(
            "stale_after must be a positive timedelta"
        )
    equity_asset = _required_asset(equity_asset)

    if account_state.state is VenueAccountObservationState.UNAVAILABLE:
        raise PortfolioRiskRecordingInputError(
            "unavailable account observation cannot produce risk snapshot"
        )

    matching_balances = tuple(
        balance
        for balance in account_state.balances
        if balance.asset == equity_asset
    )
    if len(matching_balances) != 1:
        raise PortfolioRiskRecordingInputError(
            "exactly one equity balance is required"
        )
    equity = matching_balances[0].total
    if equity <= Decimal("0"):
        raise PortfolioRiskRecordingInputError(
            "equity balance must be positive"
        )

    exposures: list[PortfolioExposure] = []
    for position in positions:
        if position.account_id != account_state.account_id:
            raise PortfolioRiskRecordingInputError(
                "position account outside producer scope"
            )
        if position.mark_price is None:
            raise PortfolioRiskRecordingInputError(
                "open position mark price is required"
            )
        if position.leverage is None:
            raise PortfolioRiskRecordingInputError(
                "open position leverage is required"
            )

        notional = position.quantity * position.mark_price
        signed_notional = (
            notional
            if position.side is VenuePositionSide.LONG
            else -notional
        )
        exposures.append(
            PortfolioExposure(
                position_group_id=_position_group_id(position),
                account_id=position.account_id,
                instrument_id=position.instrument_id,
                strategy="VENUE_OBSERVED",
                settlement_currency=equity_asset,
                correlation_cluster=position.instrument_id.asset_class.value,
                signed_notional=signed_notional,
                margin_used=notional / position.leverage,
            )
        )

    observed_at = _source_observed_at(
        account_state=account_state,
        positions=positions,
    )
    if observed_at > now:
        raise PortfolioRiskRecordingInputError(
            "source observation cannot be in the future"
        )

    baseline_known = False
    if previous_snapshot is not None:
        if previous_snapshot.user_id != user_id:
            raise PortfolioRiskRecordingInputError(
                "previous snapshot user mismatch"
            )
        if previous_snapshot.observed_at > observed_at:
            raise PortfolioRiskRecordingInputError(
                "previous snapshot is newer than current observation"
            )
        baseline_known = (
            previous_snapshot.observed_at.date() == observed_at.date()
        )

    if baseline_known and previous_snapshot is not None:
        daily_start_equity = previous_snapshot.daily_start_equity
    else:
        daily_start_equity = equity

    rolling_peak_equity = equity
    if previous_snapshot is not None:
        rolling_peak_equity = max(
            previous_snapshot.rolling_peak_equity,
            equity,
        )

    if (
        account_state.state is VenueAccountObservationState.STALE
        or now - observed_at > stale_after
    ):
        observation_state = RiskObservationState.STALE
    elif not baseline_known:
        # The first observation of a UTC day initializes the daily baseline.
        # It is real data, but daily PnL is not yet independently anchored.
        observation_state = RiskObservationState.DEGRADED
    else:
        observation_state = RiskObservationState.CURRENT

    return PortfolioRiskSnapshot(
        user_id=user_id,
        observation_state=observation_state,
        trading_state=trading_state,
        equity=equity,
        daily_start_equity=daily_start_equity,
        rolling_peak_equity=rolling_peak_equity,
        exposures=tuple(exposures),
        observed_at=observed_at,
    )
