"""Canonical Portfolio Risk V2 domain contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from apps.core.domain.intents import TradeIntentShape, TradeSide
from packages.contracts.identities import AccountId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


class PortfolioRiskState(StrEnum):
    ACTIVE = "ACTIVE"
    REDUCING = "REDUCING"
    HALTED = "HALTED"


class RiskObservationState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class PortfolioRiskDecisionState(StrEnum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"


class PortfolioRiskReason(StrEnum):
    RISK_DATA_NOT_CURRENT = "RISK_DATA_NOT_CURRENT"
    GLOBAL_KILL_SWITCH = "GLOBAL_KILL_SWITCH"
    REDUCING_ONLY = "REDUCING_ONLY"
    SINGLE_LEG_POLICY = "SINGLE_LEG_POLICY"
    MAX_POSITION_GROUPS = "MAX_POSITION_GROUPS"
    GROSS_EXPOSURE = "GROSS_EXPOSURE"
    NET_EXPOSURE = "NET_EXPOSURE"
    ACCOUNT_EXPOSURE = "ACCOUNT_EXPOSURE"
    VENUE_EXPOSURE = "VENUE_EXPOSURE"
    STRATEGY_EXPOSURE = "STRATEGY_EXPOSURE"
    INSTRUMENT_EXPOSURE = "INSTRUMENT_EXPOSURE"
    CURRENCY_CONCENTRATION = "CURRENCY_CONCENTRATION"
    CORRELATION_CLUSTER = "CORRELATION_CLUSTER"
    LEVERAGE = "LEVERAGE"
    MARGIN_UTILIZATION = "MARGIN_UTILIZATION"
    DAILY_DRAWDOWN = "DAILY_DRAWDOWN"
    ROLLING_DRAWDOWN = "ROLLING_DRAWDOWN"
    LIQUIDITY_CAPACITY = "LIQUIDITY_CAPACITY"
    SLIPPAGE = "SLIPPAGE"
    HEDGE_INTEGRITY = "HEDGE_INTEGRITY"


def _require_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


def _require_ratio(value: Decimal, *, field_name: str) -> Decimal:
    normalized = require_non_negative_decimal(
        value,
        field_name=field_name,
    )
    if normalized > Decimal("1"):
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


@dataclass(frozen=True, slots=True)
class PortfolioRiskLimits:
    max_open_position_groups: int
    max_gross_exposure: Decimal
    max_net_exposure: Decimal
    max_account_exposure: Decimal
    max_venue_exposure: Decimal
    max_strategy_exposure: Decimal
    max_instrument_exposure: Decimal
    max_currency_concentration: Decimal
    max_correlation_cluster_exposure: Decimal
    max_leverage: Decimal
    max_margin_utilization: Decimal
    max_daily_drawdown: Decimal
    max_rolling_drawdown: Decimal
    max_order_liquidity_ratio: Decimal
    max_expected_slippage_bps: Decimal
    hedge_tolerance: Decimal = Decimal("0.05")

    def __post_init__(self) -> None:
        if (
            not isinstance(self.max_open_position_groups, int)
            or isinstance(self.max_open_position_groups, bool)
            or self.max_open_position_groups <= 0
        ):
            raise ValueError(
                "max_open_position_groups must be a positive integer"
            )

        for field_name in (
            "max_gross_exposure",
            "max_net_exposure",
            "max_account_exposure",
            "max_venue_exposure",
            "max_strategy_exposure",
            "max_instrument_exposure",
            "max_correlation_cluster_exposure",
            "max_leverage",
            "max_expected_slippage_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                require_positive_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        for field_name in (
            "max_currency_concentration",
            "max_margin_utilization",
            "max_daily_drawdown",
            "max_rolling_drawdown",
            "max_order_liquidity_ratio",
            "hedge_tolerance",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )


@dataclass(frozen=True, slots=True)
class PortfolioExposure:
    position_group_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    strategy: str
    settlement_currency: str
    correlation_cluster: str
    signed_notional: Decimal
    margin_used: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "position_group_id",
            _require_text(
                self.position_group_id,
                field_name="position_group_id",
            ),
        )
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

        for field_name in (
            "strategy",
            "settlement_currency",
            "correlation_cluster",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if not isinstance(self.signed_notional, Decimal):
            raise ValueError("signed_notional must be a Decimal")
        if not self.signed_notional.is_finite():
            raise ValueError("signed_notional must be finite")

        object.__setattr__(
            self,
            "margin_used",
            require_non_negative_decimal(
                self.margin_used,
                field_name="margin_used",
            ),
        )


@dataclass(frozen=True, slots=True)
class PortfolioRiskSnapshot:
    user_id: int
    observation_state: RiskObservationState
    trading_state: PortfolioRiskState
    equity: Decimal
    daily_start_equity: Decimal
    rolling_peak_equity: Decimal
    exposures: tuple[PortfolioExposure, ...]
    observed_at: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")
        if not isinstance(
            self.observation_state,
            RiskObservationState,
        ):
            raise ValueError(
                "observation_state must be RiskObservationState"
            )
        if not isinstance(self.trading_state, PortfolioRiskState):
            raise ValueError(
                "trading_state must be PortfolioRiskState"
            )

        for field_name in (
            "equity",
            "daily_start_equity",
            "rolling_peak_equity",
        ):
            object.__setattr__(
                self,
                field_name,
                require_positive_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if not isinstance(self.exposures, tuple):
            raise ValueError("exposures must be a tuple")
        if not all(
            isinstance(item, PortfolioExposure)
            for item in self.exposures
        ):
            raise ValueError(
                "exposures must contain PortfolioExposure values"
            )

        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class RiskLegCandidate:
    leg_id: str
    account_id: AccountId
    instrument_id: InstrumentId
    side: TradeSide
    quantity: Decimal
    reduce_only: bool
    mark_price: Decimal
    settlement_currency: str
    correlation_cluster: str
    available_liquidity_notional: Decimal
    expected_slippage_bps: Decimal
    leverage: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "leg_id",
            _require_text(self.leg_id, field_name="leg_id"),
        )
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be an AccountId")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )
        if not isinstance(self.side, TradeSide):
            raise ValueError("side must be TradeSide")
        if not isinstance(self.reduce_only, bool):
            raise ValueError("reduce_only must be boolean")

        for field_name in (
            "quantity",
            "mark_price",
            "available_liquidity_notional",
            "leverage",
        ):
            object.__setattr__(
                self,
                field_name,
                require_positive_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        object.__setattr__(
            self,
            "expected_slippage_bps",
            require_non_negative_decimal(
                self.expected_slippage_bps,
                field_name="expected_slippage_bps",
            ),
        )
        for field_name in (
            "settlement_currency",
            "correlation_cluster",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )


@dataclass(frozen=True, slots=True)
class PortfolioRiskRequest:
    intent_id: str
    user_id: int
    shape: TradeIntentShape
    strategy: str
    legs: tuple[RiskLegCandidate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "intent_id",
            _require_text(self.intent_id, field_name="intent_id"),
        )
        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")
        if not isinstance(self.shape, TradeIntentShape):
            raise ValueError("shape must be TradeIntentShape")
        object.__setattr__(
            self,
            "strategy",
            _require_text(self.strategy, field_name="strategy"),
        )
        if not isinstance(self.legs, tuple):
            raise ValueError("legs must be a tuple")
        if not all(
            isinstance(leg, RiskLegCandidate)
            for leg in self.legs
        ):
            raise ValueError(
                "legs must contain RiskLegCandidate values"
            )

        leg_count = len(self.legs)
        if self.shape is TradeIntentShape.SINGLE_LEG and leg_count != 1:
            raise ValueError("SINGLE_LEG risk request requires one leg")
        if self.shape is TradeIntentShape.PAIR and leg_count != 2:
            raise ValueError("PAIR risk request requires two legs")
        if self.shape is TradeIntentShape.BASKET and leg_count < 2:
            raise ValueError(
                "BASKET risk request requires at least two legs"
            )

        leg_ids = tuple(leg.leg_id for leg in self.legs)
        if len(set(leg_ids)) != len(leg_ids):
            raise ValueError("risk request leg IDs must be unique")


@dataclass(frozen=True, slots=True)
class HedgeTarget:
    leg_id: str
    weight: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "leg_id",
            _require_text(self.leg_id, field_name="leg_id"),
        )
        if not isinstance(self.weight, Decimal):
            raise ValueError("weight must be a Decimal")
        if not self.weight.is_finite() or self.weight == 0:
            raise ValueError("weight must be finite and non-zero")


@dataclass(frozen=True, slots=True)
class PortfolioRiskDecision:
    state: PortfolioRiskDecisionState
    reasons: tuple[PortfolioRiskReason, ...]
    projected_gross_exposure: Decimal
    projected_net_exposure: Decimal
    projected_leverage: Decimal
    projected_margin_utilization: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioRiskDecisionState):
            raise ValueError(
                "state must be PortfolioRiskDecisionState"
            )
        if not isinstance(self.reasons, tuple):
            raise ValueError("reasons must be a tuple")
        if not all(
            isinstance(reason, PortfolioRiskReason)
            for reason in self.reasons
        ):
            raise ValueError(
                "reasons must contain PortfolioRiskReason values"
            )
        if len(set(self.reasons)) != len(self.reasons):
            raise ValueError("reasons must be unique")
        if (
            self.state is PortfolioRiskDecisionState.APPROVED
            and self.reasons
        ):
            raise ValueError(
                "APPROVED decision cannot contain block reasons"
            )
        if (
            self.state is PortfolioRiskDecisionState.BLOCKED
            and not self.reasons
        ):
            raise ValueError(
                "BLOCKED decision requires at least one reason"
            )

        for field_name in (
            "projected_gross_exposure",
            "projected_net_exposure",
            "projected_leverage",
            "projected_margin_utilization",
        ):
            object.__setattr__(
                self,
                field_name,
                require_non_negative_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
