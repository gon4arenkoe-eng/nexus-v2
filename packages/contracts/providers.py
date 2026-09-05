"""Canonical NEXUS V2 provider contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current timezone-aware canonical time."""
        ...


class IdProvider(Protocol):
    def next_id(self) -> str:
        """Return the next externally supplied canonical identifier."""
        ...
