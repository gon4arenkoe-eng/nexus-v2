from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.aiea.adapters.historical_replay import InMemoryCandleReplaySource, synthetic_ohlcv
from apps.aiea.adapters.stage_research_worker import BacktestConfig, DeterministicStageResearchWorker
from apps.aiea.application.experiment_lifecycle import REQUIRED_EXPERIMENT_STAGES
from apps.aiea.application.research_loop import ResearchSandboxPolicy, ResearchTask
from apps.aiea.domain.research import (
    CandidateVersion,
    DatasetLineage,
    ExperimentStage,
    FalsificationCheck,
    FalsificationCriterion,
    Hypothesis,
    KnowledgeSnapshot,
    ValidationOutcome,
)
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 22, 0, tzinfo=UTC)


def _instrument() -> InstrumentId:
    return InstrumentId(
        venue_id=VenueId("BINGX"),
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _criteria() -> tuple[FalsificationCriterion, ...]:
    return tuple(
        FalsificationCriterion(
            check=check,
            minimum_score=Decimal("0"),
            rationale="deterministic stage worker contract",
        )
        for check in FalsificationCheck
    )


def _task(*, overlapping: bool = False) -> ResearchTask:
    snapshot = KnowledgeSnapshot(
        snapshot_id="snapshot-worker",
        workspace_id="ws-1",
        user_id=7,
        created_at=NOW,
        evidence_ids=("evidence-1",),
        content_hash="snapshot-hash",
    )
    hypothesis = Hypothesis(
        hypothesis_id="hyp-worker",
        workspace_id="ws-1",
        user_id=7,
        snapshot_id=snapshot.snapshot_id,
        statement="deterministic stage-aware research must be falsifiable",
        expected_effect="produce reproducible stage evidence",
        created_at=NOW,
        criteria=_criteria(),
    )
    train = "bars:0:360"
    validation = "bars:300:480" if overlapping else "bars:360:480"
    candidate = CandidateVersion(
        candidate_id="cand-worker",
        workspace_id="ws-1",
        user_id=7,
        hypothesis_id=hypothesis.hypothesis_id,
        strategy_id="trend-continuation",
        version="1.1.0",
        parent_version="1.0.0",
        before_spec_hash="before",
        after_spec_hash="after",
        reason="test deterministic stage worker",
        expected_effect="reproducible evidence",
        code_hash="code-hash",
        environment_digest="sha256:research-worker",
        cost_model_version="cost-v1",
        dataset=DatasetLineage(
            dataset_id="synthetic-btc-1h",
            version="seed-11",
            content_hash="dataset-hash",
            feature_definition_hash="feature-hash",
            train_interval=train,
            validation_interval=validation,
            test_interval="bars:480:720",
        ),
        created_at=NOW,
    )
    return ResearchTask(
        task_id="task-worker",
        workspace_id="ws-1",
        user_id=7,
        hypothesis=hypothesis,
        candidate=candidate,
        knowledge_snapshot=snapshot,
        policy=ResearchSandboxPolicy(
            max_wall_seconds=120,
            max_memory_mb=1024,
            max_cpu_cores=1,
            allowed_dependencies=("stdlib",),
        ),
    )


def _worker() -> DeterministicStageResearchWorker:
    instrument = _instrument()
    candles = synthetic_ohlcv(instrument_id=instrument, seed=11, bars=720)
    return DeterministicStageResearchWorker(
        source=InMemoryCandleReplaySource.single_symbol(instrument, candles),
        instrument_id=instrument,
        config=BacktestConfig(),
    )


def test_all_required_lifecycle_stages_are_supported_and_lineage_bound() -> None:
    task = _task()
    worker = _worker()

    async def scenario():
        prior = []
        values = []
        for stage in REQUIRED_EXPERIMENT_STAGES:
            result = await worker.execute_stage(task, stage=stage, prior_experiments=tuple(prior))
            values.append(result)
            prior.append(result)
        return values

    values = asyncio.run(scenario())
    assert tuple(item.stage for item in values) == REQUIRED_EXPERIMENT_STAGES
    assert all(item.dataset_hash == task.candidate.dataset.content_hash for item in values)
    assert all(item.code_hash == task.candidate.code_hash for item in values)
    assert all(item.environment_digest == task.candidate.environment_digest for item in values)
    assert all(item.cost_model_version == task.candidate.cost_model_version for item in values)
    assert values[-1].metrics["prior_stage_count"] == Decimal("7")


def test_falsification_stage_runs_all_mandatory_checks() -> None:
    result = asyncio.run(
        _worker().execute_stage(
            _task(), stage=ExperimentStage.FALSIFICATION, prior_experiments=()
        )
    )
    assert {item.check for item in result.results} == frozenset(FalsificationCheck)


def test_stage_worker_is_deterministic() -> None:
    first = asyncio.run(_worker().execute_stage(_task(), stage=ExperimentStage.WALK_FORWARD, prior_experiments=()))
    second = asyncio.run(_worker().execute_stage(_task(), stage=ExperimentStage.WALK_FORWARD, prior_experiments=()))
    assert first.results == second.results
    assert first.metrics == second.metrics


def test_backtest_stage_detects_holdout_overlap() -> None:
    result = asyncio.run(
        _worker().execute_stage(_task(overlapping=True), stage=ExperimentStage.BACKTEST, prior_experiments=())
    )
    holdout = next(item for item in result.results if item.check is FalsificationCheck.HOLDOUT_ISOLATION)
    assert holdout.outcome is ValidationOutcome.FAIL
    assert holdout.score == Decimal("0")


def test_worker_refuses_noncanonical_static_data_stage() -> None:
    with pytest.raises(ValueError, match="unsupported lifecycle stage"):
        asyncio.run(
            _worker().execute_stage(_task(), stage=ExperimentStage.STATIC_DATA, prior_experiments=())
        )


def test_existing_lifecycle_orchestrator_consumes_real_stage_worker() -> None:
    from apps.aiea.application.experiment_lifecycle import AIEAExperimentLifecycleOrchestrator

    class Store:
        def __init__(self) -> None:
            self.experiments = []
        async def append_snapshot(self, value): self.snapshot = value
        async def append_evidence(self, value): return None
        async def append_memory(self, value): return None
        async def append_hypothesis(self, value): self.hypothesis = value
        async def append_candidate(self, value): self.candidate = value
        async def append_experiment(self, value): self.experiments.append(value)
        async def append_artifact(self, value): return None
        async def list_experiments_for_candidate(self, **kwargs): return tuple(self.experiments)
        async def list_record_ids(self, **kwargs): return ()
        async def get_artifact(self, **kwargs): return None
        async def list_artifacts_for_owner(self, **kwargs): return ()

    async def scenario():
        store = Store()
        result = await AIEAExperimentLifecycleOrchestrator(
            store=store,
            worker=_worker(),
        ).run(_task(), evaluated_at=NOW, rollback_version="1.0.0")
        return store, result

    store, result = asyncio.run(scenario())
    assert store.experiments
    assert result.completed_stages == tuple(item.stage for item in store.experiments)
    assert result.completed_stages[0] is ExperimentStage.BACKTEST
