"""Provider-neutral autonomous decision contracts for NEXUS V2.

This bounded context may propose strategy portfolio decisions. It never owns
Risk, execution, venue writes, credentials, or production activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from packages.contracts.identities import InstrumentId
from packages.contracts.primitives import normalize_utc_datetime, require_decimal


_ZERO = Decimal("0")
_ONE = Decimal("1")


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _unit(value: Decimal, *, field_name: str) -> Decimal:
    value = require_decimal(value, field_name=field_name)
    if not _ZERO <= value <= _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


class DecisionState(StrEnum):
    NO_TRADE = "NO_TRADE"
    HOLD = "HOLD"
    REBALANCE = "REBALANCE"
    ACTIVATE = "ACTIVATE"
    REDUCE = "REDUCE"
    DEACTIVATE = "DEACTIVATE"


class OpportunityEligibility(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"


class DecisionPreference(StrEnum):
    CAPITAL_PRESERVATION = "CAPITAL_PRESERVATION"
    BALANCED = "BALANCED"
    OPPORTUNISTIC = "OPPORTUNISTIC"


class DecisionErrorClass(StrEnum):
    NO_ERROR_DETECTED = "NO_ERROR_DETECTED"
    REGIME_CLASSIFICATION_ERROR = "REGIME_CLASSIFICATION_ERROR"
    STRATEGY_SELECTION_ERROR = "STRATEGY_SELECTION_ERROR"
    ALLOCATION_ERROR = "ALLOCATION_ERROR"
    PARAMETER_ERROR = "PARAMETER_ERROR"
    TIMING_ERROR = "TIMING_ERROR"
    DATA_QUALITY_ERROR = "DATA_QUALITY_ERROR"
    RISK_ESTIMATION_ERROR = "RISK_ESTIMATION_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ReasoningStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True, slots=True)
class DecisionObjective:
    objective_id: str
    version: str
    primary_goal: str
    preference: DecisionPreference
    max_portfolio_risk: Decimal
    min_data_quality: Decimal
    min_expected_net_edge: Decimal
    max_strategy_weight: Decimal

    def __post_init__(self) -> None:
        for name in ("objective_id", "version", "primary_goal"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if not isinstance(self.preference, DecisionPreference):
            raise ValueError("preference must be DecisionPreference")
        for name in ("max_portfolio_risk", "min_data_quality", "max_strategy_weight"):
            object.__setattr__(self, name, _unit(getattr(self, name), field_name=name))
        object.__setattr__(
            self,
            "min_expected_net_edge",
            require_decimal(self.min_expected_net_edge, field_name="min_expected_net_edge"),
        )


@dataclass(frozen=True, slots=True)
class MarketDecisionSnapshot:
    snapshot_id: str
    workspace_id: str
    user_id: int
    created_at: datetime
    market_context_hash: str
    market_context_as_of: datetime
    instruments: tuple[InstrumentId, ...]
    data_quality_state: str
    data_quality_score: Decimal
    market_uncertainty: Decimal
    active_blockers: tuple[str, ...] = ()
    available_strategy_versions: tuple[str, ...] = ()
    decision_policy_version: str = "decision-v1"
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "snapshot_id",
            "workspace_id",
            "market_context_hash",
            "data_quality_state",
            "decision_policy_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))
        object.__setattr__(
            self,
            "market_context_as_of",
            normalize_utc_datetime(self.market_context_as_of, field_name="market_context_as_of"),
        )
        if not self.instruments or not all(isinstance(item, InstrumentId) for item in self.instruments):
            raise ValueError("instruments must be a non-empty tuple of InstrumentId")
        object.__setattr__(self, "data_quality_score", _unit(self.data_quality_score, field_name="data_quality_score"))
        object.__setattr__(self, "market_uncertainty", _unit(self.market_uncertainty, field_name="market_uncertainty"))
        for name in ("active_blockers", "available_strategy_versions", "evidence_refs"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(f"{name} must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class StrategyOpportunityAssessment:
    assessment_id: str
    snapshot_id: str
    strategy_id: str
    strategy_version: str
    strategy_family: str
    eligibility: OpportunityEligibility
    expected_net_edge: Decimal
    confidence: Decimal
    uncertainty: Decimal
    regime_suitability: Decimal
    liquidity_suitability: Decimal
    event_risk_suitability: Decimal
    capacity_score: Decimal
    drawdown_risk: Decimal
    tail_risk_score: Decimal
    correlation_penalty: Decimal
    diversification_value: Decimal
    data_quality_score: Decimal
    block_reasons: tuple[str, ...] = ()
    supporting_evidence: tuple[str, ...] = ()
    contradicting_evidence: tuple[str, ...] = ()
    recommended_parameters_ref: str | None = None
    assessment_model_version: str = "assessment-v1"

    def __post_init__(self) -> None:
        for name in (
            "assessment_id",
            "snapshot_id",
            "strategy_id",
            "strategy_version",
            "strategy_family",
            "assessment_model_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if not isinstance(self.eligibility, OpportunityEligibility):
            raise ValueError("eligibility must be OpportunityEligibility")
        object.__setattr__(
            self,
            "expected_net_edge",
            require_decimal(self.expected_net_edge, field_name="expected_net_edge"),
        )
        for name in (
            "confidence",
            "uncertainty",
            "regime_suitability",
            "liquidity_suitability",
            "event_risk_suitability",
            "capacity_score",
            "drawdown_risk",
            "tail_risk_score",
            "correlation_penalty",
            "diversification_value",
            "data_quality_score",
        ):
            object.__setattr__(self, name, _unit(getattr(self, name), field_name=name))
        if self.eligibility is OpportunityEligibility.BLOCKED and not self.block_reasons:
            raise ValueError("blocked assessment requires block_reasons")
        for name in ("block_reasons", "supporting_evidence", "contradicting_evidence"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(f"{name} must contain non-empty strings")
        if self.recommended_parameters_ref is not None:
            object.__setattr__(
                self,
                "recommended_parameters_ref",
                _text(self.recommended_parameters_ref, field_name="recommended_parameters_ref"),
            )

    @property
    def deterministic_score(self) -> Decimal:
        positive = (
            self.expected_net_edge
            + self.confidence
            + self.regime_suitability
            + self.liquidity_suitability
            + self.event_risk_suitability
            + self.capacity_score
            + self.diversification_value
            + self.data_quality_score
        )
        penalties = self.uncertainty + self.drawdown_risk + self.tail_risk_score + self.correlation_penalty
        return positive - penalties


@dataclass(frozen=True, slots=True)
class StrategyAllocationRecommendation:
    strategy_id: str
    strategy_version: str
    target_weight: Decimal
    max_weight: Decimal
    confidence: Decimal
    expected_contribution: Decimal
    expected_risk_contribution: Decimal
    parameter_set_ref: str | None = None
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("strategy_id", "strategy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        for name in ("target_weight", "max_weight", "confidence", "expected_risk_contribution"):
            object.__setattr__(self, name, _unit(getattr(self, name), field_name=name))
        if self.target_weight > self.max_weight:
            raise ValueError("target_weight cannot exceed max_weight")
        object.__setattr__(
            self,
            "expected_contribution",
            require_decimal(self.expected_contribution, field_name="expected_contribution"),
        )
        if self.parameter_set_ref is not None:
            object.__setattr__(self, "parameter_set_ref", _text(self.parameter_set_ref, field_name="parameter_set_ref"))
        if not isinstance(self.reason_codes, tuple) or not all(isinstance(item, str) and item.strip() for item in self.reason_codes):
            raise ValueError("reason_codes must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class StrategyPortfolioDecision:
    decision_id: str
    snapshot_id: str
    workspace_id: str
    user_id: int
    created_at: datetime
    state: DecisionState
    objective_id: str
    objective_version: str
    portfolio_confidence: Decimal
    portfolio_uncertainty: Decimal
    allocations: tuple[StrategyAllocationRecommendation, ...]
    reason_codes: tuple[str, ...]
    decision_policy_version: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "snapshot_id",
            "workspace_id",
            "objective_id",
            "objective_version",
            "decision_policy_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))
        if not isinstance(self.state, DecisionState):
            raise ValueError("state must be DecisionState")
        object.__setattr__(self, "portfolio_confidence", _unit(self.portfolio_confidence, field_name="portfolio_confidence"))
        object.__setattr__(self, "portfolio_uncertainty", _unit(self.portfolio_uncertainty, field_name="portfolio_uncertainty"))
        if not isinstance(self.allocations, tuple) or not all(isinstance(item, StrategyAllocationRecommendation) for item in self.allocations):
            raise ValueError("allocations must contain StrategyAllocationRecommendation")
        if self.state is DecisionState.NO_TRADE and self.allocations:
            raise ValueError("NO_TRADE decision cannot contain allocations")
        if self.state is not DecisionState.NO_TRADE and not self.allocations:
            raise ValueError("trade-capable decision requires allocations")
        total = sum((item.target_weight for item in self.allocations), _ZERO)
        if total > _ONE:
            raise ValueError("allocation target weights cannot exceed 1")
        for name in ("reason_codes", "evidence_refs"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(f"{name} must contain non-empty strings")
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    outcome_id: str
    decision_id: str
    evaluated_at: datetime
    realized_pnl: Decimal
    realized_r_multiple: Decimal
    fees: Decimal
    funding: Decimal
    slippage: Decimal
    execution_quality_ref: str | None = None
    reconciliation_evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("outcome_id", "decision_id"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        object.__setattr__(self, "evaluated_at", normalize_utc_datetime(self.evaluated_at, field_name="evaluated_at"))
        for name in ("realized_pnl", "realized_r_multiple", "fees", "funding", "slippage"):
            object.__setattr__(self, name, require_decimal(getattr(self, name), field_name=name))
        if self.execution_quality_ref is not None:
            object.__setattr__(self, "execution_quality_ref", _text(self.execution_quality_ref, field_name="execution_quality_ref"))
        if not isinstance(self.reconciliation_evidence_refs, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.reconciliation_evidence_refs
        ):
            raise ValueError("reconciliation_evidence_refs must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class DecisionEvaluation:
    evaluation_id: str
    decision_id: str
    outcome_id: str
    evaluated_at: datetime
    market_model_accuracy: Decimal
    strategy_selection_quality: Decimal
    allocation_quality: Decimal
    confidence_calibration: Decimal
    timing_quality: Decimal
    data_quality_impact: Decimal
    execution_quality: Decimal
    primary_error_class: DecisionErrorClass
    secondary_error_classes: tuple[DecisionErrorClass, ...] = ()
    lesson_candidate: str | None = None
    research_required: bool = False
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("evaluation_id", "decision_id", "outcome_id"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        object.__setattr__(self, "evaluated_at", normalize_utc_datetime(self.evaluated_at, field_name="evaluated_at"))
        for name in (
            "market_model_accuracy",
            "strategy_selection_quality",
            "allocation_quality",
            "confidence_calibration",
            "timing_quality",
            "data_quality_impact",
            "execution_quality",
        ):
            object.__setattr__(self, name, _unit(getattr(self, name), field_name=name))
        if not isinstance(self.primary_error_class, DecisionErrorClass):
            raise ValueError("primary_error_class must be DecisionErrorClass")
        if not isinstance(self.secondary_error_classes, tuple) or not all(
            isinstance(item, DecisionErrorClass) for item in self.secondary_error_classes
        ):
            raise ValueError("secondary_error_classes must contain DecisionErrorClass")
        if self.lesson_candidate is not None:
            object.__setattr__(self, "lesson_candidate", _text(self.lesson_candidate, field_name="lesson_candidate"))
        if not isinstance(self.research_required, bool):
            raise ValueError("research_required must be bool")
        if not isinstance(self.evidence_refs, tuple) or not all(isinstance(item, str) and item.strip() for item in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class DecisionMemoryRecord:
    memory_id: str
    snapshot: MarketDecisionSnapshot
    decision: StrategyPortfolioDecision
    outcome: DecisionOutcome | None = None
    evaluation: DecisionEvaluation | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_id", _text(self.memory_id, field_name="memory_id"))
        if self.decision.snapshot_id != self.snapshot.snapshot_id:
            raise ValueError("decision/snapshot lineage mismatch")
        if self.outcome is not None and self.outcome.decision_id != self.decision.decision_id:
            raise ValueError("outcome/decision lineage mismatch")
        if self.evaluation is not None:
            if self.outcome is None:
                raise ValueError("evaluation requires outcome")
            if self.evaluation.decision_id != self.decision.decision_id or self.evaluation.outcome_id != self.outcome.outcome_id:
                raise ValueError("evaluation lineage mismatch")


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    request_id: str
    task: str
    structured_context: Mapping[str, object]
    evidence_refs: tuple[str, ...]
    prompt_template_version: str
    system_policy_version: str

    def __post_init__(self) -> None:
        for name in ("request_id", "task", "prompt_template_version", "system_policy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if not isinstance(self.structured_context, Mapping):
            raise ValueError("structured_context must be a mapping")
        object.__setattr__(self, "structured_context", MappingProxyType(dict(self.structured_context)))
        if not isinstance(self.evidence_refs, tuple) or not all(isinstance(item, str) and item.strip() for item in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    request_id: str
    status: ReasoningStatus
    provider: str
    model_id: str
    output: Mapping[str, object]
    output_hash: str
    created_at: datetime
    prompt_template_version: str
    system_policy_version: str
    error_code: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "provider",
            "model_id",
            "output_hash",
            "prompt_template_version",
            "system_policy_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        if not isinstance(self.status, ReasoningStatus):
            raise ValueError("status must be ReasoningStatus")
        if not isinstance(self.output, Mapping):
            raise ValueError("output must be a mapping")
        object.__setattr__(self, "output", MappingProxyType(dict(self.output)))
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))
        if self.error_code is not None:
            object.__setattr__(self, "error_code", _text(self.error_code, field_name="error_code"))
        if self.status is ReasoningStatus.DEGRADED and self.error_code is None:
            raise ValueError("DEGRADED reasoning requires error_code")
