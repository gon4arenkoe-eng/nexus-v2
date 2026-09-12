"""Read-only ports for canonical market observations."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.intelligence.domain.market_context import (
    CandleObservation,
    CorrelationObservation,
    FundingOpenInterestObservation,
    NewsEventObservation,
    OrderBookObservation,
    TopOfBookObservation,
    TradeObservation,
)
from packages.contracts.identities import InstrumentId


class CanonicalMarketDataSource(Protocol):
    """Read canonical observations without execution authority."""

    async def trades(
        self,
        *,
        instrument_id: InstrumentId,
        since: datetime | None = None,
    ) -> tuple[TradeObservation, ...]: ...

    async def candles(
        self,
        *,
        instrument_id: InstrumentId,
        limit: int,
    ) -> tuple[CandleObservation, ...]: ...

    async def top_of_book(
        self,
        *,
        instrument_id: InstrumentId,
    ) -> TopOfBookObservation | None: ...

    async def order_book(
        self,
        *,
        instrument_id: InstrumentId,
    ) -> OrderBookObservation | None: ...

    async def funding_open_interest(
        self,
        *,
        instrument_id: InstrumentId,
    ) -> FundingOpenInterestObservation | None: ...

    async def news_events(
        self,
        *,
        instrument_id: InstrumentId,
        since: datetime,
    ) -> tuple[NewsEventObservation, ...]: ...

    async def correlations(
        self,
        *,
        instrument_id: InstrumentId,
    ) -> tuple[CorrelationObservation, ...]: ...
