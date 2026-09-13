"""Deterministic, evidence-bound DecisionOutcome self-evaluation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Mapping

from apps.decision_intelligence.domain.decision import (
    DecisionErrorClass,
    DecisionEvaluation,
    DecisionMemoryRecord,
)
from apps.decision_intelligence.domain.self_evaluation import (
    DecisionCalibrationSummary,
    DecisionEvaluationSignals,
)
from apps.decision_intelligence.ports.memory import DecisionMemoryStore

_ZERO = Decimal("0")
_HALF = Decimal("0.5")
_ONE = Decimal("1")


class DecisionSelfEvaluationError(ValueError):
    """Decision memory is incomplete, immutable, or cross-owned."""


class DeterministicDecisionSelfEvaluationService:
    """Create one immutable DecisionEvaluation from proven outcome evidence.

    PnL is never used to invent regime/selection/timing/execution accuracy.
    Independent signals must provide those scores. When they are absent the
    evaluator records INSUFFICIENT_EVIDENCE and requests research.
    """

    def __init__(self, *, memory: DecisionMemoryStore, quality_threshold: Decimal = Decimal("0.60")) -> None:
        if not isinstance(quality_threshold, Decimal) or not _ZERO <= quality_threshold <= _ONE:
            raise ValueError("quality_threshold must be Decimal between 0 and 1")
        self._memory = memory
        self._threshold = quality_threshold

    async def evaluate(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
        evaluation_id: str,
        evaluated_at: datetime,
        signals: DecisionEvaluationSignals | None = None,
    ) -> DecisionEvaluation:
        record = await self._memory.rebuild(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
        )
        if record is None or record.outcome is None:
            raise DecisionSelfEvaluationError("self-evaluation requires an attributed outcome")
        if record.evaluation is not None:
            if record.evaluation.evaluation_id != evaluation_id:
                raise DecisionSelfEvaluationError(
                    "outcome already has a different immutable evaluation"
                )
            return record.evaluation
        if record.decision.workspace_id != workspace_id or record.decision.user_id != user_id:
            raise DecisionSelfEvaluationError("decision memory ownership mismatch")

        evidence = signals or DecisionEvaluationSignals()
        neutral = _HALF
        metrics = {
            "market_model_accuracy": evidence.market_model_accuracy,
            "strategy_selection_quality": evidence.strategy_selection_quality,
            "allocation_quality": evidence.allocation_quality,
            "timing_quality": evidence.timing_quality,
            "execution_quality": evidence.execution_quality,
        }
        resolved = {name: neutral if value is None else value for name, value in metrics.items()}

        observed_success = _observed_success(record.outcome.realized_r_multiple)
        confidence_calibration = _ONE - abs(
            record.decision.portfolio_confidence - observed_success
        )
        data_quality_impact = record.snapshot.data_quality_score

        classified: list[tuple[DecisionErrorClass, Decimal]] = []
        mapping = (
            ("market_model_accuracy", DecisionErrorClass.REGIME_CLASSIFICATION_ERROR),
            ("strategy_selection_quality", DecisionErrorClass.STRATEGY_SELECTION_ERROR),
            ("allocation_quality", DecisionErrorClass.ALLOCATION_ERROR),
            ("timing_quality", DecisionErrorClass.TIMING_ERROR),
            ("execution_quality", DecisionErrorClass.EXECUTION_ERROR),
        )
        for name, error_class in mapping:
            value = metrics[name]
            if value is not None and value < self._threshold:
                classified.append((error_class, value))
        if data_quality_impact < self._threshold:
            classified.append((DecisionErrorClass.DATA_QUALITY_ERROR, data_quality_impact))
        if confidence_calibration < self._threshold:
            classified.append((DecisionErrorClass.RISK_ESTIMATION_ERROR, confidence_calibration))
        if not evidence.complete:
            classified.append((DecisionErrorClass.INSUFFICIENT_EVIDENCE, _ZERO))

        if classified:
            classified.sort(key=lambda item: (item[1], item[0].value))
            primary = classified[0][0]
            secondary = tuple(
                item[0]
                for item in classified[1:]
                if item[0] != primary
            )
        else:
            primary = DecisionErrorClass.NO_ERROR_DETECTED
            secondary = ()

        research_required = primary is not DecisionErrorClass.NO_ERROR_DETECTED or bool(secondary)
        lesson = _lesson(record=record, primary=primary, complete=evidence.complete)
        refs = tuple(
            sorted(
                set(record.decision.evidence_refs)
                .union(record.snapshot.evidence_refs)
                .union(record.outcome.reconciliation_evidence_refs)
                .union(evidence.evidence_refs)
                .union(
                    (record.outcome.execution_quality_ref,)
                    if record.outcome.execution_quality_ref is not None
                    else ()
                )
            )
        )
        evaluation = DecisionEvaluation(
            evaluation_id=evaluation_id,
            decision_id=decision_id,
            outcome_id=record.outcome.outcome_id,
            evaluated_at=evaluated_at,
            market_model_accuracy=resolved["market_model_accuracy"],
            strategy_selection_quality=resolved["strategy_selection_quality"],
            allocation_quality=resolved["allocation_quality"],
            confidence_calibration=confidence_calibration,
            timing_quality=resolved["timing_quality"],
            data_quality_impact=data_quality_impact,
            execution_quality=resolved["execution_quality"],
            primary_error_class=primary,
            secondary_error_classes=secondary,
            lesson_candidate=lesson,
            research_required=research_required,
            evidence_refs=refs,
        )
        await self._memory.append_evaluation(
            workspace_id=workspace_id,
            user_id=user_id,
            value=evaluation,
        )
        return evaluation


class DecisionCalibrationService:
    """Aggregate immutable self-evaluations without changing the evaluator."""

    def summarize(
        self,
        *,
        workspace_id: str,
        user_id: int,
        records: tuple[DecisionMemoryRecord, ...],
        evaluated_at: datetime,
        context_filter: Mapping[str, str] | None = None,
    ) -> DecisionCalibrationSummary:
        context_filter = dict(context_filter or {})
        complete = tuple(
            record
            for record in records
            if record.outcome is not None
            and record.evaluation is not None
            and all(record.snapshot.market_state_tags.get(key) == value for key, value in context_filter.items())
        )
        if not complete:
            return DecisionCalibrationSummary(
                workspace_id=workspace_id,
                user_id=user_id,
                evaluated_at=evaluated_at,
                decision_count=0,
                winning_decisions=0,
                losing_decisions=0,
                flat_decisions=0,
                average_realized_r=_ZERO,
                average_confidence_calibration=_ZERO,
                brier_score=_ZERO,
                average_error_cost_r=_ZERO,
                error_counts={},
            )
        for record in complete:
            if record.decision.workspace_id != workspace_id or record.decision.user_id != user_id:
                raise DecisionSelfEvaluationError("calibration records cannot cross owners")

        count = Decimal(len(complete))
        r_values = tuple(record.outcome.realized_r_multiple for record in complete if record.outcome is not None)
        observed = tuple(_observed_success(value) for value in r_values)
        confidences = tuple(record.decision.portfolio_confidence for record in complete)
        calibration = tuple(
            record.evaluation.confidence_calibration
            for record in complete
            if record.evaluation is not None
        )
        errors = Counter(
            record.evaluation.primary_error_class
            for record in complete
            if record.evaluation is not None
            and record.evaluation.primary_error_class is not DecisionErrorClass.NO_ERROR_DETECTED
        )
        error_costs = tuple(
            record.outcome.realized_r_multiple
            for record in complete
            if record.outcome is not None
            and record.evaluation is not None
            and record.evaluation.primary_error_class is not DecisionErrorClass.NO_ERROR_DETECTED
        )
        return DecisionCalibrationSummary(
            workspace_id=workspace_id,
            user_id=user_id,
            evaluated_at=evaluated_at,
            decision_count=len(complete),
            winning_decisions=sum(1 for value in r_values if value > _ZERO),
            losing_decisions=sum(1 for value in r_values if value < _ZERO),
            flat_decisions=sum(1 for value in r_values if value == _ZERO),
            average_realized_r=sum(r_values, _ZERO) / count,
            average_confidence_calibration=sum(calibration, _ZERO) / count,
            brier_score=sum(
                ((confidence - actual) ** 2 for confidence, actual in zip(confidences, observed)),
                _ZERO,
            ) / count,
            average_error_cost_r=(
                _ZERO
                if not error_costs
                else sum(error_costs, _ZERO) / Decimal(len(error_costs))
            ),
            error_counts=dict(errors),
        )


def _observed_success(realized_r: Decimal) -> Decimal:
    if realized_r > _ZERO:
        return _ONE
    if realized_r < _ZERO:
        return _ZERO
    return _HALF


def _lesson(
    *,
    record: DecisionMemoryRecord,
    primary: DecisionErrorClass,
    complete: bool,
) -> str:
    outcome = record.outcome
    if outcome is None:  # pragma: no cover - guarded by caller
        raise DecisionSelfEvaluationError("lesson requires outcome")
    digest = sha256(
        f"{record.decision.decision_id}|{outcome.outcome_id}|{primary.value}".encode("utf-8")
    ).hexdigest()[:12]
    evidence_state = "complete" if complete else "incomplete"
    return (
        f"decision={record.decision.decision_id}; primary_error={primary.value}; "
        f"realized_r={outcome.realized_r_multiple}; evidence={evidence_state}; ref={digest}"
    )
