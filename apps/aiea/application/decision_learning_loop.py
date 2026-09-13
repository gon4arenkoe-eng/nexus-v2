"""Bounded DecisionOutcome -> Evaluation -> AIEA feedback orchestration.

This loop stops at research evidence/hypothesis generation. It cannot create a
trading candidate, change strategy runtime state, promote anything, or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.aiea.application.decision_feedback import (
    DecisionFeedbackCycleResult,
    DecisionMemoryToAIEAService,
)
from apps.aiea.ports.research import ResearchRecordStore
from apps.decision_intelligence.application.self_evaluation import (
    DeterministicDecisionSelfEvaluationService,
)
from apps.decision_intelligence.domain.decision import DecisionEvaluation
from apps.decision_intelligence.domain.self_evaluation import DecisionEvaluationSignals
from apps.decision_intelligence.ports.memory import DecisionMemoryStore


@dataclass(frozen=True, slots=True)
class DecisionLearningCycleResult:
    evaluation: DecisionEvaluation
    feedback: DecisionFeedbackCycleResult


class DecisionLearningLoopService:
    """Close one evaluated feedback cycle without granting live authority."""

    def __init__(self, *, memory: DecisionMemoryStore, research: ResearchRecordStore) -> None:
        self._evaluation = DeterministicDecisionSelfEvaluationService(memory=memory)
        self._feedback = DecisionMemoryToAIEAService(memory=memory, research=research)

    async def run(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
        evaluation_id: str,
        evaluated_at: datetime,
        signals: DecisionEvaluationSignals | None = None,
    ) -> DecisionLearningCycleResult:
        evaluation = await self._evaluation.evaluate(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
            evaluation_id=evaluation_id,
            evaluated_at=evaluated_at,
            signals=signals,
        )
        feedback = await self._feedback.publish(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
            observed_at=evaluated_at,
        )
        return DecisionLearningCycleResult(evaluation=evaluation, feedback=feedback)
