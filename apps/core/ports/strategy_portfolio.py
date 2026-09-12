"""Ports for canonical strategy runtime and allocation."""

from __future__ import annotations

from typing import Protocol

from apps.core.domain.intents import TradeIntent
from apps.core.domain.strategy_portfolio import StrategyEvaluationContext


class StrategyPlugin(Protocol):
    strategy_id: str
    version: str

    def evaluate(
        self,
        context: StrategyEvaluationContext,
    ) -> TradeIntent | None:
        """Produce a canonical intent or no action; never submit orders."""

        ...


class PortfolioAllocationPolicy(Protocol):
    def allocate(
        self,
        intent: TradeIntent,
        context: StrategyEvaluationContext,
    ) -> TradeIntent | None:
        """Return allocated intent before Portfolio Risk evaluates it."""

        ...
