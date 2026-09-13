"""Ports for optional LLM reasoning and immutable decision-memory storage."""

from __future__ import annotations

from typing import Protocol

from apps.decision_intelligence.domain.decision import (
    DecisionMemoryRecord,
    ReasoningRequest,
    ReasoningResult,
)


class ReasoningModelPort(Protocol):
    async def reason(self, request: ReasoningRequest) -> ReasoningResult: ...


class DecisionMemoryStore(Protocol):
    async def append(self, record: DecisionMemoryRecord) -> None: ...
