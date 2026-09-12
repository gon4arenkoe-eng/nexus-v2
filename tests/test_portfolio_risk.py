"""Phase 6 Portfolio Risk V2 deterministic policy tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.application.portfolio_risk import (
    PortfolioRiskEngine,
    PortfolioRiskInputError,
)
from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.portfolio_risk import (
    HedgeTarget,
    PortfolioExposure,
    PortfolioRiskDecisionState,
    PortfolioRiskLimits,
    PortfolioRiskReason,
    PortfolioRiskRequest,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskLegCandidate,
    RiskObservationState,
)
from apps.core.ports.portfolio_risk import SingleLegRiskDecision
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


NOW = datetime(2026, 9, 12, 17, 0, tzinfo=UTC)


def _account(value: int = 1, venue: str = "BINANCE") -> AccountId:
    return AccountId(venue_id=VenueId(venue), value=value)


def _instrument(
    symbol: str = "BTCUSDT",
    venue: str = "BINANCE",
) -> InstrumentId:
    return InstrumentId(
        venue_id=VenueId(venue),
        native_symbol=symbol,
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _candidate(
    *,
    leg_id: str = "leg-1",
    symbol: str = "BTCUSDT",
    venue: str = "BINANCE",
    account_value: int = 1,
    side: TradeSide = TradeSide.BUY,
    quantity: str = "1",
    reduce_only: bool = False,
    price: str = "1000",
    currency: str = "USDT",
    cluster: str = "CRYPTO-MAJOR",
    liquidity: str = "100000",
    slippage_bps: str = "5",
    leverage: str = "2",
) -> RiskLegCandidate:
    return RiskLegCandidate(
        leg_id=leg_id,
        account_id=_account(account_value, venue),
        instrument_id=_instrument(symbol, venue),
        side=side,
        quantity=Decimal(quantity),
        reduce_only=reduce_only,
        mark_price=Decimal(price),
        settlement_currency=currency,
        correlation_cluster=cluster,
        available_liquidity_notional=Decimal(liquidity),
        expected_slippage_bps=Decimal(slippage_bps),
        leverage=Decimal(leverage),
    )


def _request(
    *,
    shape: TradeIntentShape = TradeIntentShape.SINGLE_LEG,
    legs: tuple[RiskLegCandidate, ...] | None = None,
    strategy: str = "trend",
    user_id: int = 7,
) -> PortfolioRiskRequest:
    if legs is None:
        legs = (_candidate(),)
    return PortfolioRiskRequest(
        intent_id="intent-1",
        user_id=user_id,
        shape=shape,
        strategy=strategy,
        legs=legs,
    )


def _exposure(
    *,
    group: str = "group-1",
    symbol: str = "ETHUSDT",
    account_value: int = 1,
    venue: str = "BINANCE",
    strategy: str = "mean-reversion",
    currency: str = "USDT",
    cluster: str = "CRYPTO-MAJOR",
    signed_notional: str = "500",
    margin_used: str = "100",
) -> PortfolioExposure:
    return PortfolioExposure(
        position_group_id=group,
        account_id=_account(account_value, venue),
        instrument_id=_instrument(symbol, venue),
        strategy=strategy,
        settlement_currency=currency,
        correlation_cluster=cluster,
        signed_notional=Decimal(signed_notional),
        margin_used=Decimal(margin_used),
    )


def _snapshot(
    *,
    exposures: tuple[PortfolioExposure, ...] = (),
    state: PortfolioRiskState = PortfolioRiskState.ACTIVE,
    observation: RiskObservationState = RiskObservationState.CURRENT,
    equity: str = "10000",
    daily_start: str = "10000",
    rolling_peak: str = "10000",
    user_id: int = 7,
) -> PortfolioRiskSnapshot:
    return PortfolioRiskSnapshot(
        user_id=user_id,
        observation_state=observation,
        trading_state=state,
        equity=Decimal(equity),
        daily_start_equity=Decimal(daily_start),
        rolling_peak_equity=Decimal(rolling_peak),
        exposures=exposures,
        observed_at=NOW,
    )


def _limits(**changes) -> PortfolioRiskLimits:
    values = {
        "max_open_position_groups": 10,
        "max_gross_exposure": Decimal("20000"),
        "max_net_exposure": Decimal("15000"),
        "max_account_exposure": Decimal("10000"),
        "max_venue_exposure": Decimal("15000"),
        "max_strategy_exposure": Decimal("10000"),
        "max_instrument_exposure": Decimal("6000"),
        "max_currency_concentration": Decimal("1"),
        "max_correlation_cluster_exposure": Decimal("12000"),
        "max_leverage": Decimal("5"),
        "max_margin_utilization": Decimal("0.8"),
        "max_daily_drawdown": Decimal("0.05"),
        "max_rolling_drawdown": Decimal("0.10"),
        "max_order_liquidity_ratio": Decimal("0.10"),
        "max_expected_slippage_bps": Decimal("25"),
        "hedge_tolerance": Decimal("0.05"),
    }
    values.update(changes)
    return PortfolioRiskLimits(**values)


class RecordingSingleLegPolicy:
    def __init__(self, approved: bool = True) -> None:
        self.approved = approved
        self.calls: list[str] = []

    def evaluate(self, *, candidate, portfolio):
        self.calls.append(candidate.leg_id)
        if self.approved:
            return SingleLegRiskDecision(approved=True)
        return SingleLegRiskDecision(
            approved=False,
            reason="legacy single-leg policy rejected",
        )


def _engine(
    *,
    limits: PortfolioRiskLimits | None = None,
    policy: RecordingSingleLegPolicy | None = None,
) -> tuple[PortfolioRiskEngine, RecordingSingleLegPolicy]:
    if policy is None:
        policy = RecordingSingleLegPolicy()
    if limits is None:
        limits = _limits()
    return (
        PortfolioRiskEngine(
            limits=limits,
            single_leg_policy=policy,
        ),
        policy,
    )


def _reasons(decision) -> set[PortfolioRiskReason]:
    return set(decision.reasons)


def test_healthy_single_leg_is_approved_and_policy_runs() -> None:
    engine, policy = _engine()
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(),
    )

    assert decision.state is PortfolioRiskDecisionState.APPROVED
    assert decision.reasons == ()
    assert policy.calls == ["leg-1"]
    assert decision.projected_gross_exposure == Decimal("1000")
    assert decision.projected_net_exposure == Decimal("1000")
    assert decision.projected_leverage == Decimal("0.1")
    assert decision.projected_margin_utilization == Decimal("0.05")


@pytest.mark.parametrize(
    "observation",
    [
        RiskObservationState.STALE,
        RiskObservationState.DEGRADED,
        RiskObservationState.UNAVAILABLE,
        RiskObservationState.UNKNOWN,
    ],
)
def test_non_current_risk_data_blocks_new_exposure(observation) -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(observation=observation),
    )

    assert decision.state is PortfolioRiskDecisionState.BLOCKED
    assert PortfolioRiskReason.RISK_DATA_NOT_CURRENT in _reasons(decision)


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (
            PortfolioRiskState.HALTED,
            PortfolioRiskReason.GLOBAL_KILL_SWITCH,
        ),
        (
            PortfolioRiskState.REDUCING,
            PortfolioRiskReason.REDUCING_ONLY,
        ),
    ],
)
def test_trading_state_blocks_new_exposure(state, reason) -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(state=state),
    )
    assert reason in _reasons(decision)


def test_reduce_only_remains_allowed_when_halted_and_stale() -> None:
    engine, policy = _engine()
    decision = engine.evaluate(
        request=_request(legs=(_candidate(reduce_only=True),)),
        snapshot=_snapshot(
            state=PortfolioRiskState.HALTED,
            observation=RiskObservationState.STALE,
            equity="8000",
            daily_start="10000",
            rolling_peak="12000",
        ),
    )

    assert decision.state is PortfolioRiskDecisionState.APPROVED
    assert policy.calls == []


def test_single_leg_policy_rejection_is_portfolio_block() -> None:
    policy = RecordingSingleLegPolicy(approved=False)
    engine, _ = _engine(policy=policy)
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(),
    )
    assert PortfolioRiskReason.SINGLE_LEG_POLICY in _reasons(decision)


def test_max_position_groups_is_enforced() -> None:
    snapshot = _snapshot(
        exposures=(
            _exposure(group="group-1"),
            _exposure(group="group-2", symbol="SOLUSDT"),
        )
    )
    engine, _ = _engine(limits=_limits(max_open_position_groups=2))
    decision = engine.evaluate(
        request=_request(),
        snapshot=snapshot,
    )
    assert PortfolioRiskReason.MAX_POSITION_GROUPS in _reasons(decision)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        (
            "max_gross_exposure",
            Decimal("900"),
            PortfolioRiskReason.GROSS_EXPOSURE,
        ),
        (
            "max_net_exposure",
            Decimal("900"),
            PortfolioRiskReason.NET_EXPOSURE,
        ),
        (
            "max_account_exposure",
            Decimal("900"),
            PortfolioRiskReason.ACCOUNT_EXPOSURE,
        ),
        (
            "max_venue_exposure",
            Decimal("900"),
            PortfolioRiskReason.VENUE_EXPOSURE,
        ),
        (
            "max_strategy_exposure",
            Decimal("900"),
            PortfolioRiskReason.STRATEGY_EXPOSURE,
        ),
        (
            "max_instrument_exposure",
            Decimal("900"),
            PortfolioRiskReason.INSTRUMENT_EXPOSURE,
        ),
        (
            "max_correlation_cluster_exposure",
            Decimal("900"),
            PortfolioRiskReason.CORRELATION_CLUSTER,
        ),
    ],
)
def test_absolute_exposure_limits_are_enforced(field, value, reason) -> None:
    engine, _ = _engine(limits=_limits(**{field: value}))
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(),
    )
    assert reason in _reasons(decision)


def test_account_and_venue_limits_include_existing_positions() -> None:
    snapshot = _snapshot(exposures=(_exposure(signed_notional="700"),))
    engine, _ = _engine(
        limits=_limits(
            max_account_exposure=Decimal("1500"),
            max_venue_exposure=Decimal("1500"),
        )
    )
    decision = engine.evaluate(
        request=_request(),
        snapshot=snapshot,
    )
    assert PortfolioRiskReason.ACCOUNT_EXPOSURE in _reasons(decision)
    assert PortfolioRiskReason.VENUE_EXPOSURE in _reasons(decision)


def test_currency_concentration_is_enforced() -> None:
    snapshot = _snapshot(
        exposures=(
            _exposure(
                currency="USD",
                cluster="EQUITY",
                signed_notional="1000",
            ),
        )
    )
    engine, _ = _engine(
        limits=_limits(max_currency_concentration=Decimal("0.40"))
    )
    decision = engine.evaluate(
        request=_request(),
        snapshot=snapshot,
    )
    assert PortfolioRiskReason.CURRENCY_CONCENTRATION in _reasons(decision)


def test_leg_and_portfolio_leverage_limits_are_enforced() -> None:
    engine, _ = _engine(limits=_limits(max_leverage=Decimal("2")))
    decision = engine.evaluate(
        request=_request(legs=(_candidate(leverage="3"),)),
        snapshot=_snapshot(equity="200"),
    )
    assert PortfolioRiskReason.LEVERAGE in _reasons(decision)


def test_margin_utilization_is_enforced() -> None:
    engine, _ = _engine(
        limits=_limits(max_margin_utilization=Decimal("0.04"))
    )
    decision = engine.evaluate(
        request=_request(legs=(_candidate(leverage="2"),)),
        snapshot=_snapshot(),
    )
    assert PortfolioRiskReason.MARGIN_UTILIZATION in _reasons(decision)


@pytest.mark.parametrize(
    ("daily_start", "rolling_peak", "reason"),
    [
        ("10000", "9500", PortfolioRiskReason.DAILY_DRAWDOWN),
        ("9000", "10000", PortfolioRiskReason.ROLLING_DRAWDOWN),
    ],
)
def test_drawdown_circuit_breakers(daily_start, rolling_peak, reason) -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(
            equity="9000",
            daily_start=daily_start,
            rolling_peak=rolling_peak,
        ),
    )
    assert reason in _reasons(decision)


def test_liquidity_capacity_is_enforced() -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_request(legs=(_candidate(liquidity="5000"),)),
        snapshot=_snapshot(),
    )
    assert PortfolioRiskReason.LIQUIDITY_CAPACITY in _reasons(decision)


def test_expected_slippage_is_enforced() -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_request(legs=(_candidate(slippage_bps="30"),)),
        snapshot=_snapshot(),
    )
    assert PortfolioRiskReason.SLIPPAGE in _reasons(decision)


def _pair_request() -> PortfolioRiskRequest:
    return _request(
        shape=TradeIntentShape.PAIR,
        legs=(
            _candidate(
                leg_id="long",
                symbol="BTCUSDT",
                side=TradeSide.BUY,
                quantity="1",
                price="1000",
            ),
            _candidate(
                leg_id="short",
                symbol="ETHUSDT",
                side=TradeSide.SELL,
                quantity="2",
                price="500",
            ),
        ),
    )


def test_pair_hedge_integrity_accepts_matching_signed_weights() -> None:
    engine, policy = _engine()
    decision = engine.evaluate(
        request=_pair_request(),
        snapshot=_snapshot(),
        hedge_targets=(
            HedgeTarget("long", Decimal("1")),
            HedgeTarget("short", Decimal("-1")),
        ),
    )

    assert decision.state is PortfolioRiskDecisionState.APPROVED
    assert policy.calls == ["long", "short"]


def test_pair_hedge_integrity_blocks_ratio_drift() -> None:
    request = _pair_request()
    drifted = PortfolioRiskRequest(
        intent_id=request.intent_id,
        user_id=request.user_id,
        shape=request.shape,
        strategy=request.strategy,
        legs=(
            request.legs[0],
            _candidate(
                leg_id="short",
                symbol="ETHUSDT",
                side=TradeSide.SELL,
                quantity="2",
                price="400",
            ),
        ),
    )
    engine, _ = _engine()
    decision = engine.evaluate(
        request=drifted,
        snapshot=_snapshot(),
        hedge_targets=(
            HedgeTarget("long", Decimal("1")),
            HedgeTarget("short", Decimal("-1")),
        ),
    )
    assert PortfolioRiskReason.HEDGE_INTEGRITY in _reasons(decision)


def test_pair_hedge_integrity_blocks_wrong_direction() -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_pair_request(),
        snapshot=_snapshot(),
        hedge_targets=(
            HedgeTarget("long", Decimal("1")),
            HedgeTarget("short", Decimal("1")),
        ),
    )
    assert PortfolioRiskReason.HEDGE_INTEGRITY in _reasons(decision)


def test_multi_leg_new_exposure_requires_explicit_hedge_targets() -> None:
    engine, _ = _engine()
    decision = engine.evaluate(
        request=_pair_request(),
        snapshot=_snapshot(),
    )
    assert PortfolioRiskReason.HEDGE_INTEGRITY in _reasons(decision)


def test_user_ownership_mismatch_fails_closed() -> None:
    engine, _ = _engine()
    with pytest.raises(PortfolioRiskInputError):
        engine.evaluate(
            request=_request(user_id=8),
            snapshot=_snapshot(user_id=7),
        )


def test_hedge_targets_must_exactly_match_multi_leg_request() -> None:
    engine, _ = _engine()
    with pytest.raises(PortfolioRiskInputError):
        engine.evaluate(
            request=_pair_request(),
            snapshot=_snapshot(),
            hedge_targets=(HedgeTarget("long", Decimal("1")),),
        )


def test_reasons_are_unique_and_deterministic() -> None:
    engine, _ = _engine(
        limits=_limits(
            max_gross_exposure=Decimal("500"),
            max_net_exposure=Decimal("500"),
            max_account_exposure=Decimal("500"),
        )
    )
    first = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(),
    )
    second = engine.evaluate(
        request=_request(),
        snapshot=_snapshot(),
    )

    assert first == second
    assert first.reasons == tuple(
        sorted(first.reasons, key=lambda item: item.value)
    )
    assert len(first.reasons) == len(set(first.reasons))


def test_limits_and_contracts_fail_closed_on_invalid_values() -> None:
    with pytest.raises(ValueError):
        _limits(max_open_position_groups=0)
    with pytest.raises(ValueError):
        _limits(max_margin_utilization=Decimal("1.1"))
    with pytest.raises(ValueError):
        HedgeTarget("leg-1", Decimal("0"))


def test_risk_module_has_no_execution_or_infra_authority() -> None:
    from inspect import getsource

    source = getsource(PortfolioRiskEngine)
    forbidden = (
        "ExecutionPlan",
        "VenueAdapter",
        "submit_order(",
        "cancel_order(",
        "ExecutionCoordinator",
        "sqlalchemy",
        ".commit(",
        ".rollback(",
    )
    assert not any(item in source for item in forbidden)
