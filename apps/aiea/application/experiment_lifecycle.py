"""Canonical fail-closed orchestration for the AIEA experiment lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.aiea.application.research_loop import (
    FalsificationEngine,
    PromotionReadinessService,
    ResearchTask,
)
from apps.aiea.domain.research import (
    CandidateState,
    ExperimentRecord,
    ExperimentStage,
    FalsificationDecision,
    PromotionReadiness,
    PromotionReadinessState,
    ValidationOutcome,
)
from apps.aiea.ports.research import ResearchRecordStore
from apps.aiea.ports.lifecycle import ExperimentStageWorkerPort


REQUIRED_EXPERIMENT_STAGES: tuple[ExperimentStage, ...] = (
    ExperimentStage.BACKTEST,
    ExperimentStage.OOS,
    ExperimentStage.WALK_FORWARD,
    ExperimentStage.REGIME_SLICES,
    ExperimentStage.FALSIFICATION,
    ExperimentStage.PAPER,
    ExperimentStage.SHADOW,
    ExperimentStage.COMPARISON,
)


class ExperimentLifecycleError(ValueError):
    """Experiment evidence is incomplete, inconsistent, or out of sequence."""


@dataclass(frozen=True, slots=True)
class ExperimentLifecycleResult:
    experiments: tuple[ExperimentRecord, ...]
    decision: FalsificationDecision
    readiness: PromotionReadiness
    completed_stages: tuple[ExperimentStage, ...]


class AIEAExperimentLifecycleOrchestrator:
    """Drive one candidate through the mandatory research stages only.

    This service never activates a strategy and never obtains Risk, Venue, exchange,
    or production write authority. A successful result is at most SHADOW_READY.
    """

    def __init__(
        self,
        *,
        store: ResearchRecordStore,
        worker: ExperimentStageWorkerPort,
    ) -> None:
        self._store = store
        self._worker = worker
        self._falsification = FalsificationEngine()
        self._promotion = PromotionReadinessService()

    async def run(
        self,
        task: ResearchTask,
        *,
        evaluated_at: datetime,
        rollback_version: str,
    ) -> ExperimentLifecycleResult:
        await self._store.append_snapshot(task.knowledge_snapshot)
        await self._store.append_hypothesis(task.hypothesis)
        await self._store.append_candidate(task.candidate)

        persisted = await self._store.list_experiments_for_candidate(
            workspace_id=task.workspace_id,
            user_id=task.user_id,
            candidate_id=task.candidate.candidate_id,
        )
        persisted = tuple(
            sorted(
                persisted,
                key=lambda item: REQUIRED_EXPERIMENT_STAGES.index(item.stage)
                if item.stage in REQUIRED_EXPERIMENT_STAGES
                else len(REQUIRED_EXPERIMENT_STAGES),
            )
        )
        by_stage = self._validate_persisted(task, persisted)

        experiments: list[ExperimentRecord] = []
        for stage in REQUIRED_EXPERIMENT_STAGES:
            existing = by_stage.get(stage)
            if existing is not None:
                experiment = existing
            else:
                experiment = await self._worker.execute_stage(
                    task,
                    stage=stage,
                    prior_experiments=tuple(experiments),
                )
                self._validate_experiment(task, stage, experiment)
                await self._store.append_experiment(experiment)
            experiments.append(experiment)

            if stage is not ExperimentStage.FALSIFICATION and self._stage_failed(task, experiment):
                decision = self._falsification.evaluate(
                    hypothesis=task.hypothesis,
                    candidate=task.candidate,
                    experiments=tuple(experiments),
                    evaluated_at=evaluated_at,
                )
                if decision.state is not CandidateState.REJECTED:
                    raise ExperimentLifecycleError(
                        "failed lifecycle stage did not produce candidate rejection"
                    )
                readiness = self._promotion.build(
                    candidate=task.candidate,
                    decision=decision,
                    rollback_version=rollback_version,
                )
                return ExperimentLifecycleResult(
                    experiments=tuple(experiments),
                    decision=decision,
                    readiness=readiness,
                    completed_stages=tuple(item.stage for item in experiments),
                )

            if stage is ExperimentStage.FALSIFICATION:
                decision = self._falsification.evaluate(
                    hypothesis=task.hypothesis,
                    candidate=task.candidate,
                    experiments=tuple(experiments),
                    evaluated_at=evaluated_at,
                )
                if decision.state is CandidateState.REJECTED:
                    readiness = self._promotion.build(
                        candidate=task.candidate,
                        decision=decision,
                        rollback_version=rollback_version,
                    )
                    return ExperimentLifecycleResult(
                        experiments=tuple(experiments),
                        decision=decision,
                        readiness=readiness,
                        completed_stages=tuple(item.stage for item in experiments),
                    )

        decision = self._falsification.evaluate(
            hypothesis=task.hypothesis,
            candidate=task.candidate,
            experiments=tuple(experiments),
            evaluated_at=evaluated_at,
        )
        readiness = self._promotion.build(
            candidate=task.candidate,
            decision=decision,
            rollback_version=rollback_version,
        )
        if readiness.state is PromotionReadinessState.SHADOW_READY:
            if tuple(item.stage for item in experiments) != REQUIRED_EXPERIMENT_STAGES:
                raise ExperimentLifecycleError(
                    "SHADOW_READY requires the complete mandatory lifecycle"
                )
        return ExperimentLifecycleResult(
            experiments=tuple(experiments),
            decision=decision,
            readiness=readiness,
            completed_stages=tuple(item.stage for item in experiments),
        )

    @staticmethod
    def _stage_failed(task: ResearchTask, experiment: ExperimentRecord) -> bool:
        criteria = {item.check: item.minimum_score for item in task.hypothesis.criteria}
        return any(
            item.outcome is not ValidationOutcome.PASS
            or item.score < criteria[item.check]
            for item in experiment.results
        )

    def _validate_persisted(
        self,
        task: ResearchTask,
        experiments: tuple[ExperimentRecord, ...],
    ) -> dict[ExperimentStage, ExperimentRecord]:
        by_stage: dict[ExperimentStage, ExperimentRecord] = {}
        max_index = -1
        for experiment in experiments:
            if experiment.stage not in REQUIRED_EXPERIMENT_STAGES:
                raise ExperimentLifecycleError(
                    "persisted experiment stage is outside the canonical lifecycle"
                )
            self._validate_experiment(task, experiment.stage, experiment)
            if experiment.stage in by_stage:
                raise ExperimentLifecycleError(
                    "candidate has duplicate immutable evidence for one lifecycle stage"
                )
            index = REQUIRED_EXPERIMENT_STAGES.index(experiment.stage)
            if index != max_index + 1:
                raise ExperimentLifecycleError(
                    "persisted experiment lifecycle contains a stage gap or reordering"
                )
            by_stage[experiment.stage] = experiment
            max_index = index
            if self._stage_failed(task, experiment):
                if len(experiments) != len(by_stage):
                    raise ExperimentLifecycleError(
                        "rejected candidate cannot have evidence after a failed stage"
                    )
                break
        return by_stage

    @staticmethod
    def _validate_experiment(
        task: ResearchTask,
        expected_stage: ExperimentStage,
        experiment: ExperimentRecord,
    ) -> None:
        if experiment.stage is not expected_stage:
            raise ExperimentLifecycleError("research worker returned wrong lifecycle stage")
        if (
            experiment.workspace_id != task.workspace_id
            or experiment.user_id != task.user_id
        ):
            raise ExperimentLifecycleError("research worker returned cross-tenant evidence")
        if experiment.candidate_id != task.candidate.candidate_id:
            raise ExperimentLifecycleError("research worker candidate mismatch")
        if experiment.hypothesis_id != task.hypothesis.hypothesis_id:
            raise ExperimentLifecycleError("research worker hypothesis mismatch")
        if experiment.dataset_hash != task.candidate.dataset.content_hash:
            raise ExperimentLifecycleError("research worker dataset lineage mismatch")
        if experiment.code_hash != task.candidate.code_hash:
            raise ExperimentLifecycleError("research worker code lineage mismatch")
        if experiment.environment_digest != task.candidate.environment_digest:
            raise ExperimentLifecycleError("research worker environment lineage mismatch")
        if experiment.cost_model_version != task.candidate.cost_model_version:
            raise ExperimentLifecycleError("research worker cost-model lineage mismatch")
