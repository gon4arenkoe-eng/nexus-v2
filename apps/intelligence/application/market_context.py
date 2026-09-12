"""Deterministic Intelligence V2 MarketContext builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import sqrt

from apps.intelligence.domain.market_context import (
    CandleObservation,
    CorrelationObservation,
    DataQualityAssessment,
    DataQualityState,
    EventRiskState,
    FundingOpenInterestObservation,
    FundingState,
    LiquidityState,
    MarketContext,
    MarketRegime,
    NewsEventObservation,
    ObservationMetadata,
    OrderBookObservation,
    TopOfBookObservation,
    TrendState,
    VolatilityState,
)
from packages.contracts.identities import InstrumentId


@dataclass(frozen=True, slots=True)
class MarketContextPolicy:
    trend_threshold: Decimal = Decimal("0.01")
    high_volatility_threshold: Decimal = Decimal("0.02")
    extreme_volatility_threshold: Decimal = Decimal("0.05")
    thin_spread_threshold: Decimal = Decimal("0.003")
    stressed_spread_threshold: Decimal = Decimal("0.01")
    deep_depth_notional: Decimal = Decimal("100000")
    thin_depth_notional: Decimal = Decimal("5000")
    strong_funding_threshold: Decimal = Decimal("0.001")
    funding_threshold: Decimal = Decimal("0.0002")
    news_window: timedelta = timedelta(hours=4)

    def __post_init__(self) -> None:
        for name in (
            "trend_threshold",
            "high_volatility_threshold",
            "extreme_volatility_threshold",
            "thin_spread_threshold",
            "stressed_spread_threshold",
            "deep_depth_notional",
            "thin_depth_notional",
            "strong_funding_threshold",
            "funding_threshold",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or value <= Decimal("0"):
                raise ValueError(f"{name} must be a positive Decimal")
        if self.extreme_volatility_threshold <= self.high_volatility_threshold:
            raise ValueError(
                "extreme volatility threshold must exceed high threshold"
            )
        if self.stressed_spread_threshold <= self.thin_spread_threshold:
            raise ValueError(
                "stressed spread threshold must exceed thin threshold"
            )
        if self.deep_depth_notional <= self.thin_depth_notional:
            raise ValueError("deep depth must exceed thin depth")
        if self.strong_funding_threshold <= self.funding_threshold:
            raise ValueError(
                "strong funding threshold must exceed funding threshold"
            )
        if self.news_window <= timedelta(0):
            raise ValueError("news_window must be positive")


@dataclass(frozen=True, slots=True)
class MarketContextInput:
    instrument_id: InstrumentId
    as_of: datetime
    candles: tuple[CandleObservation, ...] = ()
    top_of_book: TopOfBookObservation | None = None
    order_book: OrderBookObservation | None = None
    funding_open_interest: FundingOpenInterestObservation | None = None
    news_events: tuple[NewsEventObservation, ...] = ()
    correlations: tuple[CorrelationObservation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        if not isinstance(self.as_of, datetime) or self.as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        object.__setattr__(self, "as_of", self.as_of.astimezone(timezone.utc))
        for item in self.candles:
            _same_instrument(self.instrument_id, item.instrument_id)
        if self.top_of_book is not None:
            _same_instrument(
                self.instrument_id,
                self.top_of_book.instrument_id,
            )
        if self.order_book is not None:
            _same_instrument(self.instrument_id, self.order_book.instrument_id)
        if self.funding_open_interest is not None:
            _same_instrument(
                self.instrument_id,
                self.funding_open_interest.instrument_id,
            )
        for news_event in self.news_events:
            if (
                news_event.instruments
                and self.instrument_id not in news_event.instruments
            ):
                raise ValueError("news event does not apply to instrument")
        for correlation in self.correlations:
            if self.instrument_id not in (
                correlation.left,
                correlation.right,
            ):
                raise ValueError("correlation does not include instrument")


@dataclass(frozen=True, slots=True)
class IntelligenceSnapshot:
    context: MarketContext
    quality: tuple[DataQualityAssessment, ...]


class MarketContextBuilder:
    def __init__(self, policy: MarketContextPolicy | None = None) -> None:
        self._policy = policy or MarketContextPolicy()

    def build(self, request: MarketContextInput) -> IntelligenceSnapshot:
        metadata = _metadata(request)
        assessments = tuple(
            item.quality_at(request.as_of) for item in metadata
        )
        quality_state, quality_score, blockers = _aggregate_quality(
            assessments,
            has_price=bool(request.candles or request.top_of_book),
        )
        candles = tuple(
            sorted(
                request.candles,
                key=lambda item: item.metadata.event_time,
            )
        )
        latest_price = _latest_price(candles, request.top_of_book)
        volatility, volatility_value = _volatility(candles, self._policy)
        trend, trend_return = _trend(candles, self._policy)
        liquidity = _liquidity(
            request.top_of_book,
            request.order_book,
            self._policy,
        )
        funding = _funding(request.funding_open_interest, self._policy)
        event_risk = _event_risk(
            request.news_events,
            request.as_of,
            self._policy,
        )
        regime = _regime(
            trend=trend,
            volatility=volatility,
            trend_return=trend_return,
            volatility_value=volatility_value,
            quality=quality_state,
        )
        spread = (
            request.top_of_book.spread_ratio
            if request.top_of_book
            else None
        )
        depth = (
            request.order_book.visible_depth_notional
            if request.order_book is not None
            else None
        )
        funding_rate = (
            request.funding_open_interest.funding_rate
            if request.funding_open_interest is not None
            else None
        )
        open_interest = (
            request.funding_open_interest.open_interest
            if request.funding_open_interest is not None
            else None
        )
        sources = tuple(sorted({item.source for item in metadata}))
        context = MarketContext(
            instrument_id=request.instrument_id,
            as_of=request.as_of,
            regime=regime,
            volatility=volatility,
            trend=trend,
            liquidity=liquidity,
            funding=funding,
            event_risk=event_risk,
            data_quality=quality_state,
            data_quality_score=quality_score,
            latest_price=latest_price,
            spread_ratio=spread,
            visible_depth_notional=depth,
            funding_rate=funding_rate,
            open_interest=open_interest,
            correlations=tuple(
                sorted(
                    request.correlations,
                    key=lambda item: (
                        item.left.native_symbol,
                        item.right.native_symbol,
                        item.window,
                    ),
                )
            ),
            sources=sources,
            blockers=tuple(sorted(blockers)),
        )
        return IntelligenceSnapshot(context=context, quality=assessments)


def _same_instrument(expected: InstrumentId, actual: InstrumentId) -> None:
    if actual != expected:
        raise ValueError("observation instrument mismatch")


def _metadata(request: MarketContextInput) -> tuple[ObservationMetadata, ...]:
    values: list[ObservationMetadata] = [
        item.metadata for item in request.candles
    ]
    if request.top_of_book is not None:
        values.append(request.top_of_book.metadata)
    if request.order_book is not None:
        values.append(request.order_book.metadata)
    if request.funding_open_interest is not None:
        values.append(request.funding_open_interest.metadata)
    values.extend(item.metadata for item in request.news_events)
    values.extend(item.metadata for item in request.correlations)
    return tuple(values)


def _aggregate_quality(
    assessments: tuple[DataQualityAssessment, ...],
    *,
    has_price: bool,
) -> tuple[DataQualityState, Decimal, set[str]]:
    if not assessments:
        return (
            DataQualityState.UNAVAILABLE,
            Decimal("0"),
            {"market_data_unavailable"},
        )
    score = (
        sum((item.score for item in assessments), Decimal("0"))
        / len(assessments)
    )
    states = {item.state for item in assessments}
    blockers: set[str] = set()
    if not has_price:
        blockers.add("price_context_unavailable")
    if DataQualityState.UNKNOWN in states:
        blockers.add("market_data_unknown")
        return DataQualityState.UNKNOWN, score, blockers
    if DataQualityState.UNAVAILABLE in states:
        blockers.add("market_data_unavailable")
        return DataQualityState.UNAVAILABLE, score, blockers
    if DataQualityState.STALE in states:
        blockers.add("market_data_stale")
        return DataQualityState.STALE, score, blockers
    if DataQualityState.DEGRADED in states:
        blockers.add("market_data_degraded")
        return DataQualityState.DEGRADED, score, blockers
    if not has_price:
        return DataQualityState.UNAVAILABLE, score, blockers
    return DataQualityState.CURRENT, score, blockers


def _latest_price(
    candles: tuple[CandleObservation, ...],
    top: TopOfBookObservation | None,
) -> Decimal | None:
    candidates: list[tuple[datetime, Decimal]] = []
    if candles:
        candidates.append((candles[-1].metadata.event_time, candles[-1].close))
    if top is not None:
        candidates.append((top.metadata.event_time, top.mid_price))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _returns(candles: tuple[CandleObservation, ...]) -> tuple[Decimal, ...]:
    if len(candles) < 2:
        return ()
    values: list[Decimal] = []
    for previous, current in zip(candles, candles[1:]):
        values.append((current.close - previous.close) / previous.close)
    return tuple(values)


def _volatility(
    candles: tuple[CandleObservation, ...],
    policy: MarketContextPolicy,
) -> tuple[VolatilityState, Decimal | None]:
    returns = _returns(candles)
    if len(returns) < 2:
        return VolatilityState.UNKNOWN, None
    mean = sum(returns, Decimal("0")) / len(returns)
    variance = (
        sum(((item - mean) ** 2 for item in returns), Decimal("0"))
        / len(returns)
    )
    value = Decimal(str(sqrt(float(variance))))
    if value >= policy.extreme_volatility_threshold:
        return VolatilityState.EXTREME, value
    if value >= policy.high_volatility_threshold:
        return VolatilityState.HIGH, value
    if value <= policy.high_volatility_threshold / Decimal("4"):
        return VolatilityState.LOW, value
    return VolatilityState.NORMAL, value


def _trend(
    candles: tuple[CandleObservation, ...],
    policy: MarketContextPolicy,
) -> tuple[TrendState, Decimal | None]:
    if len(candles) < 2:
        return TrendState.UNKNOWN, None
    change = (candles[-1].close - candles[0].close) / candles[0].close
    if change >= policy.trend_threshold:
        return TrendState.BULLISH, change
    if change <= -policy.trend_threshold:
        return TrendState.BEARISH, change
    return TrendState.NEUTRAL, change


def _liquidity(
    top: TopOfBookObservation | None,
    book: OrderBookObservation | None,
    policy: MarketContextPolicy,
) -> LiquidityState:
    if top is None and book is None:
        return LiquidityState.UNKNOWN
    spread = top.spread_ratio if top is not None else None
    depth = book.visible_depth_notional if book is not None else None
    if spread is not None and spread >= policy.stressed_spread_threshold:
        return LiquidityState.STRESSED
    if depth is not None and depth <= policy.thin_depth_notional:
        return LiquidityState.THIN
    if spread is not None and spread >= policy.thin_spread_threshold:
        return LiquidityState.THIN
    if depth is not None and depth >= policy.deep_depth_notional:
        return LiquidityState.DEEP
    return LiquidityState.NORMAL


def _funding(
    item: FundingOpenInterestObservation | None,
    policy: MarketContextPolicy,
) -> FundingState:
    if item is None:
        return FundingState.UNKNOWN
    rate = item.funding_rate
    if rate >= policy.strong_funding_threshold:
        return FundingState.STRONGLY_POSITIVE
    if rate >= policy.funding_threshold:
        return FundingState.POSITIVE
    if rate <= -policy.strong_funding_threshold:
        return FundingState.STRONGLY_NEGATIVE
    if rate <= -policy.funding_threshold:
        return FundingState.NEGATIVE
    return FundingState.NEUTRAL


def _event_risk(
    events: tuple[NewsEventObservation, ...],
    as_of: datetime,
    policy: MarketContextPolicy,
) -> EventRiskState:
    active = [
        item.severity
        for item in events
        if timedelta(0) <= as_of - item.published_at <= policy.news_window
    ]
    if not events:
        return EventRiskState.NONE
    if not active:
        return EventRiskState.NONE
    rank = {
        EventRiskState.NONE: 0,
        EventRiskState.LOW: 1,
        EventRiskState.MEDIUM: 2,
        EventRiskState.HIGH: 3,
        EventRiskState.UNKNOWN: 4,
    }
    return max(active, key=lambda item: rank[item])


def _regime(
    *,
    trend: TrendState,
    volatility: VolatilityState,
    trend_return: Decimal | None,
    volatility_value: Decimal | None,
    quality: DataQualityState,
) -> MarketRegime:
    if quality is not DataQualityState.CURRENT:
        return MarketRegime.UNKNOWN
    if volatility in (VolatilityState.HIGH, VolatilityState.EXTREME):
        return MarketRegime.VOLATILE
    if trend is TrendState.BULLISH:
        return MarketRegime.TRENDING_UP
    if trend is TrendState.BEARISH:
        return MarketRegime.TRENDING_DOWN
    if (
        trend is TrendState.NEUTRAL
        and volatility is not VolatilityState.UNKNOWN
    ):
        return MarketRegime.RANGE
    if trend_return is not None and volatility_value is not None:
        return MarketRegime.TRANSITION
    return MarketRegime.UNKNOWN
