"""Unit tests for Ledger -> DecisionOutcome attribution semantics."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.decision_intelligence.application.outcome_attribution import (
    DecisionOutcomeAttributionError,
    LedgerDecisionOutcomeAttributionService,
)
from apps.decision_intelligence.domain.attribution import (
    DecisionExecutionLink,
    ExecutionPlanLineage,
    LedgerAttributionEvent,
)
from apps.decision_intelligence.domain.decision import (
    DecisionMemoryRecord,
    DecisionState,
    MarketDecisionSnapshot,
    StrategyAllocationRecommendation,
    StrategyPortfolioDecision,
)
from infra.persistence.application.decision_outcome_attribution import (
    LedgerPersistenceAttributionReader,
)
from infra.persistence.models.ledger import ExecutionLedgerEventModel
from packages.contracts.identities import AssetClass, InstrumentId, InstrumentType, VenueId

NOW = datetime(2026, 9, 13, 17, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(VenueId("SIM"), "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)


def _snapshot() -> MarketDecisionSnapshot:
    return MarketDecisionSnapshot(
        snapshot_id="snap-1", workspace_id="ws-1", user_id=7, created_at=NOW,
        market_context_hash="hash-1", market_context_as_of=NOW,
        instruments=(INSTRUMENT,), data_quality_state="CURRENT",
        data_quality_score=Decimal("0.95"), market_uncertainty=Decimal("0.1"),
    )


def _decision() -> StrategyPortfolioDecision:
    return StrategyPortfolioDecision(
        decision_id="decision-1", snapshot_id="snap-1", workspace_id="ws-1",
        user_id=7, created_at=NOW, state=DecisionState.REBALANCE,
        objective_id="obj-1", objective_version="1",
        portfolio_confidence=Decimal("0.8"), portfolio_uncertainty=Decimal("0.2"),
        allocations=(
            StrategyAllocationRecommendation(
                strategy_id="trend", strategy_version="1",
                target_weight=Decimal("0.4"), max_weight=Decimal("0.5"),
                confidence=Decimal("0.8"), expected_contribution=Decimal("0.3"),
                expected_risk_contribution=Decimal("0.2"), reason_codes=("EDGE",),
            ),
            StrategyAllocationRecommendation(
                strategy_id="breakout", strategy_version="2",
                target_weight=Decimal("0.3"), max_weight=Decimal("0.5"),
                confidence=Decimal("0.75"), expected_contribution=Decimal("0.25"),
                expected_risk_contribution=Decimal("0.2"), reason_codes=("EDGE",),
            ),
        ),
        reason_codes=("PORTFOLIO_EDGE",), decision_policy_version="decision-v1",
    )


class FakeMemory:
    def __init__(self) -> None:
        self.record = DecisionMemoryRecord("decision-memory:decision-1", _snapshot(), _decision())
        self.appended = []

    async def rebuild(self, *, workspace_id, user_id, decision_id):
        if (workspace_id, user_id, decision_id) != ("ws-1", 7, "decision-1"):
            return None
        return self.record

    async def append_outcome(self, *, workspace_id, user_id, value):
        self.appended.append((workspace_id, user_id, value))
        self.record = DecisionMemoryRecord(self.record.memory_id, self.record.snapshot, self.record.decision, value)


class FakeLinks:
    def __init__(self, links): self.links = tuple(links)
    async def list_for_decision(self, **_): return self.links


class FakePlans:
    def __init__(self, plans): self.plans = tuple(plans)
    async def list_for_intents(self, *, user_id, intent_ids):
        return tuple(p for p in self.plans if p.user_id == user_id and p.intent_id in intent_ids)


class FakeLedger:
    def __init__(self, values): self.values = values
    async def list_for_plan(self, *, user_id, plan_id):
        return tuple(e for e in self.values.get(plan_id, ()) if e.user_id == user_id)


def _link(link_id, intent_id, strategy, version):
    return DecisionExecutionLink(link_id, "ws-1", 7, "decision-1", intent_id, strategy, version, NOW)


def _plan(plan_id, intent_id, strategy, version):
    return ExecutionPlanLineage(plan_id, intent_id, 7, strategy, version)


def _event(event_id, plan_id, *, pnl, r, fees, funding, slippage, second):
    return LedgerAttributionEvent(
        event_id, plan_id, 7, NOW + timedelta(seconds=second),
        Decimal(pnl), Decimal(r), Decimal(fees), Decimal(funding), Decimal(slippage),
    )


def test_multi_intent_attribution_aggregates_ledger_only_and_persists_outcome() -> None:
    async def scenario():
        memory = FakeMemory()
        service = LedgerDecisionOutcomeAttributionService(
            links=FakeLinks((_link("l1", "i1", "trend", "1"), _link("l2", "i2", "breakout", "2"))),
            plans=FakePlans((_plan("p1", "i1", "trend", "1"), _plan("p2", "i2", "breakout", "2"))),
            ledger=FakeLedger({
                "p1": (_event("e1", "p1", pnl="10", r="0.4", fees="1", funding="-0.2", slippage="0.1", second=1),),
                "p2": (_event("e2", "p2", pnl="20", r="0.6", fees="2", funding="0.3", slippage="0.2", second=2),),
            }),
            memory=memory,
        )
        outcome = await service.attribute(workspace_id="ws-1", user_id=7, decision_id="decision-1", outcome_id="outcome-1")
        return memory, outcome

    memory, outcome = asyncio.run(scenario())
    assert outcome.realized_pnl == Decimal("30")
    assert outcome.realized_r_multiple == Decimal("1.0")
    assert outcome.fees == Decimal("3")
    assert outcome.funding == Decimal("0.1")
    assert outcome.slippage == Decimal("0.3")
    assert outcome.evaluated_at == NOW + timedelta(seconds=2)
    assert outcome.execution_quality_ref.startswith("ledger-attribution:")
    assert len(memory.appended) == 1


def test_missing_plan_fails_closed() -> None:
    service = LedgerDecisionOutcomeAttributionService(
        links=FakeLinks((_link("l1", "i1", "trend", "1"), _link("l2", "i2", "breakout", "2"))),
        plans=FakePlans((_plan("p1", "i1", "trend", "1"),)),
        ledger=FakeLedger({}), memory=FakeMemory(),
    )
    with pytest.raises(DecisionOutcomeAttributionError, match="no canonical execution plan"):
        asyncio.run(service.attribute(workspace_id="ws-1", user_id=7, decision_id="decision-1", outcome_id="o1"))


def test_duplicate_ledger_event_id_across_plans_fails_closed() -> None:
    duplicate1 = _event("same", "p1", pnl="1", r="0.1", fees="0", funding="0", slippage="0", second=1)
    duplicate2 = _event("same", "p2", pnl="2", r="0.2", fees="0", funding="0", slippage="0", second=2)
    service = LedgerDecisionOutcomeAttributionService(
        links=FakeLinks((_link("l1", "i1", "trend", "1"), _link("l2", "i2", "breakout", "2"))),
        plans=FakePlans((_plan("p1", "i1", "trend", "1"), _plan("p2", "i2", "breakout", "2"))),
        ledger=FakeLedger({"p1": (duplicate1,), "p2": (duplicate2,)}), memory=FakeMemory(),
    )
    with pytest.raises(DecisionOutcomeAttributionError, match="duplicate Ledger"):
        asyncio.run(service.attribute(workspace_id="ws-1", user_id=7, decision_id="decision-1", outcome_id="o1"))


def test_strategy_lineage_mismatch_fails_closed() -> None:
    service = LedgerDecisionOutcomeAttributionService(
        links=FakeLinks((_link("l1", "i1", "trend", "1"),)),
        plans=FakePlans((_plan("p1", "i1", "other", "1"),)),
        ledger=FakeLedger({}), memory=FakeMemory(),
    )
    with pytest.raises(DecisionOutcomeAttributionError, match="strategy lineage mismatch"):
        asyncio.run(service.attribute(workspace_id="ws-1", user_id=7, decision_id="decision-1", outcome_id="o1"))


class FakeLedgerRepository:
    def __init__(self, events): self.events = tuple(events)
    async def list_for_plan(self, *, user_id, plan_id):
        return tuple(e for e in self.events if e.user_id == user_id and e.plan_id == plan_id)


def _ledger_model(event_id, event_type, payload):
    return ExecutionLedgerEventModel(
        event_id=event_id, event_type=event_type, event_version=1, user_id=7,
        plan_id="p1", group_id=None, leg_id=None, order_id=None, fill_id=None,
        venue_id="SIM", account_value=1, instrument_venue_id="SIM",
        native_symbol="BTCUSDT", instrument_type="PERPETUAL", asset_class="CRYPTO",
        source="test", correlation_id=None, causation_id=None, occurred_at=NOW,
        recorded_at=NOW, sequence_no=1, evidence_source="CORE", evidence_quality="CANONICAL",
        schema_version=1, payload=payload,
    )


def test_ledger_reader_uses_only_explicit_fill_attribution_payload() -> None:
    async def scenario():
        reader = LedgerPersistenceAttributionReader(FakeLedgerRepository((
            _ledger_model("ignore", "ORDER_FILLED", {"realized_pnl": "999"}),
            _ledger_model("fill", "FILL_RECORDED", {"decision_attribution": {
                "schema_version": 1, "realized_pnl": "12.5", "realized_r_multiple": "0.4",
                "fees": "0.2", "funding": "-0.1", "slippage": "0.05",
            }}),
        )))
        return await reader.list_for_plan(user_id=7, plan_id="p1")

    events = asyncio.run(scenario())
    assert len(events) == 1
    assert events[0].event_id == "fill"
    assert events[0].realized_pnl == Decimal("12.5")


def test_ledger_reader_rejects_incomplete_attribution_payload() -> None:
    async def scenario():
        reader = LedgerPersistenceAttributionReader(FakeLedgerRepository((
            _ledger_model("fill", "FILL_RECORDED", {"decision_attribution": {"schema_version": 1, "realized_pnl": "1"}}),
        )))
        return await reader.list_for_plan(user_id=7, plan_id="p1")

    with pytest.raises(ValueError, match="missing realized_r_multiple"):
        asyncio.run(scenario())
