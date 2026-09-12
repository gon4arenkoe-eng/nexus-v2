"""Deterministic AIEA research/evolution orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256

from apps.aiea.domain.research import (
    CandidateState,
    CandidateVersion,
    DriftAssessment,
    DriftState,
    ExperimentRecord,
    FalsificationCheck,
    FalsificationDecision,
    Hypothesis,
    KnowledgeSnapshot,
    MANDATORY_FALSIFICATION_CHECKS,
    PromotionReadiness,
    PromotionReadinessState,
    ResearchEvidence,
    ResearchMemoryEntry,
    ValidationOutcome,
    ValidationResult,
)
from apps.aiea.ports.research import ResearchRecordStore, ResearchWorkerPort
from packages.contracts.primitives import normalize_utc_datetime


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _digest(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ResearchSandboxPolicy:
    max_wall_seconds: int
    max_memory_mb: int
    max_cpu_cores: int
    allowed_dependencies: tuple[str, ...]
    network_allowed: bool = False
    exchange_credentials_allowed: bool = False
    production_filesystem_write_allowed: bool = False

    def __post_init__(self) -> None:
        for name in ("max_wall_seconds", "max_memory_mb", "max_cpu_cores"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:  # noqa: E501
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.allowed_dependencies, tuple):
            raise ValueError("allowed_dependencies must be a tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.allowed_dependencies):  # noqa: E501
            raise ValueError("allowed_dependencies must contain non-empty strings")  # noqa: E501
        if self.network_allowed:
            raise ValueError("AIEA research network access is disabled by Phase 9 policy")  # noqa: E501
        if self.exchange_credentials_allowed:
            raise ValueError("AIEA research workers cannot receive exchange credentials")  # noqa: E501
        if self.production_filesystem_write_allowed:
            raise ValueError("AIEA research workers cannot write production filesystem")  # noqa: E501


@dataclass(frozen=True, slots=True)
class ResearchTask:
    task_id: str
    workspace_id: str
    user_id: int
    hypothesis: Hypothesis
    candidate: CandidateVersion
    knowledge_snapshot: KnowledgeSnapshot
    policy: ResearchSandboxPolicy

    def __post_init__(self) -> None:
        for name in ("task_id", "workspace_id"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))  # noqa: E501
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:  # noqa: E501
            raise ValueError("user_id must be positive")
        if not isinstance(self.hypothesis, Hypothesis):
            raise ValueError("hypothesis must be Hypothesis")
        if not isinstance(self.candidate, CandidateVersion):
            raise ValueError("candidate must be CandidateVersion")
        if not isinstance(self.knowledge_snapshot, KnowledgeSnapshot):
            raise ValueError("knowledge_snapshot must be KnowledgeSnapshot")
        if not isinstance(self.policy, ResearchSandboxPolicy):
            raise ValueError("policy must be ResearchSandboxPolicy")
        ownership = {
            (self.hypothesis.workspace_id, self.hypothesis.user_id),
            (self.candidate.workspace_id, self.candidate.user_id),
            (self.knowledge_snapshot.workspace_id, self.knowledge_snapshot.user_id),  # noqa: E501
            (self.workspace_id, self.user_id),
        }
        if len(ownership) != 1:
            raise ValueError("research task ownership mismatch")
        if self.candidate.hypothesis_id != self.hypothesis.hypothesis_id:
            raise ValueError("candidate/hypothesis lineage mismatch")
        if self.hypothesis.snapshot_id != self.knowledge_snapshot.snapshot_id:
            raise ValueError("hypothesis/snapshot lineage mismatch")


class FalsificationEngine:
    """Reject weak candidates deterministically; never optimize around failures."""  # noqa: E501

    def evaluate(
        self,
        *,
        hypothesis: Hypothesis,
        candidate: CandidateVersion,
        experiments: tuple[ExperimentRecord, ...],
        evaluated_at: datetime,
    ) -> FalsificationDecision:
        if not experiments:
            raise ValueError("at least one experiment is required")
        if candidate.hypothesis_id != hypothesis.hypothesis_id:
            raise ValueError("candidate/hypothesis mismatch")
        if any(item.candidate_id != candidate.candidate_id for item in experiments):  # noqa: E501
            raise ValueError("experiment candidate mismatch")
        if any(item.hypothesis_id != hypothesis.hypothesis_id for item in experiments):  # noqa: E501
            raise ValueError("experiment hypothesis mismatch")
        ownership = {(item.workspace_id, item.user_id) for item in experiments}
        ownership.add((candidate.workspace_id, candidate.user_id))
        if len(ownership) != 1:
            raise ValueError("cross-tenant experiment evidence is forbidden")

        criteria = {item.check: item for item in hypothesis.criteria}
        latest: dict[FalsificationCheck, ValidationResult] = {}
        evidence_hashes: list[str] = []
        for experiment in experiments:
            if experiment.dataset_hash != candidate.dataset.content_hash:
                raise ValueError("experiment dataset hash does not match candidate")  # noqa: E501
            if experiment.code_hash != candidate.code_hash:
                raise ValueError("experiment code hash does not match candidate")  # noqa: E501
            if experiment.environment_digest != candidate.environment_digest:
                raise ValueError("experiment environment digest mismatch")
            if experiment.cost_model_version != candidate.cost_model_version:
                raise ValueError("experiment cost model mismatch")
            for result in experiment.results:
                latest[result.check] = result
                evidence_hashes.append(result.evidence_hash)

        missing = MANDATORY_FALSIFICATION_CHECKS - set(latest)
        failed: list[FalsificationCheck] = list(sorted(missing, key=lambda item: item.value))  # noqa: E501
        for check in sorted(MANDATORY_FALSIFICATION_CHECKS, key=lambda item: item.value):  # noqa: E501
            value = latest.get(check)
            if value is None:
                continue
            result = value
            if result.outcome is not ValidationOutcome.PASS or result.score < criteria[check].minimum_score:  # noqa: E501
                failed.append(check)

        state = CandidateState.REJECTED if failed else CandidateState.SHADOW_READY  # noqa: E501
        unique_hashes = tuple(sorted(set(evidence_hashes)))
        if not unique_hashes:
            unique_hashes = (_digest(candidate.candidate_id, "no-evidence"),)
        return FalsificationDecision(
            candidate_id=candidate.candidate_id,
            state=state,
            failed_checks=tuple(failed),
            evidence_hashes=unique_hashes,
            evaluated_at=normalize_utc_datetime(evaluated_at, field_name="evaluated_at"),  # noqa: E501
        )


class PromotionReadinessService:
    """Build evidence-bound SHADOW-only readiness; never activates strategies."""  # noqa: E501

    def build(
        self,
        *,
        candidate: CandidateVersion,
        decision: FalsificationDecision,
        rollback_version: str,
    ) -> PromotionReadiness:
        rollback = _text(rollback_version, field_name="rollback_version")
        if candidate.parent_version is None:
            state = PromotionReadinessState.BLOCKED
        elif decision.state is CandidateState.REJECTED:
            state = PromotionReadinessState.REJECTED
        else:
            state = PromotionReadinessState.SHADOW_READY
        return PromotionReadiness(
            readiness_id=_digest(candidate.candidate_id, candidate.version, "readiness"),  # noqa: E501
            workspace_id=candidate.workspace_id,
            user_id=candidate.user_id,
            strategy_id=candidate.strategy_id,
            candidate_version=candidate.version,
            candidate_id=candidate.candidate_id,
            dataset_hash=candidate.dataset.content_hash,
            code_hash=candidate.code_hash,
            environment_digest=candidate.environment_digest,
            evidence_hashes=decision.evidence_hashes,
            rollback_version=rollback,
            state=state,
            risk_approval_required=True,
            permission_approval_required=True,
        )


class ChampionChallengerService:
    """Turn degradation into research evidence, never blind live mutation."""

    def assess(
        self,
        *,
        assessment_id: str,
        workspace_id: str,
        user_id: int,
        strategy_id: str,
        champion_version: str,
        challenger_version: str | None,
        performance_ratio: Decimal,
        freshness_ratio: Decimal,
        evidence_hash: str,
        observed_at: datetime,
    ) -> DriftAssessment:
        if not isinstance(performance_ratio, Decimal) or not isinstance(freshness_ratio, Decimal):  # noqa: E501
            raise ValueError("drift ratios must be Decimal")
        if performance_ratio < Decimal("0") or performance_ratio > Decimal("1"):  # noqa: E501
            raise ValueError("performance_ratio must be between 0 and 1")
        if freshness_ratio < Decimal("0") or freshness_ratio > Decimal("1"):
            raise ValueError("freshness_ratio must be between 0 and 1")
        if freshness_ratio < Decimal("0.50"):
            state = DriftState.UNKNOWN
        elif performance_ratio < Decimal("0.55"):
            state = DriftState.DEGRADED
        elif performance_ratio < Decimal("0.75"):
            state = DriftState.WATCH
        else:
            state = DriftState.HEALTHY
        return DriftAssessment(
            assessment_id=assessment_id,
            workspace_id=workspace_id,
            user_id=user_id,
            strategy_id=strategy_id,
            champion_version=champion_version,
            challenger_version=challenger_version,
            state=state,
            observed_at=observed_at,
            performance_ratio=performance_ratio,
            freshness_ratio=freshness_ratio,
            evidence_hash=evidence_hash,
        )


class AIEAResearchCoordinator:
    """Coordinate one bounded R&D cycle through ports only."""

    def __init__(self, *, store: ResearchRecordStore, worker: ResearchWorkerPort) -> None:  # noqa: E501
        self._store = store
        self._worker = worker
        self._falsification = FalsificationEngine()
        self._promotion = PromotionReadinessService()

    async def run_task(
        self,
        task: ResearchTask,
        *,
        evaluated_at: datetime,
        rollback_version: str,
    ) -> tuple[ExperimentRecord, FalsificationDecision, PromotionReadiness]:
        experiment = await self._worker.execute(task)
        if experiment.workspace_id != task.workspace_id or experiment.user_id != task.user_id:  # noqa: E501
            raise ValueError("research worker returned cross-tenant result")
        if experiment.candidate_id != task.candidate.candidate_id:
            raise ValueError("research worker candidate mismatch")
        await self._store.append_hypothesis(task.hypothesis)
        await self._store.append_candidate(task.candidate)
        await self._store.append_experiment(experiment)
        decision = self._falsification.evaluate(
            hypothesis=task.hypothesis,
            candidate=task.candidate,
            experiments=(experiment,),
            evaluated_at=evaluated_at,
        )
        readiness = self._promotion.build(
            candidate=task.candidate,
            decision=decision,
            rollback_version=rollback_version,
        )
        return experiment, decision, readiness


def build_lesson_memory(
    *,
    memory_id: str,
    snapshot: KnowledgeSnapshot,
    hypothesis: Hypothesis,
    experiment: ExperimentRecord,
    candidate: CandidateVersion,
    lesson: str,
    created_at: datetime,
    parent_memory_id: str | None = None,
) -> ResearchMemoryEntry:
    ownership = {
        (snapshot.workspace_id, snapshot.user_id),
        (hypothesis.workspace_id, hypothesis.user_id),
        (experiment.workspace_id, experiment.user_id),
        (candidate.workspace_id, candidate.user_id),
    }
    if len(ownership) != 1:
        raise ValueError("memory lineage cannot cross tenants")
    if hypothesis.snapshot_id != snapshot.snapshot_id:
        raise ValueError("memory hypothesis/snapshot mismatch")
    if experiment.hypothesis_id != hypothesis.hypothesis_id:
        raise ValueError("memory experiment/hypothesis mismatch")
    if experiment.candidate_id != candidate.candidate_id:
        raise ValueError("memory experiment/candidate mismatch")
    provenance_hash = _digest(
        snapshot.content_hash,
        hypothesis.hypothesis_id,
        experiment.experiment_id,
        candidate.candidate_id,
        candidate.dataset.content_hash,
        candidate.code_hash,
        candidate.environment_digest,
    )
    return ResearchMemoryEntry(
        memory_id=memory_id,
        workspace_id=snapshot.workspace_id,
        user_id=snapshot.user_id,
        created_at=created_at,
        snapshot_id=snapshot.snapshot_id,
        hypothesis_id=hypothesis.hypothesis_id,
        experiment_id=experiment.experiment_id,
        candidate_id=candidate.candidate_id,
        lesson=lesson,
        provenance_hash=provenance_hash,
        parent_memory_id=parent_memory_id,
    )


@dataclass(frozen=True, slots=True)
class ResearchCycleResult:
    experiment: ExperimentRecord
    decision: FalsificationDecision
    readiness: PromotionReadiness
    memory: ResearchMemoryEntry


async def run_closed_research_cycle(
    *,
    store: ResearchRecordStore,
    worker: ResearchWorkerPort,
    task: ResearchTask,
    evidence: tuple[ResearchEvidence, ...],
    memory_id: str,
    lesson: str,
    evaluated_at: datetime,
    rollback_version: str,
    parent_memory_id: str | None = None,
) -> ResearchCycleResult:
    """Run Evidence -> Candidate -> Falsification -> Lesson as one cycle."""

    if not evidence:
        raise ValueError("closed research cycle requires evidence")
    ownership = {(item.workspace_id, item.user_id) for item in evidence}
    ownership.add((task.workspace_id, task.user_id))
    if len(ownership) != 1:
        raise ValueError("closed research cycle evidence ownership mismatch")
    evidence_ids = tuple(item.evidence_id for item in evidence)
    if tuple(sorted(evidence_ids)) != tuple(
        sorted(task.knowledge_snapshot.evidence_ids)
    ):
        raise ValueError("knowledge snapshot evidence identity mismatch")
    for item in evidence:
        await store.append_evidence(item)
    coordinator = AIEAResearchCoordinator(store=store, worker=worker)
    experiment, decision, readiness = await coordinator.run_task(
        task,
        evaluated_at=evaluated_at,
        rollback_version=rollback_version,
    )
    memory = build_lesson_memory(
        memory_id=memory_id,
        snapshot=task.knowledge_snapshot,
        hypothesis=task.hypothesis,
        experiment=experiment,
        candidate=task.candidate,
        lesson=lesson,
        created_at=evaluated_at,
        parent_memory_id=parent_memory_id,
    )
    await store.append_memory(memory)
    return ResearchCycleResult(
        experiment=experiment,
        decision=decision,
        readiness=readiness,
        memory=memory,
    )
