from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.aiea.application.drift_monitor import DurableDriftEvidence, DriftMonitorService, DriftObservation
from infra.persistence.application.aiea import AIEAResearchRecordStore
from infra.persistence.base import PersistenceBase
from infra.persistence.models.aiea import AIEAResearchRecordModel
from infra.persistence.repositories.aiea import AIEAResearchRecordRepository

NOW = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)


def _decision(workspace_id="ws-1", user_id=7):
    return DriftMonitorService().assess(DriftObservation(
        workspace_id=workspace_id, user_id=user_id, strategy_id="trend-v2",
        champion_version="2.0.0", challenger_version="2.1.0",
        observed_at=NOW, evidence_at=NOW - timedelta(hours=2),
        baseline_score=Decimal("1"), current_score=Decimal("0.60"),
        challenger_score=Decimal("0.70"), evidence_hash="champ-evidence",
        challenger_evidence_hash="chall-evidence",
    ))


def test_drift_evidence_survives_fresh_session_and_is_tenant_scoped() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(PersistenceBase.metadata.create_all, tables=(AIEAResearchRecordModel.__table__,))
        expected = _decision()
        async with factory() as session:
            durable = DurableDriftEvidence(AIEAResearchRecordStore(AIEAResearchRecordRepository(session)))
            await durable.append(expected)
            await durable.append(expected)
            await session.commit()
        async with factory() as session:
            durable = DurableDriftEvidence(AIEAResearchRecordStore(AIEAResearchRecordRepository(session)))
            owner = await durable.list_for_owner(workspace_id="ws-1", user_id=7)
            other_user = await durable.list_for_owner(workspace_id="ws-1", user_id=8)
            other_workspace = await durable.list_for_owner(workspace_id="ws-2", user_id=7)
        await engine.dispose()
        return expected, owner, other_user, other_workspace
    expected, owner, other_user, other_workspace = asyncio.run(scenario())
    assert owner == (expected,)
    assert other_user == ()
    assert other_workspace == ()
