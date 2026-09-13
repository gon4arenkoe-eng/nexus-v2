"""Fresh-session persistence proof for Decision Memory -> AIEA feedback."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.aiea.application.decision_feedback import DecisionMemoryToAIEAService
from infra.persistence.application.aiea import AIEAResearchRecordStore
from infra.persistence.application.decision_intelligence import DecisionMemoryPersistenceStore
from infra.persistence.base import PersistenceBase
from infra.persistence.models.aiea import AIEAResearchRecordModel
from infra.persistence.models.decision_intelligence import DecisionIntelligenceRecordModel
from infra.persistence.repositories.aiea import AIEAResearchRecordRepository
from infra.persistence.repositories.decision_intelligence import DecisionIntelligenceRecordRepository
from tests.test_aiea_decision_feedback import NOW, _record


def test_evaluated_decision_feedback_survives_fresh_session_and_is_idempotent() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(
                    DecisionIntelligenceRecordModel.__table__,
                    AIEAResearchRecordModel.__table__,
                ),
            )

        record = _record()
        async with factory() as session:
            memory = DecisionMemoryPersistenceStore(
                DecisionIntelligenceRecordRepository(session)
            )
            await memory.append_snapshot(record.snapshot)
            await memory.append_decision(record.decision)
            assert record.outcome is not None and record.evaluation is not None
            await memory.append_outcome(
                workspace_id="ws-1", user_id=7, value=record.outcome
            )
            await memory.append_evaluation(
                workspace_id="ws-1", user_id=7, value=record.evaluation
            )
            await session.commit()

        async with factory() as session:
            memory = DecisionMemoryPersistenceStore(
                DecisionIntelligenceRecordRepository(session)
            )
            research = AIEAResearchRecordStore(AIEAResearchRecordRepository(session))
            service = DecisionMemoryToAIEAService(memory=memory, research=research)
            first = await service.publish(
                workspace_id="ws-1", user_id=7, decision_id="decision-1",
                observed_at=NOW,
            )
            second = await service.publish(
                workspace_id="ws-1", user_id=7, decision_id="decision-1",
                observed_at=NOW,
            )
            await session.commit()

        async with factory() as session:
            records = await AIEAResearchRecordRepository(session).list_for_owner(
                workspace_id="ws-1", user_id=7
            )
        await engine.dispose()
        return first, second, records

    first, second, records = asyncio.run(scenario())
    assert first.cycle_id == second.cycle_id
    record_types = [item.record_type for item in records]
    assert record_types.count("evidence") == 2
    assert record_types.count("snapshot") == 1
    assert record_types.count("memory") == 1
    assert record_types.count("hypothesis") == 1
