from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from apps.intelligence.application.market_context import (
    MarketContextBuilder,
    MarketContextInput,
    MarketContextPolicy,
)
from apps.intelligence.domain.market_context import (
    CandleObservation,
    CorrelationObservation,
    DataQualityState,
    EventRiskState,
    FundingOpenInterestObservation,
    FundingState,
    LiquidityState,
    MarketRegime,
    NewsEventObservation,
    ObservationMetadata,
    OrderBookLevel,
    OrderBookObservation,
    TopOfBookObservation,
    TrendState,
    VolatilityState,
)
from packages.contracts.identities import (
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
BTC = InstrumentId(
    venue_id=VenueId("binance"),
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
ETH = InstrumentId(
    venue_id=VenueId("binance"),
    native_symbol="ETHUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def meta(
    *,
    minutes_ago: int = 0,
    freshness_minutes: int = 5,
    gaps: int = 0,
    duplicates: int = 0,
    outliers: int = 0,
    source: str = "fake-feed",
) -> ObservationMetadata:
    event_time = NOW - timedelta(minutes=minutes_ago)
    return ObservationMetadata(
        source=source,
        schema_version="v1",
        event_time=event_time,
        ingestion_time=event_time + timedelta(seconds=1),
        freshness_limit=timedelta(minutes=freshness_minutes),
        provenance=f"{source}:fixture",
        gap_count=gaps,
        duplicate_count=duplicates,
        outlier_count=outliers,
    )


def candle(
    price: str,
    *,
    minutes_ago: int,
    source: str = "candles",
) -> CandleObservation:
    value = Decimal(price)
    return CandleObservation(
        instrument_id=BTC,
        open=value,
        high=value * Decimal("1.001"),
        low=value * Decimal("0.999"),
        close=value,
        volume=Decimal("100"),
        metadata=meta(minutes_ago=minutes_ago, source=source),
    )


def top(
    *,
    bid: str = "99.9",
    ask: str = "100.1",
    minutes_ago: int = 0,
) -> TopOfBookObservation:
    return TopOfBookObservation(
        instrument_id=BTC,
        bid_price=Decimal(bid),
        bid_quantity=Decimal("10"),
        ask_price=Decimal(ask),
        ask_quantity=Decimal("11"),
        metadata=meta(minutes_ago=minutes_ago, source="book-top"),
    )


def book(*, depth_qty: str = "100") -> OrderBookObservation:
    quantity = Decimal(depth_qty)
    return OrderBookObservation(
        instrument_id=BTC,
        bids=(
            OrderBookLevel(Decimal("99.9"), quantity),
            OrderBookLevel(Decimal("99.8"), quantity),
        ),
        asks=(
            OrderBookLevel(Decimal("100.1"), quantity),
            OrderBookLevel(Decimal("100.2"), quantity),
        ),
        metadata=meta(source="book-depth"),
    )


def funding(rate: str = "0.0001") -> FundingOpenInterestObservation:
    return FundingOpenInterestObservation(
        instrument_id=BTC,
        funding_rate=Decimal(rate),
        open_interest=Decimal("25000000"),
        mark_price=Decimal("100"),
        index_price=Decimal("99.95"),
        metadata=meta(source="funding-oi"),
    )


def event(
    severity: EventRiskState,
    *,
    minutes_ago: int = 30,
) -> NewsEventObservation:
    published = NOW - timedelta(minutes=minutes_ago)
    return NewsEventObservation(
        event_id=f"event-{severity.value}-{minutes_ago}",
        published_at=published,
        severity=severity,
        title="Macro event",
        instruments=(BTC,),
        metadata=ObservationMetadata(
            source="news",
            schema_version="v1",
            event_time=published,
            ingestion_time=published + timedelta(seconds=2),
            freshness_limit=timedelta(hours=12),
            provenance="news:fixture",
        ),
    )


def corr(value: str = "0.75") -> CorrelationObservation:
    return CorrelationObservation(
        left=BTC,
        right=ETH,
        coefficient=Decimal(value),
        window="1h-30d",
        metadata=meta(source="correlation"),
    )


def test_metadata_tracks_dual_timestamps_and_provenance() -> None:
    value = meta()
    assert value.ingestion_time > value.event_time
    assert value.provenance == "fake-feed:fixture"


def test_metadata_rejects_ingestion_before_event() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        ObservationMetadata(
            source="feed",
            schema_version="v1",
            event_time=NOW,
            ingestion_time=NOW - timedelta(seconds=1),
            freshness_limit=timedelta(minutes=1),
            provenance="fixture",
        )


def test_quality_current_when_fresh_and_clean() -> None:
    result = meta().quality_at(NOW)
    assert result.state is DataQualityState.CURRENT
    assert result.score == Decimal("1")


def test_quality_stale_is_explicit() -> None:
    result = meta(minutes_ago=10, freshness_minutes=5).quality_at(NOW)
    assert result.state is DataQualityState.STALE
    assert "stale" in result.reasons


def test_quality_degraded_by_gap_duplicate_and_outlier() -> None:
    result = meta(gaps=1, duplicates=2, outliers=1).quality_at(NOW)
    assert result.state is DataQualityState.DEGRADED
    assert set(result.reasons) == {"gaps", "duplicates", "outliers"}
    assert result.score < Decimal("1")


def test_quality_unknown_when_as_of_precedes_event() -> None:
    result = meta().quality_at(NOW - timedelta(minutes=1))
    assert result.state is DataQualityState.UNKNOWN


def test_top_of_book_mid_and_spread_are_decimal_safe() -> None:
    value = top()
    assert value.mid_price == Decimal("100.0")
    assert value.spread_ratio == Decimal("0.002")


def test_top_of_book_rejects_crossed_market() -> None:
    with pytest.raises(ValueError, match="below ask"):
        TopOfBookObservation(
            instrument_id=BTC,
            bid_price=Decimal("101"),
            bid_quantity=Decimal("1"),
            ask_price=Decimal("100"),
            ask_quantity=Decimal("1"),
            metadata=meta(),
        )


def test_order_book_requires_deterministic_sorting() -> None:
    with pytest.raises(ValueError, match="bids must be sorted"):
        OrderBookObservation(
            instrument_id=BTC,
            bids=(
                OrderBookLevel(Decimal("99"), Decimal("1")),
                OrderBookLevel(Decimal("100"), Decimal("1")),
            ),
            asks=(OrderBookLevel(Decimal("101"), Decimal("1")),),
            metadata=meta(),
        )


def test_order_book_visible_depth_notional() -> None:
    value = book(depth_qty="1")
    assert value.visible_depth_notional == Decimal("400.0")


def test_candle_rejects_inconsistent_high() -> None:
    with pytest.raises(ValueError, match="high is inconsistent"):
        CandleObservation(
            instrument_id=BTC,
            open=Decimal("100"),
            high=Decimal("99"),
            low=Decimal("98"),
            close=Decimal("100"),
            volume=Decimal("1"),
            metadata=meta(),
        )


def test_correlation_rejects_invalid_coefficient() -> None:
    with pytest.raises(ValueError, match="between -1 and 1"):
        CorrelationObservation(
            left=BTC,
            right=ETH,
            coefficient=Decimal("1.1"),
            window="1h",
            metadata=meta(),
        )


def test_empty_context_is_unavailable_and_unknown() -> None:
    snapshot = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW)
    )
    assert snapshot.context.data_quality is DataQualityState.UNAVAILABLE
    assert snapshot.context.regime is MarketRegime.UNKNOWN
    assert "market_data_unavailable" in snapshot.context.blockers


def test_current_price_context_is_current() -> None:
    snapshot = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, top_of_book=top())
    )
    assert snapshot.context.data_quality is DataQualityState.CURRENT
    assert snapshot.context.latest_price == Decimal("100.0")


def test_stale_market_data_blocks_regime_classification() -> None:
    stale_top = top(minutes_ago=10)
    snapshot = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, top_of_book=stale_top)
    )
    assert snapshot.context.data_quality is DataQualityState.STALE
    assert snapshot.context.regime is MarketRegime.UNKNOWN
    assert "market_data_stale" in snapshot.context.blockers


def test_bullish_trend_classification() -> None:
    candles = (
        candle("100", minutes_ago=3),
        candle("101", minutes_ago=2),
        candle("102", minutes_ago=1),
        candle("103", minutes_ago=0),
    )
    context = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, candles=candles)
    ).context
    assert context.trend is TrendState.BULLISH
    assert context.regime is MarketRegime.TRENDING_UP


def test_bearish_trend_classification() -> None:
    candles = (
        candle("103", minutes_ago=3),
        candle("102", minutes_ago=2),
        candle("101", minutes_ago=1),
        candle("100", minutes_ago=0),
    )
    context = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, candles=candles)
    ).context
    assert context.trend is TrendState.BEARISH
    assert context.regime is MarketRegime.TRENDING_DOWN


def test_range_regime_for_flat_low_volatility_series() -> None:
    candles = tuple(candle("100", minutes_ago=4 - index) for index in range(5))
    context = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, candles=candles)
    ).context
    assert context.trend is TrendState.NEUTRAL
    assert context.volatility is VolatilityState.LOW
    assert context.regime is MarketRegime.RANGE


def test_high_volatility_overrides_trend_regime() -> None:
    candles = (
        candle("100", minutes_ago=4),
        candle("106", minutes_ago=3),
        candle("96", minutes_ago=2),
        candle("108", minutes_ago=1),
        candle("98", minutes_ago=0),
    )
    context = MarketContextBuilder().build(
        MarketContextInput(instrument_id=BTC, as_of=NOW, candles=candles)
    ).context
    assert context.volatility in (
        VolatilityState.HIGH,
        VolatilityState.EXTREME,
    )
    assert context.regime is MarketRegime.VOLATILE


def test_liquidity_stressed_by_wide_spread() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(bid="99", ask="101"),
        )
    ).context
    assert context.liquidity is LiquidityState.STRESSED


def test_liquidity_thin_by_visible_depth() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            order_book=book(depth_qty="1"),
        )
    ).context
    assert context.liquidity is LiquidityState.THIN


def test_liquidity_deep_by_visible_depth() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            order_book=book(depth_qty="1000"),
        )
    ).context
    assert context.liquidity is LiquidityState.DEEP


@pytest.mark.parametrize(
    ("rate", "expected"),
    [
        ("0.002", FundingState.STRONGLY_POSITIVE),
        ("0.0005", FundingState.POSITIVE),
        ("0", FundingState.NEUTRAL),
        ("-0.0005", FundingState.NEGATIVE),
        ("-0.002", FundingState.STRONGLY_NEGATIVE),
    ],
)
def test_funding_state_classification(
    rate: str,
    expected: FundingState,
) -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            funding_open_interest=funding(rate),
        )
    ).context
    assert context.funding is expected


def test_news_event_risk_selects_highest_active_severity() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            news_events=(
                event(EventRiskState.LOW),
                event(EventRiskState.HIGH),
            ),
        )
    ).context
    assert context.event_risk is EventRiskState.HIGH


def test_old_news_event_does_not_remain_active() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            news_events=(event(EventRiskState.HIGH, minutes_ago=600),),
        )
    ).context
    assert context.event_risk is EventRiskState.NONE


def test_correlations_are_carried_in_deterministic_order() -> None:
    correlation = corr()
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=top(),
            correlations=(correlation,),
        )
    ).context
    assert context.correlations == (correlation,)


def test_sources_are_unique_and_sorted() -> None:
    context = MarketContextBuilder().build(
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            candles=(candle("100", minutes_ago=1, source="z"),),
            top_of_book=top(),
            correlations=(corr(),),
        )
    ).context
    assert context.sources == tuple(sorted(context.sources))
    assert len(context.sources) == len(set(context.sources))


def test_input_rejects_instrument_cross_contamination() -> None:
    foreign = TopOfBookObservation(
        instrument_id=ETH,
        bid_price=Decimal("99"),
        bid_quantity=Decimal("1"),
        ask_price=Decimal("100"),
        ask_quantity=Decimal("1"),
        metadata=meta(),
    )
    with pytest.raises(ValueError, match="instrument mismatch"):
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            top_of_book=foreign,
        )


def test_input_rejects_unrelated_news_event() -> None:
    published = NOW - timedelta(minutes=1)
    foreign = NewsEventObservation(
        event_id="eth-only",
        published_at=published,
        severity=EventRiskState.MEDIUM,
        title="ETH event",
        instruments=(ETH,),
        metadata=ObservationMetadata(
            source="news",
            schema_version="v1",
            event_time=published,
            ingestion_time=published + timedelta(seconds=1),
            freshness_limit=timedelta(hours=1),
            provenance="fixture",
        ),
    )
    with pytest.raises(ValueError, match="does not apply"):
        MarketContextInput(
            instrument_id=BTC,
            as_of=NOW,
            news_events=(foreign,),
        )


def test_policy_rejects_inverted_volatility_thresholds() -> None:
    with pytest.raises(ValueError, match="extreme volatility"):
        MarketContextPolicy(
            high_volatility_threshold=Decimal("0.05"),
            extreme_volatility_threshold=Decimal("0.04"),
        )


def test_market_context_module_has_no_execution_authority() -> None:
    paths = (
        Path("apps/intelligence/domain/market_context.py"),
        Path("apps/intelligence/ports/market_data.py"),
        Path("apps/intelligence/application/market_context.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = (
        "ExecutionCoordinator",
        "VenueAdapter",
        "submit_order(",
        "cancel_order(",
        "sqlalchemy",
        "FastAPI",
        "credentials",
    )
    assert not any(item in source for item in forbidden)


def test_market_data_port_is_read_only() -> None:
    source = Path("apps/intelligence/ports/market_data.py").read_text(
        encoding="utf-8"
    )
    assert "CanonicalMarketDataSource" in source
    assert "async def trades" in source
    assert "async def order_book" in source
    assert "async def funding_open_interest" in source
    assert "submit" not in source.lower()
    assert "cancel" not in source.lower()
