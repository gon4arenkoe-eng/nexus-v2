"""SQL persistence integration for decision -> execution -> Ledger attribution."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.decision_intelligence.application.outcome_attribution import LedgerDecisionOutcomeAttributionService
from apps.decision_intelligence.domain.attribution import DecisionExecutionLink
from apps.decision_intelligence.domain.decision import (
    DecisionState,
    MarketDecisionSnapshot,
    StrategyAllocationRecommendation,
    StrategyPortfolioDecision,
)
from infra.persistence.application.decision_intelligence import DecisionMemoryPersistenceStore
from infra.persistence.application.decision_outcome_attribution import (
    DecisionExecutionLinkPersistenceStore,
    ExecutionPlanPersistenceLineageReader,
    LedgerPersistenceAttributionReader,
)
from infra.persistence.base import PersistenceBase
from infra.persistence.models.decision_intelligence import DecisionIntelligenceRecordModel
from infra.persistence.models.execution import ExecutionPlanModel
from infra.persistence.models.ledger import ExecutionLedgerEventModel
from infra.persistence.repositories.decision_intelligence import DecisionIntelligenceRecordRepository
from infra.persistence.repositories.ledger import ExecutionLedgerRepository
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(VenueId("SIM"), "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)


def _snapshot():
    return MarketDecisionSnapshot(
        "snap-1", "ws-1", 7, NOW, "ctx-hash", NOW, (INSTRUMENT,),
        "CURRENT", Decimal("0.95"), Decimal("0.1"),
    )


def _decision():
    return StrategyPortfolioDecision(
        "decision-1", "snap-1", "ws-1", 7, NOW, DecisionState.ACTIVATE,
        "obj-1", "1", Decimal("0.8"), Decimal("0.2"),
        (StrategyAllocationRecommendation(
            "trend", "1", Decimal("0.4"), Decimal("0.5"), Decimal("0.8"),
            Decimal("0.3"), Decimal("0.2"), reason_codes=("EDGE",),
        ),),
        ("EDGE",), "decision-v1",
    )


def _plan():
    return ExecutionPlanModel(
        id=1,
        plan_id="plan-1", intent_id="intent-1", user_id=7, shape="SINGLE",
        strategy="trend", strategy_version="1", source="decision-intelligence",
        created_at=NOW, recorded_at=NOW, schema_version=1, metadata_payload={},
    )


def _ledger_event():
    return ExecutionLedgerEventModel(
        id=1,
        event_id="fill-evidence-1", event_type="FILL_RECORDED", event_version=1,
        user_id=7, plan_id="plan-1", group_id=None, leg_id=None, order_id=None,
        fill_id=None, venue_id="SIM", account_value=1, instrument_venue_id="SIM",
        native_symbol="BTCUSDT", instrument_type="PERPETUAL", asset_class="CRYPTO",
        source="core", correlation_id=None, causation_id=None, occurred_at=NOW,
        recorded_at=NOW, sequence_no=1, evidence_source="CORE", evidence_quality="CANONICAL",
        schema_version=1,
        payload={"decision_attribution": {
            "schema_version": 1,
            "realized_pnl": "25",
            "realized_r_multiple": "0.5",
            "fees": "1",
            "funding": "-0.2",
            "slippage": "0.1",
        }},
    )


async def _engine_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(
            PersistenceBase.metadata.create_all,
            tables=(
                DecisionIntelligenceRecordModel.__table__,
                ExecutionPlanModel.__table__,
                ExecutionLedgerEventModel.__table__,
            ),
        )
    return engine, factory


def test_attribution_recovers_lineage_and_appends_outcome_across_fresh_session() -> None:
    async def scenario():
        engine, factory = await _engine_factory()
        async with factory() as session:
            decision_repo = DecisionIntelligenceRecordRepository(session)
            memory = DecisionMemoryPersistenceStore(decision_repo)
            await memory.append_snapshot(_snapshot())
            await memory.append_decision(_decision())
            links = DecisionExecutionLinkPersistenceStore(decision_repo)
            link = DecisionExecutionLink(
                "link-1", "ws-1", 7, "decision-1", "intent-1", "trend", "1", NOW
            )
            await links.append(link)
            await links.append(link)
            session.add(_plan())
            session.add(_ledger_event())
            await session.commit()

        async with factory() as session:
            decision_repo = DecisionIntelligenceRecordRepository(session)
            memory = DecisionMemoryPersistenceStore(decision_repo)
            service = LedgerDecisionOutcomeAttributionService(
                links=DecisionExecutionLinkPersistenceStore(decision_repo),
                plans=ExecutionPlanPersistenceLineageReader(session),
                ledger=LedgerPersistenceAttributionReader(ExecutionLedgerRepository(session)),
                memory=memory,
            )
            outcome = await service.attribute(
                workspace_id="ws-1", user_id=7, decision_id="decision-1", outcome_id="outcome-1"
            )
            rebuilt = await memory.rebuild(
                workspace_id="ws-1", user_id=7, decision_id="decision-1"
            )
            await session.commit()
        await engine.dispose()
        return outcome, rebuilt

    outcome, rebuilt = asyncio.run(scenario())
    assert outcome.realized_pnl == Decimal("25")
    assert outcome.fees == Decimal("1")
    assert outcome.funding == Decimal("-0.2")
    assert outcome.slippage == Decimal("0.1")
    assert rebuilt is not None and rebuilt.outcome == outcome


def test_execution_link_is_tenant_scoped_and_conflicting_intent_link_fails_closed() -> None:
    async def scenario():
        engine, factory = await _engine_factory()
        async with factory() as session:
            repo = DecisionIntelligenceRecordRepository(session)
            memory = DecisionMemoryPersistenceStore(repo)
            await memory.append_snapshot(_snapshot())
            await memory.append_decision(_decision())
            links = DecisionExecutionLinkPersistenceStore(repo)
            await links.append(DecisionExecutionLink(
                "link-1", "ws-1", 7, "decision-1", "intent-1", "trend", "1", NOW
            ))
            conflict = False
            try:
                await links.append(DecisionExecutionLink(
                    "link-2", "ws-1", 7, "decision-1", "intent-1", "trend", "1", NOW
                ))
            except ValueError:
                conflict = True
            same = await links.list_for_decision(workspace_id="ws-1", user_id=7, decision_id="decision-1")
            wrong = await links.list_for_decision(workspace_id="ws-2", user_id=7, decision_id="decision-1")
        await engine.dispose()
        return conflict, same, wrong

    conflict, same, wrong = asyncio.run(scenario())
    assert conflict is True
    assert len(same) == 1
    assert wrong == ()
