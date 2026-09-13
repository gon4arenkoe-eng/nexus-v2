"""Durable Decision Intelligence memory persistence tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.decision_intelligence.application.decision_engine import (
    DeterministicStrategyPortfolioManager,
    MarketContextDecisionBridge,
)
from apps.decision_intelligence.domain.decision import (
    DecisionErrorClass,
    DecisionEvaluation,
    DecisionObjective,
    DecisionOutcome,
    DecisionPreference,
    OpportunityEligibility,
    StrategyOpportunityAssessment,
)
from apps.intelligence.domain.market_context import (
    DataQualityState,
    EventRiskState,
    FundingState,
    LiquidityState,
    MarketContext,
    MarketRegime,
    TrendState,
    VolatilityState,
)
from infra.persistence.application.decision_intelligence import DecisionMemoryPersistenceStore
from infra.persistence.base import PersistenceBase
from infra.persistence.models.decision_intelligence import DecisionIntelligenceRecordModel
from infra.persistence.repositories.decision_intelligence import DecisionIntelligenceRecordRepository
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 15, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(
    venue_id=VenueId("SIM"),
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _snapshot(*, workspace_id: str = "ws-1", user_id: int = 7, snapshot_id: str = "snap-1"):
    context = MarketContext(
        instrument_id=INSTRUMENT,
        as_of=NOW,
        regime=MarketRegime.TRENDING_UP,
        volatility=VolatilityState.NORMAL,
        trend=TrendState.BULLISH,
        liquidity=LiquidityState.DEEP,
        funding=FundingState.NEUTRAL,
        event_risk=EventRiskState.NONE,
        data_quality=DataQualityState.CURRENT,
        data_quality_score=Decimal("0.95"),
        latest_price=Decimal("60000"),
        spread_ratio=Decimal("0.0001"),
        visible_depth_notional=Decimal("500000"),
        funding_rate=Decimal("0.00001"),
        open_interest=Decimal("1000000"),
        correlations=(),
        sources=("sim",),
        blockers=(),
    )
    return MarketContextDecisionBridge().build_snapshot(
        snapshot_id=snapshot_id,
        workspace_id=workspace_id,
        user_id=user_id,
        created_at=NOW,
        context=context,
        available_strategy_versions=("trend@1",),
    )


def _decision(snapshot, *, decision_id: str = "decision-1"):
    objective = DecisionObjective(
        objective_id="obj-1",
        version="1",
        primary_goal="MAXIMIZE_RISK_ADJUSTED_EXPECTANCY",
        preference=DecisionPreference.BALANCED,
        max_portfolio_risk=Decimal("0.5"),
        min_data_quality=Decimal("0.7"),
        min_expected_net_edge=Decimal("0.05"),
        max_strategy_weight=Decimal("0.4"),
    )
    assessment = StrategyOpportunityAssessment(
        assessment_id="assessment-1",
        snapshot_id=snapshot.snapshot_id,
        strategy_id="trend",
        strategy_version="1",
        strategy_family="TREND",
        eligibility=OpportunityEligibility.ELIGIBLE,
        expected_net_edge=Decimal("0.30"),
        confidence=Decimal("0.80"),
        uncertainty=Decimal("0.10"),
        regime_suitability=Decimal("0.90"),
        liquidity_suitability=Decimal("0.90"),
        event_risk_suitability=Decimal("0.90"),
        capacity_score=Decimal("0.80"),
        drawdown_risk=Decimal("0.20"),
        tail_risk_score=Decimal("0.20"),
        correlation_penalty=Decimal("0.10"),
        diversification_value=Decimal("0.70"),
        data_quality_score=Decimal("0.95"),
        supporting_evidence=("market:snap-1",),
    )
    return DeterministicStrategyPortfolioManager().decide(
        decision_id=decision_id,
        snapshot=snapshot,
        objective=objective,
        assessments=(assessment,),
        created_at=NOW,
    )


def _outcome(decision_id: str = "decision-1", *, outcome_id: str = "outcome-1", pnl: str = "100"):
    return DecisionOutcome(
        outcome_id=outcome_id,
        decision_id=decision_id,
        evaluated_at=NOW,
        realized_pnl=Decimal(pnl),
        realized_r_multiple=Decimal("0.8"),
        fees=Decimal("2"),
        funding=Decimal("-1"),
        slippage=Decimal("0.1"),
        execution_quality_ref="execution-quality:1",
        reconciliation_evidence_refs=("recon:matched",),
    )


def _evaluation(decision_id: str = "decision-1", outcome_id: str = "outcome-1"):
    return DecisionEvaluation(
        evaluation_id="evaluation-1",
        decision_id=decision_id,
        outcome_id=outcome_id,
        evaluated_at=NOW,
        market_model_accuracy=Decimal("0.8"),
        strategy_selection_quality=Decimal("0.9"),
        allocation_quality=Decimal("0.8"),
        confidence_calibration=Decimal("0.75"),
        timing_quality=Decimal("0.7"),
        data_quality_impact=Decimal("0.9"),
        execution_quality=Decimal("0.95"),
        primary_error_class=DecisionErrorClass.NO_ERROR_DETECTED,
        evidence_refs=("eval:1",),
    )


async def _make_store():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(
            PersistenceBase.metadata.create_all,
            tables=(DecisionIntelligenceRecordModel.__table__,),
        )
    return engine, factory


def test_decision_memory_rebuilds_full_lineage_after_fresh_session() -> None:
    async def scenario():
        engine, factory = await _make_store()
        snapshot = _snapshot()
        decision = _decision(snapshot)
        outcome = _outcome()
        evaluation = _evaluation()
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            await store.append_snapshot(snapshot)
            await store.append_decision(decision)
            await store.append_outcome(workspace_id="ws-1", user_id=7, value=outcome)
            await store.append_evaluation(workspace_id="ws-1", user_id=7, value=evaluation)
            await session.commit()
        async with factory() as session:
            record = await DecisionMemoryPersistenceStore(
                DecisionIntelligenceRecordRepository(session)
            ).rebuild(workspace_id="ws-1", user_id=7, decision_id="decision-1")
        await engine.dispose()
        return record

    record = asyncio.run(scenario())
    assert record is not None
    assert record.memory_id == "decision-memory:decision-1"
    assert record.snapshot.snapshot_id == "snap-1"
    assert record.decision.decision_id == "decision-1"
    assert record.outcome is not None and record.outcome.realized_pnl == Decimal("100")
    assert record.evaluation is not None
    assert record.evaluation.primary_error_class is DecisionErrorClass.NO_ERROR_DETECTED


def test_decision_memory_is_workspace_and_user_scoped() -> None:
    async def scenario():
        engine, factory = await _make_store()
        snapshot = _snapshot()
        decision = _decision(snapshot)
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            await store.append_snapshot(snapshot)
            await store.append_decision(decision)
            await session.commit()
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            same = await store.rebuild(workspace_id="ws-1", user_id=7, decision_id="decision-1")
            wrong_workspace = await store.rebuild(workspace_id="ws-2", user_id=7, decision_id="decision-1")
            wrong_user = await store.rebuild(workspace_id="ws-1", user_id=8, decision_id="decision-1")
        await engine.dispose()
        return same, wrong_workspace, wrong_user

    same, wrong_workspace, wrong_user = asyncio.run(scenario())
    assert same is not None
    assert wrong_workspace is None
    assert wrong_user is None


def test_decision_memory_retry_is_idempotent_and_conflict_fails_closed() -> None:
    async def scenario():
        engine, factory = await _make_store()
        snapshot = _snapshot()
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            await store.append_snapshot(snapshot)
            await store.append_snapshot(snapshot)
            await session.flush()
            conflicting = _snapshot(snapshot_id="snap-1")
            object.__setattr__(conflicting, "market_context_hash", "different-hash")
            conflict = False
            try:
                await store.append_snapshot(conflicting)
            except ValueError:
                conflict = True
            records = await DecisionIntelligenceRecordRepository(session).list_for_owner(
                workspace_id="ws-1", user_id=7
            )
        await engine.dispose()
        return conflict, records

    conflict, records = asyncio.run(scenario())
    assert conflict is True
    assert len(records) == 1


def test_outcome_and_evaluation_require_same_owner_parent_chain() -> None:
    async def scenario():
        engine, factory = await _make_store()
        snapshot = _snapshot()
        decision = _decision(snapshot)
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            await store.append_snapshot(snapshot)
            await store.append_decision(decision)
            outcome_blocked = evaluation_blocked = False
            try:
                await store.append_outcome(workspace_id="ws-2", user_id=7, value=_outcome())
            except ValueError:
                outcome_blocked = True
            try:
                await store.append_evaluation(
                    workspace_id="ws-1", user_id=7, value=_evaluation()
                )
            except ValueError:
                evaluation_blocked = True
        await engine.dispose()
        return outcome_blocked, evaluation_blocked

    assert asyncio.run(scenario()) == (True, True)


def test_decision_memory_allows_only_one_immutable_outcome_and_evaluation() -> None:
    async def scenario():
        engine, factory = await _make_store()
        snapshot = _snapshot()
        decision = _decision(snapshot)
        async with factory() as session:
            store = DecisionMemoryPersistenceStore(DecisionIntelligenceRecordRepository(session))
            await store.append_snapshot(snapshot)
            await store.append_decision(decision)
            await store.append_outcome(workspace_id="ws-1", user_id=7, value=_outcome())
            second_outcome_blocked = False
            try:
                await store.append_outcome(
                    workspace_id="ws-1",
                    user_id=7,
                    value=_outcome(outcome_id="outcome-2", pnl="90"),
                )
            except ValueError:
                second_outcome_blocked = True
            await store.append_evaluation(
                workspace_id="ws-1", user_id=7, value=_evaluation()
            )
            different_eval = _evaluation()
            object.__setattr__(different_eval, "evaluation_id", "evaluation-2")
            second_evaluation_blocked = False
            try:
                await store.append_evaluation(
                    workspace_id="ws-1", user_id=7, value=different_eval
                )
            except ValueError:
                second_evaluation_blocked = True
        await engine.dispose()
        return second_outcome_blocked, second_evaluation_blocked

    assert asyncio.run(scenario()) == (True, True)


def test_decision_memory_model_registered_and_guarded() -> None:
    assert "decision_intelligence_records" in PersistenceBase.metadata.tables
    checks = {
        str(constraint.sqltext)
        for constraint in DecisionIntelligenceRecordModel.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "user_id > 0" in checks
