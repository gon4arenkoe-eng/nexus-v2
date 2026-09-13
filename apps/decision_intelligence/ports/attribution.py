"""Provider-neutral ports for DecisionOutcome attribution."""

from __future__ import annotations

from typing import Protocol

from apps.decision_intelligence.domain.attribution import (
    DecisionExecutionLink,
    ExecutionPlanLineage,
    LedgerAttributionEvent,
)


class DecisionExecutionLinkStore(Protocol):
    async def append(self, value: DecisionExecutionLink) -> None: ...

    async def list_for_decision(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
    ) -> tuple[DecisionExecutionLink, ...]: ...


class ExecutionPlanLineageReader(Protocol):
    async def list_for_intents(
        self,
        *,
        user_id: int,
        intent_ids: tuple[str, ...],
    ) -> tuple[ExecutionPlanLineage, ...]: ...


class LedgerAttributionReader(Protocol):
    async def list_for_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> tuple[LedgerAttributionEvent, ...]: ...
