"""Evidence-bound self-evaluation contracts for Decision Intelligence.

The contracts intentionally distinguish observed facts from inferred quality
scores. Missing evaluators are represented as missing signals and cause an
INSUFFICIENT_EVIDENCE classification rather than optimistic guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from apps.decision_intelligence.domain.decision import DecisionErrorClass
from packages.contracts.primitives import normalize_utc_datetime, require_decimal

_ZERO = Decimal("0")
_ONE = Decimal("1")


def _unit_or_none(value: Decimal | None, *, field_name: str) -> Decimal | None:
    if value is None:
        return None
    value = require_decimal(value, field_name=field_name)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _text_tuple(value: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


@dataclass(frozen=True, slots=True)
class DecisionEvaluationSignals:
    """Independent evaluator scores available after an outcome is known.

    Every score is optional. Absence is meaningful evidence: the automated
    evaluator must mark the result as insufficient rather than fabricate a
    metric from PnL alone.
    """

    market_model_accuracy: Decimal | None = None
    strategy_selection_quality: Decimal | None = None
    allocation_quality: Decimal | None = None
    timing_quality: Decimal | None = None
    execution_quality: Decimal | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "market_model_accuracy",
            "strategy_selection_quality",
            "allocation_quality",
            "timing_quality",
            "execution_quality",
        ):
            object.__setattr__(
                self,
                name,
                _unit_or_none(getattr(self, name), field_name=name),
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _text_tuple(self.evidence_refs, field_name="evidence_refs"),
        )

    @property
    def complete(self) -> bool:
        return all(
            getattr(self, name) is not None
            for name in (
                "market_model_accuracy",
                "strategy_selection_quality",
                "allocation_quality",
                "timing_quality",
                "execution_quality",
            )
        )


@dataclass(frozen=True, slots=True)
class DecisionCalibrationSummary:
    workspace_id: str
    user_id: int
    evaluated_at: datetime
    decision_count: int
    winning_decisions: int
    losing_decisions: int
    flat_decisions: int
    average_realized_r: Decimal
    average_confidence_calibration: Decimal
    brier_score: Decimal
    average_error_cost_r: Decimal
    error_counts: Mapping[DecisionErrorClass, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise ValueError("workspace_id must be non-empty")
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        object.__setattr__(
            self,
            "evaluated_at",
            normalize_utc_datetime(self.evaluated_at, field_name="evaluated_at"),
        )
        for name in (
            "decision_count",
            "winning_decisions",
            "losing_decisions",
            "flat_decisions",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.winning_decisions + self.losing_decisions + self.flat_decisions != self.decision_count:
            raise ValueError("decision outcome counts must equal decision_count")
        for name in ("average_realized_r", "average_error_cost_r"):
            object.__setattr__(
                self,
                name,
                require_decimal(getattr(self, name), field_name=name),
            )
        for name in ("average_confidence_calibration", "brier_score"):
            value = require_decimal(getattr(self, name), field_name=name)
            if value < _ZERO or value > _ONE:
                raise ValueError(f"{name} must be between 0 and 1")
            object.__setattr__(self, name, value)
        normalized: dict[DecisionErrorClass, int] = {}
        for key, value in self.error_counts.items():
            if not isinstance(key, DecisionErrorClass):
                raise ValueError("error_counts keys must be DecisionErrorClass")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("error_counts values must be non-negative integers")
            normalized[key] = value
        object.__setattr__(self, "error_counts", MappingProxyType(normalized))
