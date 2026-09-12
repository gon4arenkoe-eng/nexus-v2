"""Canonical market observations and MarketContext contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import StrEnum

from packages.contracts.identities import InstrumentId


_ZERO = Decimal("0")
_ONE = Decimal("1")


def _utc(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _positive(value: Decimal, *, field_name: str) -> Decimal:
    if not isinstance(value, Decimal) or value <= _ZERO:
        raise ValueError(f"{field_name} must be a positive Decimal")
    return value


def _non_negative(value: Decimal, *, field_name: str) -> Decimal:
    if not isinstance(value, Decimal) or value < _ZERO:
        raise ValueError(f"{field_name} must be a non-negative Decimal")
    return value


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


class DataQualityState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class MarketRegime(StrEnum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGE = "RANGE"
    VOLATILE = "VOLATILE"
    TRANSITION = "TRANSITION"
    UNKNOWN = "UNKNOWN"


class VolatilityState(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class TrendState(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class LiquidityState(StrEnum):
    THIN = "THIN"
    NORMAL = "NORMAL"
    DEEP = "DEEP"
    STRESSED = "STRESSED"
    UNKNOWN = "UNKNOWN"


class FundingState(StrEnum):
    STRONGLY_NEGATIVE = "STRONGLY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    STRONGLY_POSITIVE = "STRONGLY_POSITIVE"
    UNKNOWN = "UNKNOWN"


class EventRiskState(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ObservationMetadata:
    source: str
    schema_version: str
    event_time: datetime
    ingestion_time: datetime
    freshness_limit: timedelta
    provenance: str
    gap_count: int = 0
    duplicate_count: int = 0
    outlier_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source",
            _text(self.source, field_name="source"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, field_name="schema_version"),
        )
        object.__setattr__(
            self,
            "event_time",
            _utc(self.event_time, field_name="event_time"),
        )
        object.__setattr__(
            self,
            "ingestion_time",
            _utc(self.ingestion_time, field_name="ingestion_time"),
        )
        object.__setattr__(
            self,
            "provenance",
            _text(self.provenance, field_name="provenance"),
        )
        if self.ingestion_time < self.event_time:
            raise ValueError("ingestion_time cannot precede event_time")
        if not isinstance(self.freshness_limit, timedelta):
            raise ValueError("freshness_limit must be a timedelta")
        if self.freshness_limit <= timedelta(0):
            raise ValueError("freshness_limit must be positive")
        for field_name in ("gap_count", "duplicate_count", "outlier_count"):
            value = getattr(self, field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be a non-negative integer"
                )

    def quality_at(self, as_of: datetime) -> "DataQualityAssessment":
        observed_at = _utc(as_of, field_name="as_of")
        if observed_at < self.event_time:
            return DataQualityAssessment(
                state=DataQualityState.UNKNOWN,
                score=_ZERO,
                age=timedelta(0),
                reasons=("as_of_before_event",),
            )
        age = observed_at - self.event_time
        reasons: list[str] = []
        score = _ONE
        state = DataQualityState.CURRENT
        if age > self.freshness_limit:
            state = DataQualityState.STALE
            score -= Decimal("0.60")
            reasons.append("stale")
        if self.gap_count:
            state = (
                DataQualityState.STALE
                if state is DataQualityState.STALE
                else DataQualityState.DEGRADED
            )
            score -= min(Decimal("0.30"), Decimal("0.05") * self.gap_count)
            reasons.append("gaps")
        if self.duplicate_count:
            if state is DataQualityState.CURRENT:
                state = DataQualityState.DEGRADED
            score -= min(
                Decimal("0.20"),
                Decimal("0.02") * self.duplicate_count,
            )
            reasons.append("duplicates")
        if self.outlier_count:
            if state is DataQualityState.CURRENT:
                state = DataQualityState.DEGRADED
            score -= min(
                Decimal("0.30"),
                Decimal("0.05") * self.outlier_count,
            )
            reasons.append("outliers")
        return DataQualityAssessment(
            state=state,
            score=max(_ZERO, score),
            age=age,
            reasons=tuple(reasons),
        )


@dataclass(frozen=True, slots=True)
class DataQualityAssessment:
    state: DataQualityState
    score: Decimal
    age: timedelta
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state, DataQualityState):
            raise ValueError("state must be a DataQualityState")
        if (
            not isinstance(self.score, Decimal)
            or not (_ZERO <= self.score <= _ONE)
        ):
            raise ValueError("score must be a Decimal between 0 and 1")
        if not isinstance(self.age, timedelta) or self.age < timedelta(0):
            raise ValueError("age must be a non-negative timedelta")
        if any(not item.strip() for item in self.reasons):
            raise ValueError("reasons must be non-empty strings")


@dataclass(frozen=True, slots=True)
class TradeObservation:
    instrument_id: InstrumentId
    price: Decimal
    quantity: Decimal
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        _positive(self.price, field_name="price")
        _positive(self.quantity, field_name="quantity")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")


@dataclass(frozen=True, slots=True)
class CandleObservation:
    instrument_id: InstrumentId
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        for name in ("open", "high", "low", "close"):
            _positive(getattr(self, name), field_name=name)
        _non_negative(self.volume, field_name="volume")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high is inconsistent with OHLC")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low is inconsistent with OHLC")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")


@dataclass(frozen=True, slots=True)
class TopOfBookObservation:
    instrument_id: InstrumentId
    bid_price: Decimal
    bid_quantity: Decimal
    ask_price: Decimal
    ask_quantity: Decimal
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        for name in ("bid_price", "bid_quantity", "ask_price", "ask_quantity"):
            _positive(getattr(self, name), field_name=name)
        if self.bid_price >= self.ask_price:
            raise ValueError("bid_price must be below ask_price")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")

    @property
    def mid_price(self) -> Decimal:
        return (self.bid_price + self.ask_price) / Decimal("2")

    @property
    def spread_ratio(self) -> Decimal:
        return (self.ask_price - self.bid_price) / self.mid_price


@dataclass(frozen=True, slots=True)
class OrderBookLevel:
    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        _positive(self.price, field_name="price")
        _positive(self.quantity, field_name="quantity")


@dataclass(frozen=True, slots=True)
class OrderBookObservation:
    instrument_id: InstrumentId
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        if not self.bids or not self.asks:
            raise ValueError("order book requires bid and ask levels")
        if any(
            not isinstance(item, OrderBookLevel)
            for item in self.bids + self.asks
        ):
            raise ValueError("book levels must be OrderBookLevel values")
        if (
            tuple(
                sorted(
                    self.bids,
                    key=lambda item: item.price,
                    reverse=True,
                )
            )
            != self.bids
        ):
            raise ValueError("bids must be sorted descending by price")
        if tuple(sorted(self.asks, key=lambda item: item.price)) != self.asks:
            raise ValueError("asks must be sorted ascending by price")
        if self.bids[0].price >= self.asks[0].price:
            raise ValueError("best bid must be below best ask")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")

    @property
    def visible_depth_notional(self) -> Decimal:
        return sum(
            (level.price * level.quantity for level in self.bids + self.asks),
            start=_ZERO,
        )


@dataclass(frozen=True, slots=True)
class FundingOpenInterestObservation:
    instrument_id: InstrumentId
    funding_rate: Decimal
    open_interest: Decimal
    mark_price: Decimal
    index_price: Decimal
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        if not isinstance(self.funding_rate, Decimal):
            raise ValueError("funding_rate must be a Decimal")
        _non_negative(self.open_interest, field_name="open_interest")
        _positive(self.mark_price, field_name="mark_price")
        _positive(self.index_price, field_name="index_price")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")


@dataclass(frozen=True, slots=True)
class NewsEventObservation:
    event_id: str
    published_at: datetime
    severity: EventRiskState
    title: str
    instruments: tuple[InstrumentId, ...]
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _text(self.event_id, field_name="event_id"),
        )
        object.__setattr__(
            self,
            "published_at",
            _utc(self.published_at, field_name="published_at"),
        )
        object.__setattr__(
            self,
            "title",
            _text(self.title, field_name="title"),
        )
        if not isinstance(self.severity, EventRiskState):
            raise ValueError("severity must be an EventRiskState")
        if any(
            not isinstance(item, InstrumentId)
            for item in self.instruments
        ):
            raise ValueError("instruments must contain InstrumentId values")
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")


@dataclass(frozen=True, slots=True)
class CorrelationObservation:
    left: InstrumentId
    right: InstrumentId
    coefficient: Decimal
    window: str
    metadata: ObservationMetadata

    def __post_init__(self) -> None:
        if (
            not isinstance(self.left, InstrumentId)
            or not isinstance(self.right, InstrumentId)
        ):
            raise ValueError("left/right must be InstrumentId values")
        if self.left == self.right:
            raise ValueError("correlation instruments must differ")
        if not isinstance(self.coefficient, Decimal):
            raise ValueError("coefficient must be a Decimal")
        if not Decimal("-1") <= self.coefficient <= _ONE:
            raise ValueError("coefficient must be between -1 and 1")
        object.__setattr__(
            self,
            "window",
            _text(self.window, field_name="window"),
        )
        if not isinstance(self.metadata, ObservationMetadata):
            raise ValueError("metadata must be ObservationMetadata")


@dataclass(frozen=True, slots=True)
class MarketContext:
    instrument_id: InstrumentId
    as_of: datetime
    regime: MarketRegime
    volatility: VolatilityState
    trend: TrendState
    liquidity: LiquidityState
    funding: FundingState
    event_risk: EventRiskState
    data_quality: DataQualityState
    data_quality_score: Decimal
    latest_price: Decimal | None
    spread_ratio: Decimal | None
    visible_depth_notional: Decimal | None
    funding_rate: Decimal | None
    open_interest: Decimal | None
    correlations: tuple[CorrelationObservation, ...]
    sources: tuple[str, ...]
    blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")
        object.__setattr__(self, "as_of", _utc(self.as_of, field_name="as_of"))
        for name, enum_type in (
            ("regime", MarketRegime),
            ("volatility", VolatilityState),
            ("trend", TrendState),
            ("liquidity", LiquidityState),
            ("funding", FundingState),
            ("event_risk", EventRiskState),
            ("data_quality", DataQualityState),
        ):
            if not isinstance(getattr(self, name), enum_type):
                raise ValueError(f"{name} has invalid enum type")
        if not isinstance(self.data_quality_score, Decimal):
            raise ValueError("data_quality_score must be Decimal")
        if not _ZERO <= self.data_quality_score <= _ONE:
            raise ValueError("data_quality_score must be between 0 and 1")
        for name in (
            "latest_price",
            "spread_ratio",
            "visible_depth_notional",
            "open_interest",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, Decimal) or value < _ZERO
            ):
                raise ValueError(
                    f"{name} must be a non-negative Decimal or None"
                )
        if (
            self.funding_rate is not None
            and not isinstance(self.funding_rate, Decimal)
        ):
            raise ValueError("funding_rate must be Decimal or None")
        if any(
            not isinstance(item, CorrelationObservation)
            for item in self.correlations
        ):
            raise ValueError(
                "correlations must contain CorrelationObservation values"
            )
        if tuple(sorted(set(self.sources))) != self.sources:
            raise ValueError("sources must be unique and sorted")
        if tuple(sorted(set(self.blockers))) != self.blockers:
            raise ValueError("blockers must be unique and sorted")
