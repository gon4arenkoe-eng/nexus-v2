"""Unit tests for Decision Memory store semantics without a database driver."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

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
from infra.persistence.repositories.decision_intelligence import DecisionStoredRecord
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 16, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(VenueId("SIM"), "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)


class FakeRepository:
    def __init__(self):
        self.records: dict[tuple[str, int, str, str], DecisionStoredRecord] = {}

    async def append(self, record: DecisionStoredRecord) -> None:
        key = (record.workspace_id, record.user_id, record.record_type, record.record_id)
        existing = self.records.get(key)
        if existing is not None:
            if existing == record:
                return
            raise ValueError("immutable Decision Intelligence record conflict")
        self.records[key] = record

    async def get(self, *, workspace_id, user_id, record_type, record_id):
        return self.records.get((workspace_id, user_id, record_type, record_id))

    async def list_children(self, *, workspace_id, user_id, record_type, parent_record_id):
        values = [
            record
            for record in self.records.values()
            if record.workspace_id == workspace_id
            and record.user_id == user_id
            and record.record_type == record_type
            and record.parent_record_id == parent_record_id
        ]
        return tuple(sorted(values, key=lambda item: (item.created_at, item.record_id)))


def _snapshot():
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
        snapshot_id="snap-1",
        workspace_id="ws-1",
        user_id=7,
        created_at=NOW,
        context=context,
        available_strategy_versions=("trend@1",),
    )


def _decision(snapshot):
    objective = DecisionObjective(
        "obj-1", "1", "MAXIMIZE_RISK_ADJUSTED_EXPECTANCY",
        DecisionPreference.BALANCED, Decimal("0.5"), Decimal("0.7"),
        Decimal("0.05"), Decimal("0.4"),
    )
    assessment = StrategyOpportunityAssessment(
        assessment_id="a-1", snapshot_id=snapshot.snapshot_id,
        strategy_id="trend", strategy_version="1", strategy_family="TREND",
        eligibility=OpportunityEligibility.ELIGIBLE,
        expected_net_edge=Decimal("0.3"), confidence=Decimal("0.8"),
        uncertainty=Decimal("0.1"), regime_suitability=Decimal("0.9"),
        liquidity_suitability=Decimal("0.9"), event_risk_suitability=Decimal("0.9"),
        capacity_score=Decimal("0.8"), drawdown_risk=Decimal("0.2"),
        tail_risk_score=Decimal("0.2"), correlation_penalty=Decimal("0.1"),
        diversification_value=Decimal("0.7"), data_quality_score=Decimal("0.95"),
    )
    return DeterministicStrategyPortfolioManager().decide(
        decision_id="decision-1", snapshot=snapshot, objective=objective,
        assessments=(assessment,), created_at=NOW,
    )


def _outcome():
    return DecisionOutcome(
        "outcome-1", "decision-1", NOW, Decimal("100"), Decimal("0.8"),
        Decimal("2"), Decimal("-1"), Decimal("0.1"),
        reconciliation_evidence_refs=("recon:1",),
    )


def _evaluation():
    return DecisionEvaluation(
        "evaluation-1", "decision-1", "outcome-1", NOW,
        Decimal("0.8"), Decimal("0.9"), Decimal("0.8"), Decimal("0.75"),
        Decimal("0.7"), Decimal("0.9"), Decimal("0.95"),
        DecisionErrorClass.NO_ERROR_DETECTED,
    )


def test_store_rebuilds_full_projection_from_append_only_records() -> None:
    async def scenario():
        repo = FakeRepository()
        store = DecisionMemoryPersistenceStore(repo)  # type: ignore[arg-type]
        snapshot = _snapshot()
        decision = _decision(snapshot)
        await store.append_snapshot(snapshot)
        await store.append_decision(decision)
        await store.append_outcome(workspace_id="ws-1", user_id=7, value=_outcome())
        await store.append_evaluation(workspace_id="ws-1", user_id=7, value=_evaluation())
        return await store.rebuild(workspace_id="ws-1", user_id=7, decision_id="decision-1")

    record = asyncio.run(scenario())
    assert record is not None
    assert record.snapshot.instruments == (INSTRUMENT,)
    assert record.outcome is not None and record.outcome.realized_pnl == Decimal("100")
    assert record.evaluation is not None


def test_store_blocks_cross_owner_parent_substitution() -> None:
    async def scenario():
        repo = FakeRepository()
        store = DecisionMemoryPersistenceStore(repo)  # type: ignore[arg-type]
        snapshot = _snapshot()
        await store.append_snapshot(snapshot)
        decision = _decision(snapshot)
        await store.append_decision(decision)
        try:
            await store.append_outcome(workspace_id="ws-2", user_id=7, value=_outcome())
        except ValueError:
            return True
        return False

    assert asyncio.run(scenario()) is True
