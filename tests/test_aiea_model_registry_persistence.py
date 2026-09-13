"""Fresh-session persistence tests for the canonical AIEA model registry."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.aiea.application.model_registry import (
    DurableModelRegistry,
    ModelRegistryService,
)
from apps.aiea.domain.research import (
    CandidateVersion,
    DatasetLineage,
    PromotionReadiness,
    PromotionReadinessState,
)
from infra.persistence.application.aiea import AIEAResearchRecordStore
from infra.persistence.base import PersistenceBase
from infra.persistence.models.aiea import AIEAResearchRecordModel
from infra.persistence.repositories.aiea import AIEAResearchRecordRepository


NOW = datetime(2026, 9, 13, 21, 0, tzinfo=UTC)


def _entry(*, workspace_id: str = "ws-1", user_id: int = 7):
    candidate = CandidateVersion(
        candidate_id="cand-1",
        workspace_id=workspace_id,
        user_id=user_id,
        hypothesis_id="hyp-1",
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
    readiness = PromotionReadiness(
        readiness_id="ready-1",
        workspace_id=workspace_id,
        user_id=user_id,
        strategy_id="trend-v2",
        candidate_version="2.1.0",
        candidate_id="cand-1",
        dataset_hash="dataset-hash",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        evidence_hashes=("evidence-a", "evidence-b"),
        rollback_version="2.0.0",
        state=PromotionReadinessState.SHADOW_READY,
    )
    return ModelRegistryService.build(
        candidate=candidate,
        readiness=readiness,
        model_hash="model-hash",
        hyperparameters={"lookback": 20, "threshold": "0.5"},
        result_hash="result-hash",
    )


def test_model_registry_survives_fresh_session_and_is_owner_scoped() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            registry = DurableModelRegistry(store)
            await registry.register(_entry())
            await registry.register(_entry())
            await session.commit()

        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            registry = DurableModelRegistry(store)
            restored = await registry.get(
                workspace_id="ws-1",
                user_id=7,
                strategy_id="trend-v2",
                version="2.1.0",
            )
            hidden = await registry.get(
                workspace_id="ws-1",
                user_id=8,
                strategy_id="trend-v2",
                version="2.1.0",
            )
            owner = await registry.list_for_owner(workspace_id="ws-1", user_id=7)
            other = await registry.list_for_owner(workspace_id="ws-2", user_id=7)
        await engine.dispose()
        return restored, hidden, owner, other

    restored, hidden, owner, other = asyncio.run(scenario())
    assert restored == _entry()
    assert restored is not None and restored.created_at.tzinfo is not None
    assert hidden is None
    assert owner == (_entry(),)
    assert other == ()


def test_model_registry_conflicting_re_registration_fails_closed() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        raised = False
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            registry = DurableModelRegistry(store)
            entry = _entry()
            await registry.register(entry)
            conflicting = ModelRegistryService.build(
                candidate=CandidateVersion(
                    candidate_id="cand-1",
                    workspace_id=entry.workspace_id,
                    user_id=entry.user_id,
                    hypothesis_id="hyp-1",
                    strategy_id=entry.strategy_id,
                    version=entry.version,
                    parent_version=entry.parent_version,
                    before_spec_hash="before-hash",
                    after_spec_hash="after-hash",
                    reason="bounded research improvement",
                    expected_effect="better stability",
                    code_hash=entry.code_hash,
                    environment_digest=entry.environment_digest,
                    cost_model_version=entry.cost_model_version,
                    dataset=DatasetLineage(
                        dataset_id=entry.dataset_id,
                        version=entry.dataset_version,
                        content_hash=entry.dataset_hash,
                        feature_definition_hash=entry.feature_definition_hash,
                        train_interval=entry.train_interval,
                        validation_interval=entry.validation_interval,
                        test_interval=entry.test_interval,
                    ),
                    created_at=entry.created_at,
                ),
                readiness=PromotionReadiness(
                    readiness_id="ready-1",
                    workspace_id=entry.workspace_id,
                    user_id=entry.user_id,
                    strategy_id=entry.strategy_id,
                    candidate_version=entry.version,
                    candidate_id=entry.candidate_id,
                    dataset_hash=entry.dataset_hash,
                    code_hash=entry.code_hash,
                    environment_digest=entry.environment_digest,
                    evidence_hashes=entry.evidence_hashes,
                    rollback_version=entry.rollback_target,
                    state=PromotionReadinessState.SHADOW_READY,
                ),
                model_hash="different-model-hash",
                hyperparameters=entry.hyperparameters,
                result_hash=entry.result_hash,
            )
            try:
                await registry.register(conflicting)
            except ValueError:
                raised = True
        await engine.dispose()
        return raised

    assert asyncio.run(scenario()) is True
