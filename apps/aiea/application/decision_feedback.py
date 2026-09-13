"""Read-only Decision Memory -> AIEA research evidence feedback bridge.

The bridge can seed research hypotheses, but it cannot create candidates,
promote strategies, access secrets, or invoke execution/venue writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json

from apps.aiea.domain.research import (
    FalsificationCheck,
    FalsificationCriterion,
    Hypothesis,
    KnowledgeSnapshot,
    MANDATORY_FALSIFICATION_CHECKS,
    ResearchEvidence,
    ResearchEvidenceKind,
    ResearchMemoryEntry,
)
from apps.aiea.ports.research import ResearchRecordStore
from apps.decision_intelligence.domain.decision import DecisionMemoryRecord
from apps.decision_intelligence.ports.memory import DecisionMemoryStore


class DecisionFeedbackError(ValueError):
    """Decision feedback is incomplete, cross-owned, or not evaluated."""


@dataclass(frozen=True, slots=True)
class DecisionFeedbackCycleResult:
    cycle_id: str
    trade_evidence: ResearchEvidence
    lesson_evidence: ResearchEvidence
    knowledge_snapshot: KnowledgeSnapshot
    lesson_memory: ResearchMemoryEntry | None
    hypothesis: Hypothesis | None


class DecisionMemoryToAIEAService:
    """Publish evaluated decision history into AIEA with deterministic lineage."""

    def __init__(self, *, memory: DecisionMemoryStore, research: ResearchRecordStore) -> None:
        self._memory = memory
        self._research = research

    async def publish(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
        observed_at: datetime,
    ) -> DecisionFeedbackCycleResult:
        record = await self._memory.rebuild(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
        )
        if record is None or record.outcome is None or record.evaluation is None:
            raise DecisionFeedbackError(
                "AIEA feedback requires durable decision, outcome, and evaluation"
            )
        if record.decision.workspace_id != workspace_id or record.decision.user_id != user_id:
            raise DecisionFeedbackError("Decision Memory feedback ownership mismatch")

        if observed_at != record.evaluation.evaluated_at:
            raise DecisionFeedbackError(
                "feedback observed_at must equal immutable evaluation timestamp"
            )
        cycle_id = _id("decision-feedback", record.evaluation.evaluation_id)
        trade_payload = _trade_payload(record)
        trade_hash = _hash_payload(trade_payload)
        trade = ResearchEvidence(
            evidence_id=_id("decision-trade", record.outcome.outcome_id),
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ResearchEvidenceKind.TRADE,
            observed_at=observed_at,
            content_hash=trade_hash,
            source_ref=f"decision-memory:{decision_id}",
            payload=trade_payload,
        )
        lesson_payload = _lesson_payload(record, cycle_id=cycle_id)
        lesson_hash = _hash_payload(lesson_payload)
        lesson = ResearchEvidence(
            evidence_id=_id("decision-lesson", record.evaluation.evaluation_id),
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ResearchEvidenceKind.LESSON,
            observed_at=observed_at,
            content_hash=lesson_hash,
            source_ref=f"decision-evaluation:{record.evaluation.evaluation_id}",
            payload=lesson_payload,
        )
        snapshot_hash = _digest(trade_hash, lesson_hash, record.snapshot.market_context_hash)
        snapshot = KnowledgeSnapshot(
            snapshot_id=_id("decision-knowledge", record.evaluation.evaluation_id),
            workspace_id=workspace_id,
            user_id=user_id,
            created_at=observed_at,
            evidence_ids=(trade.evidence_id, lesson.evidence_id),
            content_hash=snapshot_hash,
        )

        hypothesis = None
        memory_entry = None
        if record.evaluation.research_required:
            hypothesis = _hypothesis(record=record, snapshot=snapshot, observed_at=observed_at)
            memory_entry = ResearchMemoryEntry(
                memory_id=_id("decision-memory-lesson", record.evaluation.evaluation_id),
                workspace_id=workspace_id,
                user_id=user_id,
                created_at=observed_at,
                snapshot_id=snapshot.snapshot_id,
                hypothesis_id=hypothesis.hypothesis_id,
                experiment_id=None,
                candidate_id=None,
                lesson=record.evaluation.lesson_candidate
                or f"Investigate {record.evaluation.primary_error_class.value}",
                provenance_hash=_digest(
                    cycle_id,
                    trade.content_hash,
                    lesson.content_hash,
                    snapshot.content_hash,
                    hypothesis.hypothesis_id,
                ),
                parent_memory_id=None,
            )

        await self._research.append_evidence(trade)
        await self._research.append_evidence(lesson)
        await self._research.append_snapshot(snapshot)
        if memory_entry is not None and hypothesis is not None:
            await self._research.append_memory(memory_entry)
            await self._research.append_hypothesis(hypothesis)
        return DecisionFeedbackCycleResult(
            cycle_id=cycle_id,
            trade_evidence=trade,
            lesson_evidence=lesson,
            knowledge_snapshot=snapshot,
            lesson_memory=memory_entry,
            hypothesis=hypothesis,
        )


def _hypothesis(
    *,
    record: DecisionMemoryRecord,
    snapshot: KnowledgeSnapshot,
    observed_at: datetime,
) -> Hypothesis:
    evaluation = record.evaluation
    if evaluation is None:  # pragma: no cover - caller guard
        raise DecisionFeedbackError("hypothesis requires evaluation")
    checks = tuple(
        FalsificationCriterion(
            check=check,
            minimum_score=Decimal("0.70"),
            rationale=(
                "predeclared Decision feedback hypothesis kill criterion; "
                f"must pass {check.value} before shadow readiness"
            ),
        )
        for check in sorted(MANDATORY_FALSIFICATION_CHECKS, key=lambda item: item.value)
    )
    return Hypothesis(
        hypothesis_id=_id("decision-hypothesis", evaluation.evaluation_id),
        workspace_id=record.decision.workspace_id,
        user_id=record.decision.user_id,
        snapshot_id=snapshot.snapshot_id,
        statement=(
            f"Investigate whether {evaluation.primary_error_class.value} is a repeatable "
            f"failure mode for decision policy {record.decision.decision_policy_version}."
        ),
        expected_effect=(
            "A challenger must reduce the observed error without degrading costs, OOS, "
            "walk-forward, regime stability, or holdout integrity."
        ),
        created_at=observed_at,
        criteria=checks,
    )


def _trade_payload(record: DecisionMemoryRecord) -> dict[str, object]:
    outcome = record.outcome
    evaluation = record.evaluation
    if outcome is None or evaluation is None:  # pragma: no cover
        raise DecisionFeedbackError("trade payload requires evaluated outcome")
    return {
        "decision_id": record.decision.decision_id,
        "snapshot_id": record.snapshot.snapshot_id,
        "decision_policy_version": record.decision.decision_policy_version,
        "decision_state": record.decision.state.value,
        "portfolio_confidence": str(record.decision.portfolio_confidence),
        "portfolio_uncertainty": str(record.decision.portfolio_uncertainty),
        "market_state_tags": dict(record.snapshot.market_state_tags),
        "realized_pnl": str(outcome.realized_pnl),
        "realized_r_multiple": str(outcome.realized_r_multiple),
        "fees": str(outcome.fees),
        "funding": str(outcome.funding),
        "slippage": str(outcome.slippage),
        "execution_quality_ref": outcome.execution_quality_ref,
        "evaluation_id": evaluation.evaluation_id,
    }


def _lesson_payload(record: DecisionMemoryRecord, *, cycle_id: str) -> dict[str, object]:
    evaluation = record.evaluation
    if evaluation is None:  # pragma: no cover
        raise DecisionFeedbackError("lesson payload requires evaluation")
    return {
        "cycle_id": cycle_id,
        "decision_id": record.decision.decision_id,
        "evaluation_id": evaluation.evaluation_id,
        "primary_error_class": evaluation.primary_error_class.value,
        "secondary_error_classes": [item.value for item in evaluation.secondary_error_classes],
        "market_model_accuracy": str(evaluation.market_model_accuracy),
        "strategy_selection_quality": str(evaluation.strategy_selection_quality),
        "allocation_quality": str(evaluation.allocation_quality),
        "confidence_calibration": str(evaluation.confidence_calibration),
        "timing_quality": str(evaluation.timing_quality),
        "data_quality_impact": str(evaluation.data_quality_impact),
        "execution_quality": str(evaluation.execution_quality),
        "lesson_candidate": evaluation.lesson_candidate,
        "research_required": evaluation.research_required,
        "evidence_refs": list(evaluation.evidence_refs),
    }


def _id(prefix: str, identity: str) -> str:
    return f"{prefix}:{sha256(identity.encode('utf-8')).hexdigest()}"


def _digest(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


class DecisionCalibrationToAIEAService:
    """Publish aggregate self-calibration as research-only model evidence."""

    def __init__(self, *, memory: DecisionMemoryStore, research: ResearchRecordStore) -> None:
        self._memory = memory
        self._research = research

    async def publish_summary(
        self,
        *,
        workspace_id: str,
        user_id: int,
        observed_at: datetime,
        context_filter: dict[str, str] | None = None,
    ) -> ResearchEvidence:
        from apps.decision_intelligence.application.self_evaluation import DecisionCalibrationService

        records = await self._memory.list_memories(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        summary = DecisionCalibrationService().summarize(
            workspace_id=workspace_id,
            user_id=user_id,
            records=records,
            evaluated_at=observed_at,
            context_filter=context_filter,
        )
        payload: dict[str, object] = {
            "decision_count": summary.decision_count,
            "winning_decisions": summary.winning_decisions,
            "losing_decisions": summary.losing_decisions,
            "flat_decisions": summary.flat_decisions,
            "average_realized_r": str(summary.average_realized_r),
            "average_confidence_calibration": str(summary.average_confidence_calibration),
            "brier_score": str(summary.brier_score),
            "average_error_cost_r": str(summary.average_error_cost_r),
            "error_counts": {
                key.value: value for key, value in summary.error_counts.items()
            },
            "context_filter": dict(sorted((context_filter or {}).items())),
        }
        content_hash = _hash_payload(payload)
        context_digest = _hash_payload({"context_filter": payload["context_filter"]})
        evidence = ResearchEvidence(
            evidence_id=_id(
                "decision-calibration",
                f"{workspace_id}:{user_id}:{context_digest}:{content_hash}:{observed_at.isoformat()}",
            ),
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ResearchEvidenceKind.MODEL,
            observed_at=observed_at,
            content_hash=content_hash,
            source_ref=f"decision-calibration:{workspace_id}:{user_id}:{context_digest}",
            payload=payload,
        )
        await self._research.append_evidence(evidence)
        return evidence
