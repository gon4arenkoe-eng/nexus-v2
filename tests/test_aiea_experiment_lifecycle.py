"""Focused tests for the canonical AIEA experiment lifecycle orchestrator."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.aiea.application.experiment_lifecycle import (
    AIEAExperimentLifecycleOrchestrator,
    ExperimentLifecycleError,
    REQUIRED_EXPERIMENT_STAGES,
)
from apps.aiea.application.research_loop import ResearchSandboxPolicy, ResearchTask
from apps.aiea.domain.research import (
    CandidateState,
    CandidateVersion,
    DatasetLineage,
    ExperimentRecord,
    ExperimentStage,
    FalsificationCheck,
    FalsificationCriterion,
    Hypothesis,
    KnowledgeSnapshot,
    PromotionReadinessState,
    ValidationOutcome,
    ValidationResult,
)

NOW = datetime(2026, 9, 13, 20, 0, tzinfo=UTC)


def _criteria() -> tuple[FalsificationCriterion, ...]:
    return tuple(
        FalsificationCriterion(
            check=check,
            minimum_score=Decimal("0.70"),
            rationale=f"reject weak {check.value.lower()}",
        )
        for check in FalsificationCheck
    )


def _task() -> ResearchTask:
    snapshot = KnowledgeSnapshot(
        snapshot_id="snapshot-1",
        workspace_id="ws-1",
        user_id=7,
        created_at=NOW,
        evidence_ids=("evidence-1",),
        content_hash="snapshot-hash",
    )
    hypothesis = Hypothesis(
        hypothesis_id="hyp-1",
        workspace_id="ws-1",
        user_id=7,
        snapshot_id=snapshot.snapshot_id,
        statement="A bounded candidate should survive only complete staged validation.",
        expected_effect="Improve OOS stability after realistic costs.",
        created_at=NOW,
        criteria=_criteria(),
    )
    candidate = CandidateVersion(
        candidate_id="cand-1",
        workspace_id="ws-1",
        user_id=7,
        hypothesis_id=hypothesis.hypothesis_id,
        strategy_id="trend-v2",
        version="2.1.0",
        parent_version="2.0.0",
        before_spec_hash="before-hash",
        after_spec_hash="after-hash",
        reason="bounded research improvement",
        expected_effect="better stability",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        dataset=DatasetLineage(
            dataset_id="btc-1m",
            version="v3",
            content_hash="dataset-hash",
            feature_definition_hash="feature-hash",
            train_interval="2024",
            validation_interval="2025-H1",
            test_interval="2025-H2",
        ),
        created_at=NOW,
    )
    return ResearchTask(
        task_id="task-1",
        workspace_id="ws-1",
        user_id=7,
        hypothesis=hypothesis,
        candidate=candidate,
        knowledge_snapshot=snapshot,
        policy=ResearchSandboxPolicy(
            max_wall_seconds=900,
            max_memory_mb=4096,
            max_cpu_cores=4,
            allowed_dependencies=("numpy", "pandas"),
        ),
    )


def _result(
    check: FalsificationCheck,
    *,
    outcome: ValidationOutcome = ValidationOutcome.PASS,
) -> ValidationResult:
    return ValidationResult(
        check=check,
        outcome=outcome,
        score=Decimal("0.90") if outcome is ValidationOutcome.PASS else Decimal("0.10"),
        evidence_hash=f"evidence-{check.value.lower()}-{outcome.value.lower()}",
        detail=outcome.value.lower(),
    )


def _experiment(
    stage: ExperimentStage,
    *,
    failing: FalsificationCheck | None = None,
    candidate_id: str = "cand-1",
) -> ExperimentRecord:
    if stage is ExperimentStage.FALSIFICATION:
        results = tuple(
            _result(
                check,
                outcome=(
                    ValidationOutcome.FAIL
                    if check is failing
                    else ValidationOutcome.PASS
                ),
            )
            for check in FalsificationCheck
        )
    else:
        check_by_stage = {
            ExperimentStage.BACKTEST: FalsificationCheck.REALISTIC_COSTS,
            ExperimentStage.OOS: FalsificationCheck.OOS,
            ExperimentStage.WALK_FORWARD: FalsificationCheck.WALK_FORWARD,
            ExperimentStage.REGIME_SLICES: FalsificationCheck.REGIME_STABILITY,
            ExperimentStage.PAPER: FalsificationCheck.MINIMUM_SAMPLE,
            ExperimentStage.SHADOW: FalsificationCheck.DATA_QUALITY,
            ExperimentStage.COMPARISON: FalsificationCheck.FALSE_DISCOVERY,
        }
        check = check_by_stage[stage]
        results = (
            _result(
                check,
                outcome=(
                    ValidationOutcome.FAIL if check is failing else ValidationOutcome.PASS
                ),
            ),
        )
    index = REQUIRED_EXPERIMENT_STAGES.index(stage)
    at = NOW + timedelta(minutes=index + 1)
    return ExperimentRecord(
        experiment_id=f"exp-{index + 1}-{stage.value.lower()}",
        workspace_id="ws-1",
        user_id=7,
        hypothesis_id="hyp-1",
        candidate_id=candidate_id,
        stage=stage,
        started_at=at,
        completed_at=at,
        dataset_hash="dataset-hash",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        results=results,
        metrics={"score": Decimal("0.90")},
    )


class Store:
    def __init__(self, persisted: tuple[ExperimentRecord, ...] = ()) -> None:
        self.persisted = list(persisted)
        self.appended: list[ExperimentRecord] = []

    async def append_snapshot(self, value) -> None:  # noqa: ANN001
        self.snapshot = value

    async def append_evidence(self, value) -> None:  # noqa: ANN001
        return None

    async def append_memory(self, value) -> None:  # noqa: ANN001
        return None

    async def append_hypothesis(self, value) -> None:  # noqa: ANN001
        self.hypothesis = value

    async def append_candidate(self, value) -> None:  # noqa: ANN001
        self.candidate = value

    async def append_experiment(self, value: ExperimentRecord) -> None:
        self.appended.append(value)
        self.persisted.append(value)

    async def append_artifact(self, value) -> None:  # noqa: ANN001
        return None

    async def list_experiments_for_candidate(self, **kwargs) -> tuple[ExperimentRecord, ...]:  # noqa: ANN003
        return tuple(self.persisted)

    async def list_record_ids(self, **kwargs) -> tuple[str, ...]:  # noqa: ANN003
        return ()


class Worker:
    def __init__(
        self,
        *,
        fail_stage: ExperimentStage | None = None,
        wrong_stage: bool = False,
    ) -> None:
        self.fail_stage = fail_stage
        self.wrong_stage = wrong_stage
        self.calls: list[ExperimentStage] = []

    async def execute_stage(
        self,
        task: ResearchTask,
        *,
        stage: ExperimentStage,
        prior_experiments: tuple[ExperimentRecord, ...],
    ) -> ExperimentRecord:
        assert tuple(item.stage for item in prior_experiments[-len(self.calls):]) == tuple(self.calls) if self.calls else True
        self.calls.append(stage)
        actual_stage = ExperimentStage.OOS if self.wrong_stage else stage
        failing = None
        if stage is self.fail_stage:
            failing = {
                ExperimentStage.BACKTEST: FalsificationCheck.REALISTIC_COSTS,
                ExperimentStage.OOS: FalsificationCheck.OOS,
                ExperimentStage.WALK_FORWARD: FalsificationCheck.WALK_FORWARD,
                ExperimentStage.REGIME_SLICES: FalsificationCheck.REGIME_STABILITY,
                ExperimentStage.FALSIFICATION: FalsificationCheck.LOOKAHEAD_LEAKAGE,
                ExperimentStage.PAPER: FalsificationCheck.MINIMUM_SAMPLE,
                ExperimentStage.SHADOW: FalsificationCheck.DATA_QUALITY,
                ExperimentStage.COMPARISON: FalsificationCheck.FALSE_DISCOVERY,
            }[stage]
        return _experiment(actual_stage, failing=failing)


def test_complete_lifecycle_is_required_before_shadow_readiness() -> None:
    async def scenario():
        store = Store()
        worker = Worker()
        result = await AIEAExperimentLifecycleOrchestrator(
            store=store, worker=worker
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")
        return store, worker, result

    store, worker, result = asyncio.run(scenario())
    assert tuple(worker.calls) == REQUIRED_EXPERIMENT_STAGES
    assert result.completed_stages == REQUIRED_EXPERIMENT_STAGES
    assert result.decision.state is CandidateState.SHADOW_READY
    assert result.readiness.state is PromotionReadinessState.SHADOW_READY
    assert len(store.appended) == len(REQUIRED_EXPERIMENT_STAGES)


def test_failed_stage_stops_candidate_and_never_runs_later_stage() -> None:
    async def scenario():
        worker = Worker(fail_stage=ExperimentStage.OOS)
        result = await AIEAExperimentLifecycleOrchestrator(
            store=Store(), worker=worker
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")
        return worker, result

    worker, result = asyncio.run(scenario())
    assert worker.calls == [ExperimentStage.BACKTEST, ExperimentStage.OOS]
    assert result.decision.state is CandidateState.REJECTED
    assert result.readiness.state is PromotionReadinessState.REJECTED


def test_falsification_rejection_stops_before_paper() -> None:
    async def scenario():
        worker = Worker(fail_stage=ExperimentStage.FALSIFICATION)
        result = await AIEAExperimentLifecycleOrchestrator(
            store=Store(), worker=worker
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")
        return worker, result

    worker, result = asyncio.run(scenario())
    assert worker.calls[-1] is ExperimentStage.FALSIFICATION
    assert ExperimentStage.PAPER not in worker.calls
    assert result.decision.state is CandidateState.REJECTED


def test_worker_cannot_return_wrong_stage() -> None:
    async def scenario():
        await AIEAExperimentLifecycleOrchestrator(
            store=Store(), worker=Worker(wrong_stage=True)
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")

    with pytest.raises(ExperimentLifecycleError, match="wrong lifecycle stage"):
        asyncio.run(scenario())


def test_resume_is_idempotent_and_does_not_rerun_persisted_stages() -> None:
    persisted = tuple(_experiment(stage) for stage in REQUIRED_EXPERIMENT_STAGES[:4])

    async def scenario():
        store = Store(persisted)
        worker = Worker()
        result = await AIEAExperimentLifecycleOrchestrator(
            store=store, worker=worker
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")
        return store, worker, result

    store, worker, result = asyncio.run(scenario())
    assert worker.calls == list(REQUIRED_EXPERIMENT_STAGES[4:])
    assert len(store.appended) == 4
    assert result.completed_stages == REQUIRED_EXPERIMENT_STAGES


def test_persisted_stage_gap_is_fail_closed() -> None:
    persisted = (
        _experiment(ExperimentStage.BACKTEST),
        _experiment(ExperimentStage.WALK_FORWARD),
    )

    async def scenario():
        await AIEAExperimentLifecycleOrchestrator(
            store=Store(persisted), worker=Worker()
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")

    with pytest.raises(ExperimentLifecycleError, match="stage gap"):
        asyncio.run(scenario())


def test_persisted_cross_candidate_evidence_is_fail_closed() -> None:
    persisted = (_experiment(ExperimentStage.BACKTEST, candidate_id="other"),)

    async def scenario():
        await AIEAExperimentLifecycleOrchestrator(
            store=Store(persisted), worker=Worker()
        ).run(_task(), evaluated_at=NOW, rollback_version="2.0.0")

    with pytest.raises(ExperimentLifecycleError, match="candidate mismatch"):
        asyncio.run(scenario())
