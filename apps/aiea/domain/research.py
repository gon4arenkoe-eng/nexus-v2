"""Canonical AIEA research/evolution contracts for NEXUS V2 Phase 9."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from packages.contracts.primitives import normalize_utc_datetime


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _positive_user(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("user_id must be a positive integer")
    return value


def _ratio(value: Decimal, *, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _mapping(value: Mapping[str, object], *, field_name: str) -> Mapping[str, object]:  # noqa: E501
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return MappingProxyType(dict(value))


class ResearchEvidenceKind(StrEnum):
    MARKET = "MARKET"
    TRADE = "TRADE"
    DATA_QUALITY = "DATA_QUALITY"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    DRIFT = "DRIFT"
    MODEL = "MODEL"
    LESSON = "LESSON"


class HypothesisState(StrEnum):
    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    FALSIFIED = "FALSIFIED"
    SUPPORTED = "SUPPORTED"
    RETIRED = "RETIRED"


class CandidateState(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    VALIDATING = "VALIDATING"
    REJECTED = "REJECTED"
    SHADOW_READY = "SHADOW_READY"
    RETIRED = "RETIRED"


class ExperimentStage(StrEnum):
    STATIC_DATA = "STATIC_DATA"
    BACKTEST = "BACKTEST"
    OOS = "OOS"
    WALK_FORWARD = "WALK_FORWARD"
    REGIME_SLICES = "REGIME_SLICES"
    FALSIFICATION = "FALSIFICATION"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    COMPARISON = "COMPARISON"


class FalsificationCheck(StrEnum):
    LOOKAHEAD_LEAKAGE = "LOOKAHEAD_LEAKAGE"
    HOLDOUT_ISOLATION = "HOLDOUT_ISOLATION"
    REALISTIC_COSTS = "REALISTIC_COSTS"
    OOS = "OOS"
    WALK_FORWARD = "WALK_FORWARD"
    REGIME_STABILITY = "REGIME_STABILITY"
    SYMBOL_STABILITY = "SYMBOL_STABILITY"
    PARAMETER_STABILITY = "PARAMETER_STABILITY"
    CAPACITY_LIQUIDITY = "CAPACITY_LIQUIDITY"
    MINIMUM_SAMPLE = "MINIMUM_SAMPLE"
    TAIL_RISK = "TAIL_RISK"
    DATA_QUALITY = "DATA_QUALITY"
    FALSE_DISCOVERY = "FALSE_DISCOVERY"


MANDATORY_FALSIFICATION_CHECKS: frozenset[FalsificationCheck] = (
    frozenset(FalsificationCheck)
)


class ValidationOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class PromotionReadinessState(StrEnum):
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    SHADOW_READY = "SHADOW_READY"


class DriftState(StrEnum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class ArtifactKind(StrEnum):
    DATASET = "DATASET"
    FEATURES = "FEATURES"
    MODEL = "MODEL"
    STRATEGY = "STRATEGY"
    EVIDENCE = "EVIDENCE"


@dataclass(frozen=True, slots=True)
class DatasetLineage:
    dataset_id: str
    version: str
    content_hash: str
    feature_definition_hash: str
    train_interval: str
    validation_interval: str
    test_interval: str

    def __post_init__(self) -> None:
        for name in (
            "dataset_id",
            "version",
            "content_hash",
            "feature_definition_hash",
            "train_interval",
            "validation_interval",
            "test_interval",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        intervals = (
            self.train_interval,
            self.validation_interval,
            self.test_interval,
        )
        if len(set(intervals)) != 3:
            raise ValueError("train/validation/test intervals must be distinct")  # noqa: E501


@dataclass(frozen=True, slots=True)
class ResearchEvidence:
    evidence_id: str
    workspace_id: str
    user_id: int
    kind: ResearchEvidenceKind
    observed_at: datetime
    content_hash: str
    source_ref: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("evidence_id", "workspace_id", "content_hash", "source_ref"):  # noqa: E501
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if not isinstance(self.kind, ResearchEvidenceKind):
            raise ValueError("kind must be ResearchEvidenceKind")
        object.__setattr__(self, "observed_at", normalize_utc_datetime(self.observed_at, field_name="observed_at"))  # noqa: E501
        object.__setattr__(self, "payload", _mapping(self.payload, field_name="payload"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    snapshot_id: str
    workspace_id: str
    user_id: int
    created_at: datetime
    evidence_ids: tuple[str, ...]
    content_hash: str

    def __post_init__(self) -> None:
        for name in ("snapshot_id", "workspace_id", "content_hash"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ValueError("evidence_ids must be a non-empty tuple")
        normalized = tuple(_text(item, field_name="evidence_id") for item in self.evidence_ids)  # noqa: E501
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_ids must be unique")
        object.__setattr__(self, "evidence_ids", normalized)


@dataclass(frozen=True, slots=True)
class ResearchMemoryEntry:
    memory_id: str
    workspace_id: str
    user_id: int
    created_at: datetime
    snapshot_id: str
    hypothesis_id: str | None
    experiment_id: str | None
    candidate_id: str | None
    lesson: str
    provenance_hash: str
    parent_memory_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("memory_id", "workspace_id", "snapshot_id", "lesson", "provenance_hash"):  # noqa: E501
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        for name in ("hypothesis_id", "experiment_id", "candidate_id", "parent_memory_id"):  # noqa: E501
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _text(value, field_name=name))


@dataclass(frozen=True, slots=True)
class FalsificationCriterion:
    check: FalsificationCheck
    minimum_score: Decimal
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.check, FalsificationCheck):
            raise ValueError("check must be FalsificationCheck")
        _ratio(self.minimum_score, field_name="minimum_score")
        object.__setattr__(self, "rationale", _text(self.rationale, field_name="rationale"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class Hypothesis:
    hypothesis_id: str
    workspace_id: str
    user_id: int
    snapshot_id: str
    statement: str
    expected_effect: str
    created_at: datetime
    criteria: tuple[FalsificationCriterion, ...]
    state: HypothesisState = HypothesisState.PROPOSED

    def __post_init__(self) -> None:
        for name in ("hypothesis_id", "workspace_id", "snapshot_id", "statement", "expected_effect"):  # noqa: E501
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        if not isinstance(self.criteria, tuple):
            raise ValueError("criteria must be a tuple")
        if not all(isinstance(item, FalsificationCriterion) for item in self.criteria):  # noqa: E501
            raise ValueError("criteria must contain FalsificationCriterion values")  # noqa: E501
        checks = frozenset(item.check for item in self.criteria)
        missing = MANDATORY_FALSIFICATION_CHECKS - checks
        if missing:
            names = ",".join(sorted(item.value for item in missing))
            raise ValueError(f"hypothesis missing mandatory falsification checks: {names}")  # noqa: E501
        if len(checks) != len(self.criteria):
            raise ValueError("criteria checks must be unique")
        if not isinstance(self.state, HypothesisState):
            raise ValueError("state must be HypothesisState")


@dataclass(frozen=True, slots=True)
class CandidateVersion:
    candidate_id: str
    workspace_id: str
    user_id: int
    hypothesis_id: str
    strategy_id: str
    version: str
    parent_version: str | None
    before_spec_hash: str
    after_spec_hash: str
    reason: str
    expected_effect: str
    code_hash: str
    environment_digest: str
    cost_model_version: str
    dataset: DatasetLineage
    created_at: datetime
    state: CandidateState = CandidateState.RESEARCH_ONLY

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "workspace_id",
            "hypothesis_id",
            "strategy_id",
            "version",
            "before_spec_hash",
            "after_spec_hash",
            "reason",
            "expected_effect",
            "code_hash",
            "environment_digest",
            "cost_model_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if self.parent_version is not None:
            object.__setattr__(self, "parent_version", _text(self.parent_version, field_name="parent_version"))  # noqa: E501
            if self.parent_version == self.version:
                raise ValueError("candidate version must differ from parent_version")  # noqa: E501
        if self.before_spec_hash == self.after_spec_hash:
            raise ValueError("candidate must have immutable before/after evolution delta")  # noqa: E501
        if not isinstance(self.dataset, DatasetLineage):
            raise ValueError("dataset must be DatasetLineage")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        if not isinstance(self.state, CandidateState):
            raise ValueError("state must be CandidateState")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    check: FalsificationCheck
    outcome: ValidationOutcome
    score: Decimal
    evidence_hash: str
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.check, FalsificationCheck):
            raise ValueError("check must be FalsificationCheck")
        if not isinstance(self.outcome, ValidationOutcome):
            raise ValueError("outcome must be ValidationOutcome")
        _ratio(self.score, field_name="score")
        object.__setattr__(self, "evidence_hash", _text(self.evidence_hash, field_name="evidence_hash"))  # noqa: E501
        object.__setattr__(self, "detail", _text(self.detail, field_name="detail"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    experiment_id: str
    workspace_id: str
    user_id: int
    hypothesis_id: str
    candidate_id: str
    stage: ExperimentStage
    started_at: datetime
    completed_at: datetime
    dataset_hash: str
    code_hash: str
    environment_digest: str
    cost_model_version: str
    results: tuple[ValidationResult, ...]
    metrics: Mapping[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "experiment_id",
            "workspace_id",
            "hypothesis_id",
            "candidate_id",
            "dataset_hash",
            "code_hash",
            "environment_digest",
            "cost_model_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if not isinstance(self.stage, ExperimentStage):
            raise ValueError("stage must be ExperimentStage")
        object.__setattr__(self, "started_at", normalize_utc_datetime(self.started_at, field_name="started_at"))  # noqa: E501
        object.__setattr__(self, "completed_at", normalize_utc_datetime(self.completed_at, field_name="completed_at"))  # noqa: E501
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if not isinstance(self.results, tuple) or not self.results:
            raise ValueError("results must be a non-empty tuple")
        if not all(isinstance(item, ValidationResult) for item in self.results):  # noqa: E501
            raise ValueError("results must contain ValidationResult values")
        checks = tuple(item.check for item in self.results)
        if len(checks) != len(set(checks)):
            raise ValueError("experiment results must have unique checks")
        if not isinstance(self.metrics, Mapping):
            raise ValueError("metrics must be a mapping")
        normalized: dict[str, Decimal] = {}
        for key, value in self.metrics.items():
            normalized[_text(key, field_name="metric_name")] = value
            if not isinstance(value, Decimal):
                raise ValueError("metrics values must be Decimal")
        object.__setattr__(self, "metrics", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class FalsificationDecision:
    candidate_id: str
    state: CandidateState
    failed_checks: tuple[FalsificationCheck, ...]
    evidence_hashes: tuple[str, ...]
    evaluated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _text(self.candidate_id, field_name="candidate_id"))  # noqa: E501
        if self.state not in (CandidateState.REJECTED, CandidateState.SHADOW_READY):  # noqa: E501
            raise ValueError("falsification state must be REJECTED or SHADOW_READY")  # noqa: E501
        if self.state is CandidateState.SHADOW_READY and self.failed_checks:
            raise ValueError("SHADOW_READY decision cannot have failed_checks")
        if self.state is CandidateState.REJECTED and not self.failed_checks:
            raise ValueError("REJECTED decision requires failed_checks")
        if not all(isinstance(item, FalsificationCheck) for item in self.failed_checks):  # noqa: E501
            raise ValueError("failed_checks must contain FalsificationCheck")
        if not self.evidence_hashes:
            raise ValueError("evidence_hashes must be non-empty")
        object.__setattr__(self, "evaluated_at", normalize_utc_datetime(self.evaluated_at, field_name="evaluated_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class PromotionReadiness:
    readiness_id: str
    workspace_id: str
    user_id: int
    strategy_id: str
    candidate_version: str
    candidate_id: str
    dataset_hash: str
    code_hash: str
    environment_digest: str
    evidence_hashes: tuple[str, ...]
    rollback_version: str
    state: PromotionReadinessState
    risk_approval_required: bool = True
    permission_approval_required: bool = True

    def __post_init__(self) -> None:
        for name in (
            "readiness_id",
            "workspace_id",
            "strategy_id",
            "candidate_version",
            "candidate_id",
            "dataset_hash",
            "code_hash",
            "environment_digest",
            "rollback_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if not isinstance(self.state, PromotionReadinessState):
            raise ValueError("state must be PromotionReadinessState")
        if not self.evidence_hashes:
            raise ValueError("evidence_hashes must be non-empty")
        if self.state is PromotionReadinessState.SHADOW_READY:
            if not self.risk_approval_required or not self.permission_approval_required:  # noqa: E501
                raise ValueError("SHADOW_READY must still require independent approvals")  # noqa: E501


@dataclass(frozen=True, slots=True)
class DriftAssessment:
    assessment_id: str
    workspace_id: str
    user_id: int
    strategy_id: str
    champion_version: str
    challenger_version: str | None
    state: DriftState
    observed_at: datetime
    performance_ratio: Decimal
    freshness_ratio: Decimal
    evidence_hash: str

    def __post_init__(self) -> None:
        for name in ("assessment_id", "workspace_id", "strategy_id", "champion_version", "evidence_hash"):  # noqa: E501
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if self.challenger_version is not None:
            object.__setattr__(self, "challenger_version", _text(self.challenger_version, field_name="challenger_version"))  # noqa: E501
            if self.challenger_version == self.champion_version:
                raise ValueError("challenger_version must differ from champion_version")  # noqa: E501
        if not isinstance(self.state, DriftState):
            raise ValueError("state must be DriftState")
        object.__setattr__(self, "observed_at", normalize_utc_datetime(self.observed_at, field_name="observed_at"))  # noqa: E501
        _ratio(self.performance_ratio, field_name="performance_ratio")
        _ratio(self.freshness_ratio, field_name="freshness_ratio")


@dataclass(frozen=True, slots=True)
class ResearchArtifact:
    artifact_id: str
    workspace_id: str
    user_id: int
    kind: ArtifactKind
    version: str
    content_hash: str
    parent_artifact_id: str | None
    created_at: datetime
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("artifact_id", "workspace_id", "version", "content_hash"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        _positive_user(self.user_id)
        if not isinstance(self.kind, ArtifactKind):
            raise ValueError("kind must be ArtifactKind")
        if self.parent_artifact_id is not None:
            object.__setattr__(self, "parent_artifact_id", _text(self.parent_artifact_id, field_name="parent_artifact_id"))  # noqa: E501
            if self.parent_artifact_id == self.artifact_id:
                raise ValueError("artifact cannot parent itself")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        object.__setattr__(self, "metadata", _mapping(self.metadata, field_name="metadata"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class ResearchArtifactRegistry:
    registry_version: str
    artifacts: tuple[ResearchArtifact, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "registry_version",
            _text(self.registry_version, field_name="registry_version"),
        )
        if not isinstance(self.artifacts, tuple):
            raise ValueError("artifacts must be a tuple")
        if not all(isinstance(item, ResearchArtifact) for item in self.artifacts):  # noqa: E501
            raise ValueError("artifacts must contain ResearchArtifact values")
        keys = tuple(
            (
                item.workspace_id,
                item.user_id,
                item.kind,
                item.artifact_id,
                item.version,
            )
            for item in self.artifacts
        )
        if len(keys) != len(set(keys)):
            raise ValueError(
                "artifact registry entries must be immutable and unique"
            )
        object.__setattr__(
            self,
            "artifacts",
            tuple(
                sorted(
                    self.artifacts,
                    key=lambda item: (
                        item.workspace_id,
                        item.user_id,
                        item.kind.value,
                        item.artifact_id,
                        item.version,
                    ),
                )
            ),
        )

    def for_owner(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[ResearchArtifact, ...]:
        return tuple(
            item
            for item in self.artifacts
            if item.workspace_id == workspace_id and item.user_id == user_id
        )
