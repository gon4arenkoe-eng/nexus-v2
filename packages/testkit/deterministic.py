"""Deterministic NEXUS V2 test providers."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Iterable

from packages.contracts.primitives import normalize_utc_datetime


class DeterministicClock:
    def __init__(self, initial_time: datetime) -> None:
        self._current = normalize_utc_datetime(
            initial_time,
            field_name="initial_time",
        )

    def now(self) -> datetime:
        return self._current

    def set(self, value: datetime) -> None:
        self._current = normalize_utc_datetime(
            value,
            field_name="value",
        )

    def advance(self, delta: timedelta) -> None:
        if not isinstance(delta, timedelta):
            raise ValueError("delta must be timedelta")

        if delta < timedelta(0):
            raise ValueError("delta must be non-negative")

        self._current = normalize_utc_datetime(
            self._current + delta,
            field_name="current_time",
        )


class SequenceIdProvider:
    def __init__(self, values: Iterable[str]) -> None:
        self._values = deque(self._normalize(value) for value in values)

    @staticmethod
    def _normalize(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("id value must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError("id value must be non-empty")

        return normalized

    def next_id(self) -> str:
        if not self._values:
            raise RuntimeError("deterministic ID sequence exhausted")

        return self._values.popleft()
