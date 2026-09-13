"""Persistence adapter for append-only Decision Intelligence memory."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

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
from infra.persistence.repositories.decision_intelligence import (
    DecisionIntelligenceRecordRepository,
    DecisionStoredRecord,
)
from packages.contracts.identities import (
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_value(item) for item in value]
    return value


def _serialize(value: object) -> str:
    return json.dumps(
        _json_value(value),
        sort_keys=True,
        separators=(",", ":"),
    )


def _hash(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def _load(payload_json: str) -> dict[str, Any]:
    value = json.loads(payload_json)
    if not isinstance(value, dict):
        raise ValueError("Decision Intelligence payload must be an object")
    return value


def _instrument(value: Mapping[str, Any]) -> InstrumentId:
    venue = value.get("venue_id")
    if not isinstance(venue, Mapping):
        raise ValueError("instrument venue_id payload is invalid")
    return InstrumentId(
        venue_id=VenueId(str(venue["value"])),
        native_symbol=str(value["native_symbol"]),
        instrument_type=InstrumentType(str(value["instrument_type"])),
        asset_class=AssetClass(str(value["asset_class"])),
    )


def _snapshot(payload_json: str) -> MarketDecisionSnapshot:
    value = _load(payload_json)
    return MarketDecisionSnapshot(
        snapshot_id=str(value["snapshot_id"]),
        workspace_id=str(value["workspace_id"]),
        user_id=int(value["user_id"]),
        created_at=datetime.fromisoformat(str(value["created_at"])),
        market_context_hash=str(value["market_context_hash"]),
        market_context_as_of=datetime.fromisoformat(str(value["market_context_as_of"])),
        instruments=tuple(_instrument(item) for item in value["instruments"]),
        data_quality_state=str(value["data_quality_state"]),
        data_quality_score=Decimal(str(value["data_quality_score"])),
        market_uncertainty=Decimal(str(value["market_uncertainty"])),
        active_blockers=tuple(str(item) for item in value.get("active_blockers", [])),
        available_strategy_versions=tuple(
            str(item) for item in value.get("available_strategy_versions", [])
        ),
        decision_policy_version=str(value["decision_policy_version"]),
        evidence_refs=tuple(str(item) for item in value.get("evidence_refs", [])),
    )


def _allocation(value: Mapping[str, Any]) -> StrategyAllocationRecommendation:
    parameter_set_ref = value.get("parameter_set_ref")
    return StrategyAllocationRecommendation(
        strategy_id=str(value["strategy_id"]),
        strategy_version=str(value["strategy_version"]),
        target_weight=Decimal(str(value["target_weight"])),
        max_weight=Decimal(str(value["max_weight"])),
        confidence=Decimal(str(value["confidence"])),
        expected_contribution=Decimal(str(value["expected_contribution"])),
        expected_risk_contribution=Decimal(str(value["expected_risk_contribution"])),
        parameter_set_ref=None if parameter_set_ref is None else str(parameter_set_ref),
        reason_codes=tuple(str(item) for item in value.get("reason_codes", [])),
    )


def _decision(payload_json: str) -> StrategyPortfolioDecision:
    value = _load(payload_json)
    return StrategyPortfolioDecision(
        decision_id=str(value["decision_id"]),
        snapshot_id=str(value["snapshot_id"]),
        workspace_id=str(value["workspace_id"]),
        user_id=int(value["user_id"]),
        created_at=datetime.fromisoformat(str(value["created_at"])),
        state=DecisionState(str(value["state"])),
        objective_id=str(value["objective_id"]),
        objective_version=str(value["objective_version"]),
        portfolio_confidence=Decimal(str(value["portfolio_confidence"])),
        portfolio_uncertainty=Decimal(str(value["portfolio_uncertainty"])),
        allocations=tuple(_allocation(item) for item in value.get("allocations", [])),
        reason_codes=tuple(str(item) for item in value["reason_codes"]),
        decision_policy_version=str(value["decision_policy_version"]),
        evidence_refs=tuple(str(item) for item in value.get("evidence_refs", [])),
    )


def _outcome(payload_json: str) -> DecisionOutcome:
    value = _load(payload_json)
    execution_quality_ref = value.get("execution_quality_ref")
    return DecisionOutcome(
        outcome_id=str(value["outcome_id"]),
        decision_id=str(value["decision_id"]),
        evaluated_at=datetime.fromisoformat(str(value["evaluated_at"])),
        realized_pnl=Decimal(str(value["realized_pnl"])),
        realized_r_multiple=Decimal(str(value["realized_r_multiple"])),
        fees=Decimal(str(value["fees"])),
        funding=Decimal(str(value["funding"])),
        slippage=Decimal(str(value["slippage"])),
        execution_quality_ref=(
            None if execution_quality_ref is None else str(execution_quality_ref)
        ),
        reconciliation_evidence_refs=tuple(
            str(item) for item in value.get("reconciliation_evidence_refs", [])
        ),
    )


def _evaluation(payload_json: str) -> DecisionEvaluation:
    value = _load(payload_json)
    lesson_candidate = value.get("lesson_candidate")
    return DecisionEvaluation(
        evaluation_id=str(value["evaluation_id"]),
        decision_id=str(value["decision_id"]),
        outcome_id=str(value["outcome_id"]),
        evaluated_at=datetime.fromisoformat(str(value["evaluated_at"])),
        market_model_accuracy=Decimal(str(value["market_model_accuracy"])),
        strategy_selection_quality=Decimal(str(value["strategy_selection_quality"])),
        allocation_quality=Decimal(str(value["allocation_quality"])),
        confidence_calibration=Decimal(str(value["confidence_calibration"])),
        timing_quality=Decimal(str(value["timing_quality"])),
        data_quality_impact=Decimal(str(value["data_quality_impact"])),
        execution_quality=Decimal(str(value["execution_quality"])),
        primary_error_class=DecisionErrorClass(str(value["primary_error_class"])),
        secondary_error_classes=tuple(
            DecisionErrorClass(str(item))
            for item in value.get("secondary_error_classes", [])
        ),
        lesson_candidate=None if lesson_candidate is None else str(lesson_candidate),
        research_required=bool(value["research_required"]),
        evidence_refs=tuple(str(item) for item in value.get("evidence_refs", [])),
    )


class DecisionMemoryPersistenceStore:
    """Append-only store and deterministic DecisionMemoryRecord projection."""

    def __init__(self, repository: DecisionIntelligenceRecordRepository) -> None:
        self._repository = repository

    async def append_snapshot(self, value: MarketDecisionSnapshot) -> None:
        await self._append(
            value,
            record_type="snapshot",
            record_id=value.snapshot_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
        )

    async def append_decision(self, value: StrategyPortfolioDecision) -> None:
        snapshot = await self._repository.get(
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            record_type="snapshot",
            record_id=value.snapshot_id,
        )
        if snapshot is None:
            raise ValueError("decision requires existing same-owner snapshot")
        await self._append(
            value,
            record_type="decision",
            record_id=value.decision_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
            parent_record_id=value.snapshot_id,
        )

    async def append_outcome(
        self,
        *,
        workspace_id: str,
        user_id: int,
        value: DecisionOutcome,
    ) -> None:
        decision = await self._repository.get(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="decision",
            record_id=value.decision_id,
        )
        if decision is None:
            raise ValueError("outcome requires existing same-owner decision")
        children = await self._repository.list_children(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="outcome",
            parent_record_id=value.decision_id,
        )
        if children and all(item.record_id != value.outcome_id for item in children):
            raise ValueError("decision already has a different immutable outcome")
        await self._append(
            value,
            record_type="outcome",
            record_id=value.outcome_id,
            workspace_id=workspace_id,
            user_id=user_id,
            created_at=value.evaluated_at,
            parent_record_id=value.decision_id,
        )

    async def append_evaluation(
        self,
        *,
        workspace_id: str,
        user_id: int,
        value: DecisionEvaluation,
    ) -> None:
        outcome = await self._repository.get(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="outcome",
            record_id=value.outcome_id,
        )
        if outcome is None:
            raise ValueError("evaluation requires existing same-owner outcome")
        persisted_outcome = _outcome(outcome.payload_json)
        if persisted_outcome.decision_id != value.decision_id:
            raise ValueError("evaluation/outcome decision lineage mismatch")
        children = await self._repository.list_children(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="evaluation",
            parent_record_id=value.outcome_id,
        )
        if children and all(item.record_id != value.evaluation_id for item in children):
            raise ValueError("outcome already has a different immutable evaluation")
        await self._append(
            value,
            record_type="evaluation",
            record_id=value.evaluation_id,
            workspace_id=workspace_id,
            user_id=user_id,
            created_at=value.evaluated_at,
            parent_record_id=value.outcome_id,
        )

    async def rebuild(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
    ) -> DecisionMemoryRecord | None:
        decision_record = await self._repository.get(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="decision",
            record_id=decision_id,
        )
        if decision_record is None:
            return None
        if decision_record.parent_record_id is None:
            raise ValueError("persisted decision is missing snapshot lineage")
        snapshot_record = await self._repository.get(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="snapshot",
            record_id=decision_record.parent_record_id,
        )
        if snapshot_record is None:
            raise ValueError("persisted decision snapshot is missing")

        outcome_records = await self._repository.list_children(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="outcome",
            parent_record_id=decision_id,
        )
        if len(outcome_records) > 1:
            raise ValueError("multiple outcomes found for immutable decision")
        outcome = None if not outcome_records else _outcome(outcome_records[0].payload_json)

        evaluation = None
        if outcome is not None:
            evaluation_records = await self._repository.list_children(
                workspace_id=workspace_id,
                user_id=user_id,
                record_type="evaluation",
                parent_record_id=outcome.outcome_id,
            )
            if len(evaluation_records) > 1:
                raise ValueError("multiple evaluations found for immutable outcome")
            if evaluation_records:
                evaluation = _evaluation(evaluation_records[0].payload_json)

        return DecisionMemoryRecord(
            memory_id=f"decision-memory:{decision_id}",
            snapshot=_snapshot(snapshot_record.payload_json),
            decision=_decision(decision_record.payload_json),
            outcome=outcome,
            evaluation=evaluation,
        )

    async def _append(
        self,
        value: object,
        *,
        record_type: str,
        record_id: str,
        workspace_id: str,
        user_id: int,
        created_at: datetime,
        parent_record_id: str | None = None,
    ) -> None:
        payload = _serialize(value)
        await self._repository.append(
            DecisionStoredRecord(
                workspace_id=workspace_id,
                user_id=user_id,
                record_type=record_type,
                record_id=record_id,
                parent_record_id=parent_record_id,
                content_hash=_hash(payload),
                payload_json=payload,
                created_at=created_at,
            )
        )
