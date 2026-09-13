from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from apps.aiea.application.decision_learning_loop import DecisionLearningLoopService
from apps.decision_intelligence.domain.self_evaluation import DecisionEvaluationSignals
from tests.test_aiea_decision_feedback import Memory, ResearchStore, _record

NOW = datetime(2026, 9, 13, 23, 0, tzinfo=UTC)


def test_learning_loop_closes_outcome_evaluation_lesson_hypothesis_without_execution() -> None:
    async def scenario():
        record = _record()
        object.__setattr__(record, "evaluation", None)
        memory = Memory(record)
        # feedback test Memory is read-only; add the DecisionMemoryStore write method for this scenario.
        async def append_evaluation(*, workspace_id, user_id, value):
            memory.record = type(memory.record)(
                memory.record.memory_id,
                memory.record.snapshot,
                memory.record.decision,
                memory.record.outcome,
                value,
            )
        memory.append_evaluation = append_evaluation  # type: ignore[attr-defined]
        research = ResearchStore()
        service = DecisionLearningLoopService(
            memory=memory, research=research  # type: ignore[arg-type]
        )
        result = await service.run(
            workspace_id="ws-1", user_id=7, decision_id="decision-1",
            evaluation_id="loop-evaluation-1", evaluated_at=NOW,
            signals=DecisionEvaluationSignals(
                market_model_accuracy=Decimal("0.9"),
                strategy_selection_quality=Decimal("0.2"),
                allocation_quality=Decimal("0.8"),
                timing_quality=Decimal("0.8"),
                execution_quality=Decimal("0.9"),
                evidence_refs=("external-evaluator:1",),
            ),
        )
        return result, research

    result, research = asyncio.run(scenario())
    assert result.evaluation.research_required is True
    assert result.feedback.hypothesis is not None
    assert len(research.evidence) == 2
    assert len(research.hypotheses) == 1
