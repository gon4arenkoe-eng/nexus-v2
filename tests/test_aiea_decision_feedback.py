from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from apps.aiea.application.decision_feedback import DecisionMemoryToAIEAService
from apps.aiea.domain.research import FalsificationCheck, ResearchEvidenceKind
from apps.decision_intelligence.domain.decision import (
    DecisionErrorClass,
    DecisionEvaluation,
    DecisionMemoryRecord,
    DecisionOutcome,
    DecisionState,
    MarketDecisionSnapshot,
    StrategyAllocationRecommendation,
    StrategyPortfolioDecision,
)
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 22, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(VenueId("SIM"), "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)


def _record(*, research_required: bool = True) -> DecisionMemoryRecord:
    snapshot = MarketDecisionSnapshot(
        "snap-1", "ws-1", 7, NOW, "market-hash", NOW, (INSTRUMENT,), "CURRENT",
        Decimal("0.9"), Decimal("0.1"), evidence_refs=("market:1",),
    )
    decision = StrategyPortfolioDecision(
        "decision-1", "snap-1", "ws-1", 7, NOW, DecisionState.REBALANCE,
        "obj", "1", Decimal("0.8"), Decimal("0.2"),
        (StrategyAllocationRecommendation(
            "trend", "1", Decimal("0.3"), Decimal("0.5"), Decimal("0.8"),
            Decimal("0.1"), Decimal("0.1"), reason_codes=("score",),
        ),), ("portfolio",), "decision-v1", ("decision:1",),
    )
    outcome = DecisionOutcome(
        "outcome-1", "decision-1", NOW, Decimal("-50"), Decimal("-0.5"),
        Decimal("1"), Decimal("0"), Decimal("0.1"), "ledger:1",
    )
    evaluation = DecisionEvaluation(
        "evaluation-1", "decision-1", "outcome-1", NOW,
        Decimal("0.8"), Decimal("0.3"), Decimal("0.8"), Decimal("0.2"),
        Decimal("0.8"), Decimal("0.9"), Decimal("0.9"),
        DecisionErrorClass.STRATEGY_SELECTION_ERROR,
        lesson_candidate="Strategy selection failed in this observed context.",
        research_required=research_required,
        evidence_refs=("evaluator:1",),
    )
    return DecisionMemoryRecord("memory-1", snapshot, decision, outcome, evaluation)


class Memory:
    def __init__(self, record): self.record = record
    async def rebuild(self, **kwargs): return self.record


class ResearchStore:
    def __init__(self):
        self.snapshots = []
        self.evidence = []
        self.memory = []
        self.hypotheses = []
    async def append_snapshot(self, value): self.snapshots.append(value)
    async def append_evidence(self, value): self.evidence.append(value)
    async def append_memory(self, value): self.memory.append(value)
    async def append_hypothesis(self, value): self.hypotheses.append(value)


def test_feedback_publishes_trade_lesson_snapshot_and_falsification_first_hypothesis() -> None:
    async def scenario():
        research = ResearchStore()
        service = DecisionMemoryToAIEAService(
            memory=Memory(_record()), research=research  # type: ignore[arg-type]
        )
        result = await service.publish(
            workspace_id="ws-1", user_id=7, decision_id="decision-1", observed_at=NOW,
        )
        return result, research
    result, research = asyncio.run(scenario())
    assert [item.kind for item in research.evidence] == [ResearchEvidenceKind.TRADE, ResearchEvidenceKind.LESSON]
    assert result.knowledge_snapshot.evidence_ids == tuple(item.evidence_id for item in research.evidence)
    assert result.hypothesis is not None and result.lesson_memory is not None
    assert {item.check for item in result.hypothesis.criteria} == set(FalsificationCheck)
    assert len(research.hypotheses) == 1 and len(research.memory) == 1


def test_feedback_without_research_requirement_does_not_seed_hypothesis() -> None:
    async def scenario():
        research = ResearchStore()
        service = DecisionMemoryToAIEAService(
            memory=Memory(_record(research_required=False)), research=research  # type: ignore[arg-type]
        )
        result = await service.publish(
            workspace_id="ws-1", user_id=7, decision_id="decision-1", observed_at=NOW,
        )
        return result, research
    result, research = asyncio.run(scenario())
    assert result.hypothesis is None and result.lesson_memory is None
    assert len(research.evidence) == 2 and len(research.snapshots) == 1
    assert not research.hypotheses and not research.memory


def test_aiea_feedback_module_has_no_execution_or_venue_write_dependency() -> None:
    from pathlib import Path
    source = Path("apps/aiea/application/decision_feedback.py").read_text()
    forbidden = ("ExecutionCoordinator", "VenueAdapter", "place_order", "cancel_order", "credentials")
    assert all(item not in source for item in forbidden)


def test_calibration_summary_becomes_context_scoped_aiea_model_evidence() -> None:
    from apps.aiea.application.decision_feedback import DecisionCalibrationToAIEAService

    class ListMemory(Memory):
        async def list_memories(self, **kwargs): return (self.record,)

    async def scenario():
        research = ResearchStore()
        service = DecisionCalibrationToAIEAService(
            memory=ListMemory(_record()), research=research  # type: ignore[arg-type]
        )
        evidence = await service.publish_summary(
            workspace_id="ws-1", user_id=7, observed_at=NOW,
            context_filter={"regime": "TRENDING_UP"},
        )
        return evidence, research

    evidence, research = asyncio.run(scenario())
    assert evidence.kind is ResearchEvidenceKind.MODEL
    assert evidence.payload["context_filter"] == {"regime": "TRENDING_UP"}
    assert research.evidence == [evidence]


def test_feedback_rejects_noncanonical_observation_timestamp() -> None:
    from datetime import timedelta
    import pytest
    from apps.aiea.application.decision_feedback import DecisionFeedbackError

    async def scenario():
        research = ResearchStore()
        service = DecisionMemoryToAIEAService(
            memory=Memory(_record()), research=research  # type: ignore[arg-type]
        )
        with pytest.raises(DecisionFeedbackError, match="immutable evaluation timestamp"):
            await service.publish(
                workspace_id="ws-1", user_id=7, decision_id="decision-1",
                observed_at=NOW + timedelta(seconds=1),
            )
    asyncio.run(scenario())


def test_aiea_learning_loop_module_has_no_execution_or_venue_write_dependency() -> None:
    from pathlib import Path
    source = Path("apps/aiea/application/decision_learning_loop.py").read_text()
    forbidden = ("ExecutionCoordinator", "VenueAdapter", "place_order", "cancel_order")
    assert all(item not in source for item in forbidden)
