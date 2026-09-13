"""Durable append-only Decision Intelligence memory port."""

from __future__ import annotations

from typing import Protocol

from apps.decision_intelligence.domain.decision import (
    DecisionEvaluation,
    DecisionMemoryRecord,
    DecisionOutcome,
    MarketDecisionSnapshot,
    StrategyPortfolioDecision,
)


class DecisionMemoryStore(Protocol):
    async def append_snapshot(self, value: MarketDecisionSnapshot) -> None: ...

    async def append_decision(self, value: StrategyPortfolioDecision) -> None: ...

    async def append_outcome(
        self,
        *,
        workspace_id: str,
        user_id: int,
        value: DecisionOutcome,
    ) -> None: ...

    async def append_evaluation(
        self,
        *,
        workspace_id: str,
        user_id: int,
        value: DecisionEvaluation,
    ) -> None: ...

    async def rebuild(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
    ) -> DecisionMemoryRecord | None: ...

    async def list_memories(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[DecisionMemoryRecord, ...]: ...
