"""Research-only historical candle range port for deterministic AIEA replay."""
from __future__ import annotations
from typing import Protocol
from apps.intelligence.domain.market_context import CandleObservation
from packages.contracts.identities import InstrumentId

class HistoricalCandleRangeSource(Protocol):
    async def candles_between(self, *, instrument_id: InstrumentId, start_index: int, end_index: int) -> tuple[CandleObservation, ...]: ...
    async def bar_count(self, *, instrument_id: InstrumentId) -> int: ...
