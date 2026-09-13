"""Historical candle access for AIEA backtesting.

`apps.intelligence.ports.market_data.CanonicalMarketDataSource` only exposes
"give me the latest N candles" (`candles(instrument_id, limit)`), which is the
right shape for a *live* intelligence read but the wrong shape for
*backtesting*, which needs arbitrary past date/bar ranges. Rather than bend
the existing live port to do something it was not designed for, this module
adds a second, narrow port (`HistoricalCandleRangeSource`) purely for
research/backtest use, plus one concrete implementation
(`InMemoryCandleReplaySource`) that also satisfies `CanonicalMarketDataSource`
so it can be used as a stand-in Intelligence source in tests/demos.

Nothing here talks to a real exchange. `synthetic_ohlcv()` produces a fully
deterministic (seeded) synthetic series with three distinct regime phases
(trend, range, high-volatility) so that regime-dependent falsification
checks in `backtest_worker.py` have something real to discriminate on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Sequence

from apps.intelligence.domain.market_context import (
    CandleObservation,
    CorrelationObservation,
    FundingOpenInterestObservation,
    NewsEventObservation,
    ObservationMetadata,
    OrderBookObservation,
    TopOfBookObservation,
    TradeObservation,
)
from packages.contracts.identities import InstrumentId


from apps.aiea.ports.historical_data import HistoricalCandleRangeSource


def _metadata(event_time: datetime, *, source: str) -> ObservationMetadata:
    return ObservationMetadata(
        source=source,
        schema_version="1",
        event_time=event_time,
        ingestion_time=event_time,
        freshness_limit=timedelta(days=3650),
        provenance="synthetic-replay",
    )


def synthetic_ohlcv(
    *,
    instrument_id: InstrumentId,
    seed: int,
    bars: int = 720,
    start: datetime | None = None,
    bar_interval: timedelta = timedelta(hours=1),
    start_price: Decimal = Decimal("50000"),
) -> list[CandleObservation]:
    """Deterministic synthetic OHLCV series with three regime phases.

    Phase 1 (first 40% of bars): steady upward drift  -> TREND regime.
    Phase 2 (next 30%): near-zero drift, mean-reverting -> RANGE regime.
    Phase 3 (final 30%): high-variance, no drift -> VOLATILE regime.

    Fully reproducible for a given (seed, bars): re-running with the same
    arguments always yields byte-identical candles, which is required for
    the dataset content-hash / replay checks in the falsification pipeline.
    """
    if bars < 10:
        raise ValueError("bars must be >= 10 for a usable train/val/test split")
    rng = random.Random(seed)
    started_at = start or datetime(2024, 1, 1, tzinfo=UTC)

    phase1_end = int(bars * 0.4)
    phase2_end = int(bars * 0.7)

    price = start_price
    candles: list[CandleObservation] = []
    for i in range(bars):
        if i < phase1_end:
            drift = Decimal("0.0009")
            vol = Decimal("0.006")
        elif i < phase2_end:
            drift = Decimal("0.0000")
            vol = Decimal("0.004")
        else:
            drift = Decimal("0.0000")
            vol = Decimal("0.016")

        shock = Decimal(str(round(rng.gauss(0.0, float(vol)), 6)))
        change = drift + shock
        open_price = price
        close_price = max(Decimal("1"), open_price * (Decimal("1") + change))
        wick = abs(change) / Decimal("2") + Decimal("0.001")
        high_price = max(open_price, close_price) * (Decimal("1") + wick)
        low_price = min(open_price, close_price) * (Decimal("1") - wick)
        volume = Decimal(str(round(abs(rng.gauss(120.0, 40.0)) + 5.0, 3)))

        event_time = started_at + bar_interval * i
        candles.append(
            CandleObservation(
                instrument_id=instrument_id,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                metadata=_metadata(event_time, source="synthetic-replay"),
            )
        )
        price = close_price
    return candles


@dataclass
class InMemoryCandleReplaySource:
    """Deterministic in-memory candle source for backtesting and demos.

    Implements `HistoricalCandleRangeSource` (research/backtest use) and the
    full `CanonicalMarketDataSource` surface (so it can also stand in as an
    Intelligence live-data source in tests) by returning empty/None for the
    observation kinds it does not model (order book, funding, news,
    correlations, trades).
    """

    candles_by_instrument: dict[str, list[CandleObservation]]

    @classmethod
    def single_symbol(
        cls,
        instrument_id: InstrumentId,
        candles: Sequence[CandleObservation],
    ) -> "InMemoryCandleReplaySource":
        return cls(
            candles_by_instrument={
                instrument_id.native_symbol: list(candles),
            }
        )

    def _series(self, instrument_id: InstrumentId) -> list[CandleObservation]:
        series = self.candles_by_instrument.get(instrument_id.native_symbol)
        if series is None:
            raise ValueError(
                f"no synthetic/replay series loaded for {instrument_id.native_symbol}"
            )
        return series

    # -- HistoricalCandleRangeSource -----------------------------------

    async def candles_between(
        self,
        *,
        instrument_id: InstrumentId,
        start_index: int,
        end_index: int,
    ) -> tuple[CandleObservation, ...]:
        series = self._series(instrument_id)
        if start_index < 0 or end_index > len(series) or start_index >= end_index:
            raise ValueError(
                f"invalid bar range [{start_index}:{end_index}] for "
                f"series of length {len(series)}"
            )
        return tuple(series[start_index:end_index])

    async def bar_count(self, *, instrument_id: InstrumentId) -> int:
        return len(self._series(instrument_id))

    # -- CanonicalMarketDataSource ---------------------------------------

    async def trades(
        self,
        *,
        instrument_id: InstrumentId,
        since: datetime | None = None,
    ) -> tuple[TradeObservation, ...]:
        return ()

    async def candles(
        self,
        *,
        instrument_id: InstrumentId,
        limit: int,
    ) -> tuple[CandleObservation, ...]:
        series = self._series(instrument_id)
        return tuple(series[-limit:])

    async def top_of_book(
        self, *, instrument_id: InstrumentId
    ) -> TopOfBookObservation | None:
        return None

    async def order_book(
        self, *, instrument_id: InstrumentId
    ) -> OrderBookObservation | None:
        return None

    async def funding_open_interest(
        self, *, instrument_id: InstrumentId
    ) -> FundingOpenInterestObservation | None:
        return None

    async def news_events(
        self,
        *,
        instrument_id: InstrumentId,
        since: datetime,
    ) -> tuple[NewsEventObservation, ...]:
        return ()

    async def correlations(
        self, *, instrument_id: InstrumentId
    ) -> tuple[CorrelationObservation, ...]:
        return ()
