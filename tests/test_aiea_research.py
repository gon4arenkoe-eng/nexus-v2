"""Focused Phase 9 AIEA research/evolution tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from apps.aiea.application.research_loop import (
    AIEAResearchCoordinator,
    ChampionChallengerService,
    FalsificationEngine,
    PromotionReadinessService,
    ResearchSandboxPolicy,
    ResearchTask,
    build_lesson_memory,
)
from apps.aiea.domain.research import (
    ArtifactKind,
    CandidateState,
    CandidateVersion,
    DatasetLineage,
    DriftState,
    ExperimentRecord,
    ExperimentStage,
    FalsificationCheck,
    FalsificationCriterion,
    Hypothesis,
    KnowledgeSnapshot,
    PromotionReadinessState,
    ResearchArtifact,
    ValidationOutcome,
    ValidationResult,
)
from workers.aiea_research.policy import (
    ResearchCodeSubmission,
    validate_submission,
)

NOW = datetime(2026, 9, 12, 19, 30, tzinfo=UTC)


def _dataset() -> DatasetLineage:
    return DatasetLineage(
        dataset_id="btc-perp-1m",
        version="v3",
        content_hash="dataset-hash",
        feature_definition_hash="feature-hash",
        train_interval="2024-01/2024-12",
        validation_interval="2025-01/2025-06",
        test_interval="2025-07/2025-12",
    )


def _criteria() -> tuple[FalsificationCriterion, ...]:
    return tuple(
        FalsificationCriterion(
            check=check,
            minimum_score=Decimal("0.70"),
            rationale=f"reject weak {check.value.lower()}",
        )
        for check in FalsificationCheck
    )


def _snapshot(*, workspace_id: str = "ws-1", user_id: int = 7) -> KnowledgeSnapshot:  # noqa: E501
    return KnowledgeSnapshot(
        snapshot_id="snapshot-1",
        workspace_id=workspace_id,
        user_id=user_id,
        created_at=NOW,
        evidence_ids=("evidence-1", "evidence-2"),
        content_hash="snapshot-hash",
    )


def _hypothesis(*, workspace_id: str = "ws-1", user_id: int = 7) -> Hypothesis:
    return Hypothesis(
        hypothesis_id="hyp-1",
        workspace_id=workspace_id,
        user_id=user_id,
        snapshot_id="snapshot-1",
        statement="Funding dislocations mean revert after liquidity normalizes.",  # noqa: E501
        expected_effect="Improve OOS expectancy after costs.",
        created_at=NOW,
        criteria=_criteria(),
    )


def _candidate(*, workspace_id: str = "ws-1", user_id: int = 7) -> CandidateVersion:  # noqa: E501
    return CandidateVersion(
        candidate_id="cand-1",
        workspace_id=workspace_id,
        user_id=user_id,
        hypothesis_id="hyp-1",
        strategy_id="funding-carry",
        version="2.1.0",
        parent_version="2.0.0",
        before_spec_hash="before-hash",
        after_spec_hash="after-hash",
        reason="Reduce unstable entry sensitivity.",
        expected_effect="Higher cross-regime stability.",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        dataset=_dataset(),
        created_at=NOW,
    )


def _results(*, failing: FalsificationCheck | None = None) -> tuple[ValidationResult, ...]:  # noqa: E501
    values = []
    for check in FalsificationCheck:
        failed = check is failing
        values.append(
            ValidationResult(
                check=check,
                outcome=ValidationOutcome.FAIL if failed else ValidationOutcome.PASS,  # noqa: E501
                score=Decimal("0.20") if failed else Decimal("0.90"),
                evidence_hash=f"evidence-{check.value.lower()}",
                detail="failed" if failed else "passed",
            )
        )
    return tuple(values)


def _experiment(
    *,
    results: tuple[ValidationResult, ...] | None = None,
    workspace_id: str = "ws-1",
    user_id: int = 7,
) -> ExperimentRecord:
    return ExperimentRecord(
        experiment_id="exp-1",
        workspace_id=workspace_id,
        user_id=user_id,
        hypothesis_id="hyp-1",
        candidate_id="cand-1",
        stage=ExperimentStage.FALSIFICATION,
        started_at=NOW,
        completed_at=NOW,
        dataset_hash="dataset-hash",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        results=_results() if results is None else results,
        metrics={"oos_expectancy": Decimal("0.12")},
    )


def _policy() -> ResearchSandboxPolicy:
    return ResearchSandboxPolicy(
        max_wall_seconds=900,
        max_memory_mb=4096,
        max_cpu_cores=4,
        allowed_dependencies=("numpy", "pandas", "scikit-learn"),
    )


def test_hypothesis_requires_every_mandatory_falsification_check() -> None:
    criteria = _criteria()[:-1]
    with pytest.raises(ValueError, match="missing mandatory falsification"):
        Hypothesis(
            hypothesis_id="hyp-x",
            workspace_id="ws-1",
            user_id=7,
            snapshot_id="snapshot-1",
            statement="test",
            expected_effect="test",
            created_at=NOW,
            criteria=criteria,
        )


def test_candidate_version_is_immutable_parent_child_delta() -> None:
    with pytest.raises(ValueError, match="before/after"):
        CandidateVersion(
            candidate_id="cand-x",
            workspace_id="ws-1",
            user_id=7,
            hypothesis_id="hyp-1",
            strategy_id="s",
            version="2",
            parent_version="1",
            before_spec_hash="same",
            after_spec_hash="same",
            reason="test",
            expected_effect="test",
            code_hash="code",
            environment_digest="image",
            cost_model_version="cost",
            dataset=_dataset(),
            created_at=NOW,
        )


def test_falsification_all_checks_pass_only_to_shadow_ready() -> None:
    decision = FalsificationEngine().evaluate(
        hypothesis=_hypothesis(),
        candidate=_candidate(),
        experiments=(_experiment(),),
        evaluated_at=NOW,
    )
    assert decision.state is CandidateState.SHADOW_READY
    assert decision.failed_checks == ()


def test_falsification_rejects_one_failed_gate() -> None:
    check = FalsificationCheck.LOOKAHEAD_LEAKAGE
    decision = FalsificationEngine().evaluate(
        hypothesis=_hypothesis(),
        candidate=_candidate(),
        experiments=(_experiment(results=_results(failing=check)),),
        evaluated_at=NOW,
    )
    assert decision.state is CandidateState.REJECTED
    assert check in decision.failed_checks


def test_falsification_rejects_missing_gate_evidence() -> None:
    decision = FalsificationEngine().evaluate(
        hypothesis=_hypothesis(),
        candidate=_candidate(),
        experiments=(_experiment(results=_results()[:-1]),),
        evaluated_at=NOW,
    )
    assert decision.state is CandidateState.REJECTED
    assert FalsificationCheck.FALSE_DISCOVERY in decision.failed_checks


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("dataset_hash", "wrong", "dataset hash"),
        ("code_hash", "wrong", "code hash"),
        ("environment_digest", "wrong", "environment digest"),
        ("cost_model_version", "wrong", "cost model"),
    ),
)
def test_falsification_binds_exact_reproducibility_identity(
    field: str,
    value: str,
    message: str,
) -> None:
    kwargs = dict(
        experiment_id="exp-1",
        workspace_id="ws-1",
        user_id=7,
        hypothesis_id="hyp-1",
        candidate_id="cand-1",
        stage=ExperimentStage.FALSIFICATION,
        started_at=NOW,
        completed_at=NOW,
        dataset_hash="dataset-hash",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        results=_results(),
    )
    kwargs[field] = value
    experiment = ExperimentRecord(**kwargs)
    with pytest.raises(ValueError, match=message):
        FalsificationEngine().evaluate(
            hypothesis=_hypothesis(),
            candidate=_candidate(),
            experiments=(experiment,),
            evaluated_at=NOW,
        )


def test_cross_tenant_experiment_is_rejected() -> None:
    with pytest.raises(ValueError, match="cross-tenant"):
        FalsificationEngine().evaluate(
            hypothesis=_hypothesis(),
            candidate=_candidate(),
            experiments=(_experiment(workspace_id="ws-2"),),
            evaluated_at=NOW,
        )


def test_promotion_readiness_is_shadow_only_and_keeps_independent_approvals() -> None:  # noqa: E501
    decision = FalsificationEngine().evaluate(
        hypothesis=_hypothesis(),
        candidate=_candidate(),
        experiments=(_experiment(),),
        evaluated_at=NOW,
    )
    readiness = PromotionReadinessService().build(
        candidate=_candidate(),
        decision=decision,
        rollback_version="2.0.0",
    )
    assert readiness.state is PromotionReadinessState.SHADOW_READY
    assert readiness.risk_approval_required is True
    assert readiness.permission_approval_required is True
    assert readiness.rollback_version == "2.0.0"


def test_root_candidate_cannot_be_promotion_ready_without_rollback_parent() -> None:  # noqa: E501
    candidate = CandidateVersion(
        candidate_id="cand-root",
        workspace_id="ws-1",
        user_id=7,
        hypothesis_id="hyp-1",
        strategy_id="s",
        version="1",
        parent_version=None,
        before_spec_hash="before",
        after_spec_hash="after",
        reason="initial candidate",
        expected_effect="test",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        dataset=_dataset(),
        created_at=NOW,
    )
    decision = FalsificationEngine().evaluate(
        hypothesis=_hypothesis(),
        candidate=candidate,
        experiments=(
            ExperimentRecord(
                experiment_id="exp-root",
                workspace_id="ws-1",
                user_id=7,
                hypothesis_id="hyp-1",
                candidate_id="cand-root",
                stage=ExperimentStage.FALSIFICATION,
                started_at=NOW,
                completed_at=NOW,
                dataset_hash="dataset-hash",
                code_hash="code-hash",
                environment_digest="sha256:research-image",
                cost_model_version="cost-v2",
                results=_results(),
            ),
        ),
        evaluated_at=NOW,
    )
    readiness = PromotionReadinessService().build(
        candidate=candidate,
        decision=decision,
        rollback_version="baseline",
    )
    assert readiness.state is PromotionReadinessState.BLOCKED


@pytest.mark.parametrize(
    ("performance", "freshness", "expected"),
    (
        ("0.90", "0.90", DriftState.HEALTHY),
        ("0.65", "0.90", DriftState.WATCH),
        ("0.40", "0.90", DriftState.DEGRADED),
        ("0.90", "0.40", DriftState.UNKNOWN),
    ),
)
def test_champion_challenger_drift_is_explicit(
    performance: str,
    freshness: str,
    expected: DriftState,
) -> None:
    assessment = ChampionChallengerService().assess(
        assessment_id="drift-1",
        workspace_id="ws-1",
        user_id=7,
        strategy_id="s",
        champion_version="2.0.0",
        challenger_version="2.1.0",
        performance_ratio=Decimal(performance),
        freshness_ratio=Decimal(freshness),
        evidence_hash="drift-hash",
        observed_at=NOW,
    )
    assert assessment.state is expected


def test_research_memory_provenance_is_deterministic() -> None:
    first = build_lesson_memory(
        memory_id="memory-1",
        snapshot=_snapshot(),
        hypothesis=_hypothesis(),
        experiment=_experiment(),
        candidate=_candidate(),
        lesson="Candidate survived falsification.",
        created_at=NOW,
    )
    second = build_lesson_memory(
        memory_id="memory-2",
        snapshot=_snapshot(),
        hypothesis=_hypothesis(),
        experiment=_experiment(),
        candidate=_candidate(),
        lesson="Different wording does not alter lineage provenance.",
        created_at=NOW,
    )
    assert first.provenance_hash == second.provenance_hash


def test_research_memory_rejects_cross_tenant_lineage() -> None:
    with pytest.raises(ValueError, match="cannot cross tenants"):
        build_lesson_memory(
            memory_id="memory-x",
            snapshot=_snapshot(),
            hypothesis=_hypothesis(workspace_id="ws-2"),
            experiment=_experiment(),
            candidate=_candidate(),
            lesson="bad",
            created_at=NOW,
        )


def test_sandbox_policy_refuses_network_exchange_credentials_and_prod_writes() -> None:  # noqa: E501
    with pytest.raises(ValueError, match="network access"):
        ResearchSandboxPolicy(60, 512, 1, ("numpy",), network_allowed=True)
    with pytest.raises(ValueError, match="exchange credentials"):
        ResearchSandboxPolicy(
            60,
            512,
            1,
            ("numpy",),
            exchange_credentials_allowed=True,
        )
    with pytest.raises(ValueError, match="production filesystem"):
        ResearchSandboxPolicy(
            60,
            512,
            1,
            ("numpy",),
            production_filesystem_write_allowed=True,
        )


def test_worker_submission_requires_dependency_allowlist() -> None:
    submission = ResearchCodeSubmission(
        source_code="import numpy as np\nprint(np.mean([1, 2]))",
        declared_dependencies=("numpy", "requests"),
    )
    with pytest.raises(ValueError, match="not allowlisted"):
        validate_submission(submission, _policy())


@pytest.mark.parametrize(
    "token",
    (
        "VenueAdapter",
        "ExecutionCoordinator",
        "submit_order",
        "exchange_credentials",
    ),
)
def test_worker_submission_refuses_execution_authority_tokens(token: str) -> None:  # noqa: E501
    submission = ResearchCodeSubmission(
        source_code=f"print('{token}')",
        declared_dependencies=("numpy",),
    )
    with pytest.raises(ValueError, match="forbidden research token"):
        validate_submission(submission, _policy())


def test_research_task_is_tenant_and_lineage_scoped() -> None:
    with pytest.raises(ValueError, match="ownership mismatch"):
        ResearchTask(
            task_id="task-1",
            workspace_id="ws-2",
            user_id=7,
            hypothesis=_hypothesis(),
            candidate=_candidate(),
            knowledge_snapshot=_snapshot(),
            policy=_policy(),
        )


def test_artifact_registry_lineage_cannot_self_parent() -> None:
    with pytest.raises(ValueError, match="parent itself"):
        ResearchArtifact(
            artifact_id="artifact-1",
            workspace_id="ws-1",
            user_id=7,
            kind=ArtifactKind.MODEL,
            version="1",
            content_hash="hash",
            parent_artifact_id="artifact-1",
            created_at=NOW,
        )


def test_aiea_source_has_no_direct_execution_or_exchange_write_authority() -> None:  # noqa: E501
    root = Path(__file__).resolve().parents[1]
    files = (
        root / "apps" / "aiea" / "domain" / "research.py",
        root / "apps" / "aiea" / "application" / "research_loop.py",
        root / "apps" / "aiea" / "ports" / "research.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = (
        "from apps.core.application.execution_coordinator",
        "from apps.core.ports.venue",
        "VenueAdapter",
        "submit_order(",
        "cancel_order(",
        "api_secret",
        "SQLAlchemy",
        "sqlalchemy",
        "FastAPI",
    )
    assert not any(token in source for token in forbidden)


def test_coordinator_persists_candidate_and_experiment_but_does_not_activate() -> None:  # noqa: E501

    class Store:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def append_evidence(self, value):
            self.calls.append("evidence")

        async def append_memory(self, value):
            self.calls.append("memory")

        async def append_hypothesis(self, value):
            self.calls.append("hypothesis")

        async def append_candidate(self, value):
            self.calls.append("candidate")

        async def append_experiment(self, value):
            self.calls.append("experiment")

        async def append_artifact(self, value):
            self.calls.append("artifact")

        async def list_record_ids(self, *, workspace_id, user_id):
            return ()

    class Worker:
        async def execute(self, task):
            return _experiment()

    async def scenario():
        store = Store()
        coordinator = AIEAResearchCoordinator(store=store, worker=Worker())
        task = ResearchTask(
            task_id="task-1",
            workspace_id="ws-1",
            user_id=7,
            hypothesis=_hypothesis(),
            candidate=_candidate(),
            knowledge_snapshot=_snapshot(),
            policy=_policy(),
        )
        result = await coordinator.run_task(
            task,
            evaluated_at=NOW,
            rollback_version="2.0.0",
        )
        return store.calls, result

    calls, (_, decision, readiness) = asyncio.run(scenario())
    assert calls == ["hypothesis", "candidate", "experiment"]
    assert decision.state is CandidateState.SHADOW_READY
    assert readiness.state is PromotionReadinessState.SHADOW_READY


def test_closed_cycle_persists_evidence_hypothesis_candidate_experiment_and_lesson() -> None:  # noqa: E501
    from apps.aiea.application.research_loop import run_closed_research_cycle
    from apps.aiea.domain.research import (
        ResearchEvidence,
        ResearchEvidenceKind,
    )

    class Store:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def append_evidence(self, value):
            self.calls.append(f"evidence:{value.evidence_id}")

        async def append_memory(self, value):
            self.calls.append(f"memory:{value.memory_id}")

        async def append_hypothesis(self, value):
            self.calls.append(f"hypothesis:{value.hypothesis_id}")

        async def append_candidate(self, value):
            self.calls.append(f"candidate:{value.candidate_id}")

        async def append_experiment(self, value):
            self.calls.append(f"experiment:{value.experiment_id}")

        async def append_artifact(self, value):
            self.calls.append(f"artifact:{value.artifact_id}")

        async def list_record_ids(self, *, workspace_id, user_id):
            return ()

    class Worker:
        async def execute(self, task):
            return _experiment()

    evidence = (
        ResearchEvidence(
            evidence_id="evidence-1",
            workspace_id="ws-1",
            user_id=7,
            kind=ResearchEvidenceKind.MARKET,
            observed_at=NOW,
            content_hash="market-hash",
            source_ref="market-context:1",
        ),
        ResearchEvidence(
            evidence_id="evidence-2",
            workspace_id="ws-1",
            user_id=7,
            kind=ResearchEvidenceKind.TRADE,
            observed_at=NOW,
            content_hash="trade-hash",
            source_ref="ledger:1",
        ),
    )

    async def scenario():
        store = Store()
        task = ResearchTask(
            task_id="task-closed",
            workspace_id="ws-1",
            user_id=7,
            hypothesis=_hypothesis(),
            candidate=_candidate(),
            knowledge_snapshot=_snapshot(),
            policy=_policy(),
        )
        result = await run_closed_research_cycle(
            store=store,
            worker=Worker(),
            task=task,
            evidence=evidence,
            memory_id="memory-closed",
            lesson="Validated candidate with explicit falsification evidence.",
            evaluated_at=NOW,
            rollback_version="2.0.0",
        )
        return store.calls, result

    calls, result = asyncio.run(scenario())
    assert calls == [
        "evidence:evidence-1",
        "evidence:evidence-2",
        "hypothesis:hyp-1",
        "candidate:cand-1",
        "experiment:exp-1",
        "memory:memory-closed",
    ]
    assert result.decision.state is CandidateState.SHADOW_READY
    assert result.readiness.state is PromotionReadinessState.SHADOW_READY
    assert result.memory.hypothesis_id == "hyp-1"


def test_artifact_registry_is_owner_scoped_and_rejects_duplicate_identity() -> None:  # noqa: E501
    from apps.aiea.domain.research import ResearchArtifactRegistry

    first = ResearchArtifact(
        artifact_id="model-1",
        workspace_id="ws-1",
        user_id=7,
        kind=ArtifactKind.MODEL,
        version="1",
        content_hash="hash-1",
        parent_artifact_id=None,
        created_at=NOW,
    )
    second = ResearchArtifact(
        artifact_id="strategy-1",
        workspace_id="ws-2",
        user_id=8,
        kind=ArtifactKind.STRATEGY,
        version="1",
        content_hash="hash-2",
        parent_artifact_id=None,
        created_at=NOW,
    )
    registry = ResearchArtifactRegistry(
        registry_version="registry-v1",
        artifacts=(second, first),
    )
    assert registry.for_owner(workspace_id="ws-1", user_id=7) == (first,)
    with pytest.raises(ValueError, match="immutable and unique"):
        ResearchArtifactRegistry(
            registry_version="registry-v1",
            artifacts=(first, first),
        )
