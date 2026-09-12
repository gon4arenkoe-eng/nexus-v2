"""Deterministic Portfolio Risk V2 engine."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.portfolio_risk import (
    HedgeTarget,
    PortfolioExposure,
    PortfolioRiskDecision,
    PortfolioRiskDecisionState,
    PortfolioRiskLimits,
    PortfolioRiskReason,
    PortfolioRiskRequest,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from apps.core.ports.portfolio_risk import SingleLegRiskPolicy
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
    VenueId,
)


class PortfolioRiskInputError(ValueError):
    """Portfolio risk input is incomplete or ownership-invalid."""


def _ratio_loss(reference: Decimal, current: Decimal) -> Decimal:
    if current >= reference:
        return Decimal("0")
    return (reference - current) / reference


def _signed_notional(side: TradeSide, notional: Decimal) -> Decimal:
    if side is TradeSide.BUY:
        return notional
    return -notional


def _sum_abs(values: list[Decimal]) -> Decimal:
    return sum((abs(value) for value in values), Decimal("0"))


class PortfolioRiskEngine:
    """Own deterministic portfolio/account/venue risk admission."""

    def __init__(
        self,
        *,
        limits: PortfolioRiskLimits,
        single_leg_policy: SingleLegRiskPolicy,
    ) -> None:
        if not isinstance(limits, PortfolioRiskLimits):
            raise ValueError("limits must be PortfolioRiskLimits")
        self._limits = limits
        self._single_leg_policy = single_leg_policy

    def evaluate(
        self,
        *,
        request: PortfolioRiskRequest,
        snapshot: PortfolioRiskSnapshot,
        hedge_targets: tuple[HedgeTarget, ...] = (),
    ) -> PortfolioRiskDecision:
        if not isinstance(request, PortfolioRiskRequest):
            raise ValueError("request must be PortfolioRiskRequest")
        if not isinstance(snapshot, PortfolioRiskSnapshot):
            raise ValueError("snapshot must be PortfolioRiskSnapshot")
        if request.user_id != snapshot.user_id:
            raise PortfolioRiskInputError(
                "risk request user does not match portfolio snapshot user"
            )
        if not isinstance(hedge_targets, tuple):
            raise ValueError("hedge_targets must be a tuple")
        if not all(
            isinstance(item, HedgeTarget)
            for item in hedge_targets
        ):
            raise ValueError(
                "hedge_targets must contain HedgeTarget values"
            )

        target_map = {item.leg_id: item.weight for item in hedge_targets}
        if len(target_map) != len(hedge_targets):
            raise PortfolioRiskInputError("duplicate hedge target")
        request_leg_ids = {leg.leg_id for leg in request.legs}
        if target_map and set(target_map) != request_leg_ids:
            raise PortfolioRiskInputError(
                "hedge targets must exactly match risk request legs"
            )

        all_reduce_only = all(leg.reduce_only for leg in request.legs)
        reasons: list[PortfolioRiskReason] = []

        if not all_reduce_only:
            if snapshot.observation_state is not RiskObservationState.CURRENT:
                reasons.append(PortfolioRiskReason.RISK_DATA_NOT_CURRENT)
            if snapshot.trading_state is PortfolioRiskState.HALTED:
                reasons.append(PortfolioRiskReason.GLOBAL_KILL_SWITCH)
            elif snapshot.trading_state is PortfolioRiskState.REDUCING:
                reasons.append(PortfolioRiskReason.REDUCING_ONLY)

        current_positions = list(snapshot.exposures)
        projected: list[PortfolioExposure] = list(current_positions)
        proposed_signed_notionals: dict[str, Decimal] = {}
        proposed_margin = Decimal("0")

        for candidate in request.legs:
            notional = candidate.quantity * candidate.mark_price
            proposed_signed_notionals[candidate.leg_id] = _signed_notional(
                candidate.side,
                notional,
            )

            if candidate.reduce_only:
                continue

            leg_decision = self._single_leg_policy.evaluate(
                candidate=candidate,
                portfolio=snapshot,
            )
            if not leg_decision.approved:
                reasons.append(PortfolioRiskReason.SINGLE_LEG_POLICY)

            if candidate.leverage > self._limits.max_leverage:
                reasons.append(PortfolioRiskReason.LEVERAGE)

            if (
                notional / candidate.available_liquidity_notional
                > self._limits.max_order_liquidity_ratio
            ):
                reasons.append(PortfolioRiskReason.LIQUIDITY_CAPACITY)

            if (
                candidate.expected_slippage_bps
                > self._limits.max_expected_slippage_bps
            ):
                reasons.append(PortfolioRiskReason.SLIPPAGE)

            proposed_margin += notional / candidate.leverage
            projected.append(
                PortfolioExposure(
                    position_group_id=f"candidate:{request.intent_id}",
                    account_id=candidate.account_id,
                    instrument_id=candidate.instrument_id,
                    strategy=request.strategy,
                    settlement_currency=candidate.settlement_currency,
                    correlation_cluster=candidate.correlation_cluster,
                    signed_notional=proposed_signed_notionals[
                        candidate.leg_id
                    ],
                    margin_used=notional / candidate.leverage,
                )
            )

        projected_gross = _sum_abs(
            [item.signed_notional for item in projected]
        )
        projected_net = abs(
            sum(
                (item.signed_notional for item in projected),
                Decimal("0"),
            )
        )
        projected_leverage = projected_gross / snapshot.equity
        projected_margin = (
            sum(
                (item.margin_used for item in current_positions),
                Decimal("0"),
            )
            + proposed_margin
        )
        projected_margin_utilization = projected_margin / snapshot.equity

        if not all_reduce_only:
            self._apply_portfolio_limits(
                projected=projected,
                projected_gross=projected_gross,
                projected_net=projected_net,
                projected_leverage=projected_leverage,
                projected_margin_utilization=projected_margin_utilization,
                snapshot=snapshot,
                request=request,
                proposed_signed_notionals=proposed_signed_notionals,
                target_map=target_map,
                reasons=reasons,
            )

        ordered_reasons = tuple(
            sorted(set(reasons), key=lambda item: item.value)
        )
        state = (
            PortfolioRiskDecisionState.BLOCKED
            if ordered_reasons
            else PortfolioRiskDecisionState.APPROVED
        )

        return PortfolioRiskDecision(
            state=state,
            reasons=ordered_reasons,
            projected_gross_exposure=projected_gross,
            projected_net_exposure=projected_net,
            projected_leverage=projected_leverage,
            projected_margin_utilization=projected_margin_utilization,
        )

    def _apply_portfolio_limits(
        self,
        *,
        projected: list[PortfolioExposure],
        projected_gross: Decimal,
        projected_net: Decimal,
        projected_leverage: Decimal,
        projected_margin_utilization: Decimal,
        snapshot: PortfolioRiskSnapshot,
        request: PortfolioRiskRequest,
        proposed_signed_notionals: dict[str, Decimal],
        target_map: dict[str, Decimal],
        reasons: list[PortfolioRiskReason],
    ) -> None:
        groups = {
            item.position_group_id
            for item in snapshot.exposures
        }
        groups.add(f"candidate:{request.intent_id}")
        if len(groups) > self._limits.max_open_position_groups:
            reasons.append(PortfolioRiskReason.MAX_POSITION_GROUPS)

        if projected_gross > self._limits.max_gross_exposure:
            reasons.append(PortfolioRiskReason.GROSS_EXPOSURE)
        if projected_net > self._limits.max_net_exposure:
            reasons.append(PortfolioRiskReason.NET_EXPOSURE)
        if projected_leverage > self._limits.max_leverage:
            reasons.append(PortfolioRiskReason.LEVERAGE)
        if (
            projected_margin_utilization
            > self._limits.max_margin_utilization
        ):
            reasons.append(PortfolioRiskReason.MARGIN_UTILIZATION)

        daily_drawdown = _ratio_loss(
            snapshot.daily_start_equity,
            snapshot.equity,
        )
        rolling_drawdown = _ratio_loss(
            snapshot.rolling_peak_equity,
            snapshot.equity,
        )
        if daily_drawdown >= self._limits.max_daily_drawdown:
            reasons.append(PortfolioRiskReason.DAILY_DRAWDOWN)
        if rolling_drawdown >= self._limits.max_rolling_drawdown:
            reasons.append(PortfolioRiskReason.ROLLING_DRAWDOWN)

        account: defaultdict[AccountId, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        venue: defaultdict[VenueId, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        strategy: defaultdict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        instrument: defaultdict[InstrumentId, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        currency: defaultdict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        cluster: defaultdict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )

        for item in projected:
            absolute = abs(item.signed_notional)
            account[item.account_id] += absolute
            venue[item.account_id.venue_id] += absolute
            strategy[item.strategy] += absolute
            instrument[item.instrument_id] += absolute
            currency[item.settlement_currency] += absolute
            cluster[item.correlation_cluster] += absolute

        if any(
            value > self._limits.max_account_exposure
            for value in account.values()
        ):
            reasons.append(PortfolioRiskReason.ACCOUNT_EXPOSURE)
        if any(
            value > self._limits.max_venue_exposure
            for value in venue.values()
        ):
            reasons.append(PortfolioRiskReason.VENUE_EXPOSURE)
        if any(
            value > self._limits.max_strategy_exposure
            for value in strategy.values()
        ):
            reasons.append(PortfolioRiskReason.STRATEGY_EXPOSURE)
        if any(
            value > self._limits.max_instrument_exposure
            for value in instrument.values()
        ):
            reasons.append(PortfolioRiskReason.INSTRUMENT_EXPOSURE)
        if any(
            value > self._limits.max_correlation_cluster_exposure
            for value in cluster.values()
        ):
            reasons.append(PortfolioRiskReason.CORRELATION_CLUSTER)

        if projected_gross > 0 and any(
            value / projected_gross
            > self._limits.max_currency_concentration
            for value in currency.values()
        ):
            reasons.append(PortfolioRiskReason.CURRENCY_CONCENTRATION)

        if request.shape is not TradeIntentShape.SINGLE_LEG:
            if not target_map or not self._hedge_is_intact(
                proposed_signed_notionals=proposed_signed_notionals,
                target_map=target_map,
            ):
                reasons.append(PortfolioRiskReason.HEDGE_INTEGRITY)

    def _hedge_is_intact(
        self,
        *,
        proposed_signed_notionals: dict[str, Decimal],
        target_map: dict[str, Decimal],
    ) -> bool:
        normalized = [
            proposed_signed_notionals[leg_id] / target
            for leg_id, target in target_map.items()
        ]
        anchor = normalized[0]
        if anchor <= 0:
            return False

        return all(
            abs(value - anchor) / anchor
            <= self._limits.hedge_tolerance
            for value in normalized[1:]
        )
