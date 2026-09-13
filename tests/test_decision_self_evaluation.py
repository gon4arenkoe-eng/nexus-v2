from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from apps.decision_intelligence.application.self_evaluation import (
    DecisionCalibrationService,
    DeterministicDecisionSelfEvaluationService,
)
from apps.decision_intelligence.domain.decision import (
    DecisionErrorClass,
    DecisionMemoryRecord,
    DecisionOutcome,
    DecisionState,
    MarketDecisionSnapshot,
    StrategyAllocationRecommendation,
    StrategyPortfolioDecision,
)
from apps.decision_intelligence.domain.self_evaluation import DecisionEvaluationSignals
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 21, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(VenueId("SIM"), "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)


def _record(*, realized_r: str = "-0.8", confidence: str = "0.80") -> DecisionMemoryRecord:
    snapshot = MarketDecisionSnapshot(
        snapshot_id="snap-1", workspace_id="ws-1", user_id=7, created_at=NOW,
        market_context_hash="market-hash", market_context_as_of=NOW,
        instruments=(INSTRUMENT,), data_quality_state="CURRENT",
        data_quality_score=Decimal("0.90"), market_uncertainty=Decimal("0.10"),
        available_strategy_versions=("trend@1",), evidence_refs=("market:1",),
    )
    decision = StrategyPortfolioDecision(
        decision_id="decision-1", snapshot_id="snap-1", workspace_id="ws-1", user_id=7,
        created_at=NOW, state=DecisionState.REBALANCE, objective_id="obj", objective_version="1",
        portfolio_confidence=Decimal(confidence), portfolio_uncertainty=Decimal("0.20"),
        allocations=(StrategyAllocationRecommendation(
            strategy_id="trend", strategy_version="1", target_weight=Decimal("0.30"),
            max_weight=Decimal("0.50"), confidence=Decimal("0.80"),
            expected_contribution=Decimal("0.10"), expected_risk_contribution=Decimal("0.10"),
            reason_codes=("score",),
        ),), reason_codes=("portfolio",), decision_policy_version="decision-v1",
        evidence_refs=("decision:1",),
    )
    outcome = DecisionOutcome(
        outcome_id="outcome-1", decision_id="decision-1", evaluated_at=NOW,
        realized_pnl=Decimal("-80"), realized_r_multiple=Decimal(realized_r),
        fees=Decimal("2"), funding=Decimal("0"), slippage=Decimal("0.1"),
        execution_quality_ref="ledger:1",
    )
    return DecisionMemoryRecord("decision-memory:decision-1", snapshot, decision, outcome)


class Memory:
    def __init__(self, record): self.record = record
    async def rebuild(self, **kwargs): return self.record
    async def append_evaluation(self, *, workspace_id, user_id, value):
        self.record = DecisionMemoryRecord(
            self.record.memory_id, self.record.snapshot, self.record.decision,
            self.record.outcome, value,
        )


def test_self_evaluation_fails_closed_on_missing_independent_signals() -> None:
    async def scenario():
        memory = Memory(_record())
        service = DeterministicDecisionSelfEvaluationService(memory=memory)  # type: ignore[arg-type]
        return await service.evaluate(
            workspace_id="ws-1", user_id=7, decision_id="decision-1",
            evaluation_id="evaluation-1", evaluated_at=NOW,
        )
    evaluation = asyncio.run(scenario())
    assert evaluation.primary_error_class is DecisionErrorClass.INSUFFICIENT_EVIDENCE
    assert evaluation.research_required is True
    assert evaluation.confidence_calibration == Decimal("0.20")


def test_self_evaluation_classifies_low_strategy_quality_without_blaming_execution() -> None:
    async def scenario():
        memory = Memory(_record(confidence="0.40"))
        service = DeterministicDecisionSelfEvaluationService(memory=memory)  # type: ignore[arg-type]
        signals = DecisionEvaluationSignals(
            market_model_accuracy=Decimal("0.85"),
            strategy_selection_quality=Decimal("0.25"),
            allocation_quality=Decimal("0.80"),
            timing_quality=Decimal("0.75"),
            execution_quality=Decimal("0.95"),
            evidence_refs=("evaluator:strategy",),
        )
        return await service.evaluate(
            workspace_id="ws-1", user_id=7, decision_id="decision-1",
            evaluation_id="evaluation-1", evaluated_at=NOW, signals=signals,
        )
    evaluation = asyncio.run(scenario())
    assert evaluation.primary_error_class is DecisionErrorClass.STRATEGY_SELECTION_ERROR
    assert DecisionErrorClass.EXECUTION_ERROR not in evaluation.secondary_error_classes
    assert "evaluator:strategy" in evaluation.evidence_refs


def test_calibration_summary_reports_error_cost_and_brier_score() -> None:
    async def evaluated(realized_r: str, confidence: str, evaluation_id: str):
        memory = Memory(_record(realized_r=realized_r, confidence=confidence))
        service = DeterministicDecisionSelfEvaluationService(memory=memory)  # type: ignore[arg-type]
        signals = DecisionEvaluationSignals(
            market_model_accuracy=Decimal("0.90"), strategy_selection_quality=Decimal("0.90"),
            allocation_quality=Decimal("0.90"), timing_quality=Decimal("0.90"),
            execution_quality=Decimal("0.90"),
        )
        await service.evaluate(
            workspace_id="ws-1", user_id=7, decision_id="decision-1",
            evaluation_id=evaluation_id, evaluated_at=NOW, signals=signals,
        )
        return memory.record
    first = asyncio.run(evaluated("1.0", "0.80", "eval-1"))
    second = asyncio.run(evaluated("-1.0", "0.80", "eval-2"))
    # give the second record a distinct immutable decision id for aggregation semantics
    object.__setattr__(second.decision, "decision_id", "decision-2")
    object.__setattr__(second.outcome, "decision_id", "decision-2")
    object.__setattr__(second.evaluation, "decision_id", "decision-2")
    summary = DecisionCalibrationService().summarize(
        workspace_id="ws-1", user_id=7, records=(first, second), evaluated_at=NOW,
    )
    assert summary.decision_count == 2
    assert summary.winning_decisions == 1 and summary.losing_decisions == 1
    assert summary.brier_score == Decimal("0.34")
    assert summary.average_confidence_calibration == Decimal("0.50")


def test_calibration_can_slice_exact_market_state_tags() -> None:
    async def evaluated(realized_r: str, tag: str, decision_id: str):
        memory = Memory(_record(realized_r=realized_r, confidence="0.40"))
        object.__setattr__(memory.record.snapshot, "market_state_tags", {"regime": tag})
        object.__setattr__(memory.record.decision, "decision_id", decision_id)
        object.__setattr__(memory.record.outcome, "decision_id", decision_id)
        service = DeterministicDecisionSelfEvaluationService(memory=memory)  # type: ignore[arg-type]
        signals = DecisionEvaluationSignals(
            market_model_accuracy=Decimal("0.9"), strategy_selection_quality=Decimal("0.9"),
            allocation_quality=Decimal("0.9"), timing_quality=Decimal("0.9"), execution_quality=Decimal("0.9"),
        )
        await service.evaluate(
            workspace_id="ws-1", user_id=7, decision_id=decision_id,
            evaluation_id=f"eval-{decision_id}", evaluated_at=NOW, signals=signals,
        )
        return memory.record
    trending = asyncio.run(evaluated("1.0", "TRENDING_UP", "d-1"))
    ranging = asyncio.run(evaluated("-1.0", "RANGING", "d-2"))
    summary = DecisionCalibrationService().summarize(
        workspace_id="ws-1", user_id=7, records=(trending, ranging), evaluated_at=NOW,
        context_filter={"regime": "RANGING"},
    )
    assert summary.decision_count == 1
    assert summary.average_realized_r == Decimal("-1.0")
