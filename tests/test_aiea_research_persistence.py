"""Persistence/restart tests for immutable Phase 9 AIEA research records."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.aiea.domain.research import (
    ExperimentRecord,
    ExperimentStage,
    FalsificationCheck,
    ResearchEvidence,
    ResearchEvidenceKind,
    ValidationOutcome,
    ValidationResult,
)
from infra.persistence.application.aiea import AIEAResearchRecordStore
from infra.persistence.base import PersistenceBase
from infra.persistence.models.aiea import AIEAResearchRecordModel
from infra.persistence.repositories.aiea import AIEAResearchRecordRepository

NOW = datetime(2026, 9, 12, 20, 0, tzinfo=UTC)


def _evidence(
    *,
    workspace_id: str = "ws-1",
    user_id: int = 7,
    evidence_id: str = "evidence-1",
    content_hash: str = "hash-1",
) -> ResearchEvidence:
    return ResearchEvidence(
        evidence_id=evidence_id,
        workspace_id=workspace_id,
        user_id=user_id,
        kind=ResearchEvidenceKind.MARKET,
        observed_at=NOW,
        content_hash=content_hash,
        source_ref="market-context:snapshot-1",
        payload={"quality": "CURRENT"},
    )


def test_aiea_research_record_survives_fresh_session() -> None:

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))  # noqa: E501
            await store.append_evidence(_evidence())
            await session.commit()
        async with factory() as session:
            repo = AIEAResearchRecordRepository(session)
            record = await repo.get(
                workspace_id="ws-1",
                user_id=7,
                record_type="evidence",
                record_id="evidence-1",
            )
        await engine.dispose()
        return record

    record = asyncio.run(scenario())
    assert record is not None
    assert record.workspace_id == "ws-1"
    assert record.user_id == 7
    assert record.record_id == "evidence-1"
    assert record.created_at.tzinfo is not None


def test_aiea_research_store_is_workspace_and_user_scoped() -> None:

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))  # noqa: E501
            await store.append_evidence(_evidence())
            await store.append_evidence(
                _evidence(
                    workspace_id="ws-2",
                    user_id=8,
                    evidence_id="evidence-2",
                )
            )
            await session.commit()
        async with factory() as session:
            repo = AIEAResearchRecordRepository(session)
            owner = await repo.list_for_owner(workspace_id="ws-1", user_id=7)
            hidden = await repo.get(
                workspace_id="ws-1",
                user_id=7,
                record_type="evidence",
                record_id="evidence-2",
            )
        await engine.dispose()
        return owner, hidden

    owner, hidden = asyncio.run(scenario())
    assert [item.record_id for item in owner] == ["evidence-1"]
    assert hidden is None


def test_aiea_research_record_retry_is_idempotent() -> None:

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))  # noqa: E501
            value = _evidence()
            await store.append_evidence(value)
            await store.append_evidence(value)
            await session.commit()
        async with factory() as session:
            records = await AIEAResearchRecordRepository(session).list_for_owner(  # noqa: E501
                workspace_id="ws-1",
                user_id=7,
            )
        await engine.dispose()
        return records

    records = asyncio.run(scenario())
    assert len(records) == 1


def test_aiea_research_record_conflict_fails_closed() -> None:

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        raised = False
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))  # noqa: E501
            await store.append_evidence(_evidence())
            await session.flush()
            try:
                await store.append_evidence(_evidence(content_hash="different"))  # noqa: E501
            except ValueError:
                raised = True
        await engine.dispose()
        return raised

    assert asyncio.run(scenario()) is True


def test_aiea_model_registered_and_guarded() -> None:
    assert "aiea_research_records" in PersistenceBase.metadata.tables
    checks = {
        str(constraint.sqltext)
        for constraint in AIEAResearchRecordModel.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "user_id > 0" in checks


def test_aiea_store_persists_explicit_knowledge_snapshot_provenance() -> None:
    from apps.aiea.domain.research import KnowledgeSnapshot

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(AIEAResearchRecordModel.__table__,),
            )
        value = KnowledgeSnapshot(
            snapshot_id="decision-knowledge-1",
            workspace_id="ws-1",
            user_id=7,
            created_at=NOW,
            evidence_ids=("evidence-1",),
            content_hash="snapshot-content-hash",
        )
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            await store.append_snapshot(value)
            await session.commit()
        async with factory() as session:
            record = await AIEAResearchRecordRepository(session).get(
                workspace_id="ws-1", user_id=7, record_type="snapshot",
                record_id="decision-knowledge-1",
            )
        await engine.dispose()
        return record

    record = asyncio.run(scenario())
    assert record is not None
    assert record.record_type == "snapshot"
    assert record.content_hash


def test_aiea_store_rebuilds_candidate_experiments_for_lifecycle_resume() -> None:
    def experiment(stage: ExperimentStage, index: int) -> ExperimentRecord:
        return ExperimentRecord(
            experiment_id=f"resume-exp-{index}",
            workspace_id="ws-1",
            user_id=7,
            hypothesis_id="hyp-1",
            candidate_id="cand-1",
            stage=stage,
            started_at=NOW,
            completed_at=NOW,
            dataset_hash="dataset-hash",
            code_hash="code-hash",
            environment_digest="sha256:research-image",
            cost_model_version="cost-v2",
            results=(
                ValidationResult(
                    check=FalsificationCheck.REALISTIC_COSTS,
                    outcome=ValidationOutcome.PASS,
                    score=Decimal("0.90"),
                    evidence_hash=f"evidence-{index}",
                    detail="pass",
                ),
            ),
            metrics={"score": Decimal("0.90")},
        )

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
            await store.append_experiment(experiment(ExperimentStage.BACKTEST, 1))
            await store.append_experiment(experiment(ExperimentStage.OOS, 2))
            await session.commit()
        async with factory() as session:
            store = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            records = await store.list_experiments_for_candidate(
                workspace_id="ws-1", user_id=7, candidate_id="cand-1"
            )
            hidden = await store.list_experiments_for_candidate(
                workspace_id="ws-2", user_id=7, candidate_id="cand-1"
            )
        await engine.dispose()
        return records, hidden

    records, hidden = asyncio.run(scenario())
    assert tuple(item.stage for item in records) == (
        ExperimentStage.BACKTEST,
        ExperimentStage.OOS,
    )
    assert hidden == ()
