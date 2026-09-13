from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import inspect

import pytest

from adapters.reasoning.openai_compatible import (
    OpenAICompatibleReasoningAdapter,
    groq_config,
    ollama_config,
)
from apps.decision_intelligence.application.decision_engine import (
    DeterministicStrategyPortfolioManager,
    MarketContextDecisionBridge,
)
from apps.decision_intelligence.domain.decision import (
    DecisionErrorClass,
    DecisionEvaluation,
    DecisionMemoryRecord,
    DecisionObjective,
    DecisionOutcome,
    DecisionPreference,
    DecisionState,
    OpportunityEligibility,
    ReasoningRequest,
    ReasoningStatus,
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
from packages.contracts.identities import (
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


NOW = datetime(2026, 9, 13, 10, 0, tzinfo=UTC)
INSTRUMENT = InstrumentId(
    venue_id=VenueId("SIM"),
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _market_context(*, quality=Decimal("0.95"), blockers=()):
    return MarketContext(
        instrument_id=INSTRUMENT,
        as_of=NOW,
        regime=MarketRegime.TRENDING_UP,
        volatility=VolatilityState.NORMAL,
        trend=TrendState.BULLISH,
        liquidity=LiquidityState.DEEP,
        funding=FundingState.NEUTRAL,
        event_risk=EventRiskState.NONE,
        data_quality=DataQualityState.CURRENT,
        data_quality_score=quality,
        latest_price=Decimal("60000"),
        spread_ratio=Decimal("0.0001"),
        visible_depth_notional=Decimal("500000"),
        funding_rate=Decimal("0.00001"),
        open_interest=Decimal("1000000"),
        correlations=(),
        sources=("sim",),
        blockers=blockers,
    )


def _snapshot(*, quality=Decimal("0.95"), blockers=()):
    return MarketContextDecisionBridge().build_snapshot(
        snapshot_id="snap-1",
        workspace_id="ws-1",
        user_id=7,
        created_at=NOW,
        context=_market_context(quality=quality, blockers=blockers),
        available_strategy_versions=("trend@1", "breakout@1"),
    )


def _objective():
    return DecisionObjective(
        objective_id="obj-1",
        version="1",
        primary_goal="MAXIMIZE_RISK_ADJUSTED_EXPECTANCY",
        preference=DecisionPreference.BALANCED,
        max_portfolio_risk=Decimal("0.60"),
        min_data_quality=Decimal("0.70"),
        min_expected_net_edge=Decimal("0.05"),
        max_strategy_weight=Decimal("0.40"),
    )


def _assessment(strategy_id: str, *, edge: str, confidence: str):
    return StrategyOpportunityAssessment(
        assessment_id=f"a-{strategy_id}",
        snapshot_id="snap-1",
        strategy_id=strategy_id,
        strategy_version="1",
        strategy_family="TEST",
        eligibility=OpportunityEligibility.ELIGIBLE,
        expected_net_edge=Decimal(edge),
        confidence=Decimal(confidence),
        uncertainty=Decimal("0.15"),
        regime_suitability=Decimal("0.85"),
        liquidity_suitability=Decimal("0.90"),
        event_risk_suitability=Decimal("0.90"),
        capacity_score=Decimal("0.80"),
        drawdown_risk=Decimal("0.20"),
        tail_risk_score=Decimal("0.20"),
        correlation_penalty=Decimal("0.10"),
        diversification_value=Decimal("0.70"),
        data_quality_score=Decimal("0.95"),
        supporting_evidence=(f"evidence:{strategy_id}",),
    )


def test_market_context_bridge_creates_replayable_snapshot() -> None:
    snapshot = _snapshot()
    assert snapshot.data_quality_score == Decimal("0.95")
    assert snapshot.market_uncertainty == Decimal("0.05")
    assert snapshot.instruments == (INSTRUMENT,)
    assert snapshot.market_context_hash
    assert snapshot.evidence_refs[0].startswith("market-context:")


def test_market_blockers_force_evidence_bearing_no_trade() -> None:
    snapshot = _snapshot(blockers=("stale-price",))
    decision = DeterministicStrategyPortfolioManager().decide(
        decision_id="d-1",
        snapshot=snapshot,
        objective=_objective(),
        assessments=(_assessment("trend", edge="0.3", confidence="0.8"),),
        created_at=NOW,
    )
    assert decision.state is DecisionState.NO_TRADE
    assert decision.allocations == ()
    assert "MARKET_CONTEXT_BLOCKED" in decision.reason_codes
    assert "stale-price" in decision.reason_codes


def test_manager_builds_multi_strategy_weights_without_execution_authority() -> None:
    decision = DeterministicStrategyPortfolioManager().decide(
        decision_id="d-2",
        snapshot=_snapshot(),
        objective=_objective(),
        assessments=(
            _assessment("trend", edge="0.30", confidence="0.80"),
            _assessment("breakout", edge="0.40", confidence="0.75"),
        ),
        created_at=NOW,
    )
    assert decision.state is DecisionState.REBALANCE
    assert {item.strategy_id for item in decision.allocations} == {"trend", "breakout"}
    assert sum(item.target_weight for item in decision.allocations) <= Decimal("0.60")
    assert all(item.target_weight <= Decimal("0.40") for item in decision.allocations)
    source = inspect.getsource(DeterministicStrategyPortfolioManager)
    for forbidden in ("VenueAdapter", "submit_order", "ExecutionCoordinator", "place_order"):
        assert forbidden not in source


def test_manager_uses_no_trade_when_edge_is_below_objective() -> None:
    decision = DeterministicStrategyPortfolioManager().decide(
        decision_id="d-3",
        snapshot=_snapshot(),
        objective=_objective(),
        assessments=(_assessment("trend", edge="0.01", confidence="0.9"),),
        created_at=NOW,
    )
    assert decision.state is DecisionState.NO_TRADE
    assert decision.reason_codes == ("NO_ELIGIBLE_POSITIVE_EDGE",)


def test_decision_memory_enforces_lineage() -> None:
    snapshot = _snapshot()
    decision = DeterministicStrategyPortfolioManager().decide(
        decision_id="d-4",
        snapshot=snapshot,
        objective=_objective(),
        assessments=(_assessment("trend", edge="0.2", confidence="0.8"),),
        created_at=NOW,
    )
    outcome = DecisionOutcome(
        outcome_id="o-1",
        decision_id=decision.decision_id,
        evaluated_at=NOW,
        realized_pnl=Decimal("100"),
        realized_r_multiple=Decimal("0.8"),
        fees=Decimal("2"),
        funding=Decimal("-1"),
        slippage=Decimal("0.1"),
        reconciliation_evidence_refs=("recon:matched",),
    )
    evaluation = DecisionEvaluation(
        evaluation_id="e-1",
        decision_id=decision.decision_id,
        outcome_id=outcome.outcome_id,
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
    record = DecisionMemoryRecord(
        memory_id="m-1",
        snapshot=snapshot,
        decision=decision,
        outcome=outcome,
        evaluation=evaluation,
    )
    assert record.evaluation is evaluation

    with pytest.raises(ValueError, match="outcome/decision lineage mismatch"):
        DecisionMemoryRecord(
            memory_id="m-bad",
            snapshot=snapshot,
            decision=decision,
            outcome=DecisionOutcome(
                outcome_id="o-bad",
                decision_id="different",
                evaluated_at=NOW,
                realized_pnl=Decimal("0"),
                realized_r_multiple=Decimal("0"),
                fees=Decimal("0"),
                funding=Decimal("0"),
                slippage=Decimal("0"),
            ),
        )


class FakeTransport:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = []

    async def post_json(self, *, url, headers, payload, timeout_seconds):
        self.calls.append((url, headers, payload, timeout_seconds))
        if self.fail:
            raise TimeoutError("offline")
        return {
            "choices": [
                {"message": {"content": '{"hypothesis":"test","confidence":0.6}'}}
            ]
        }


def _reasoning_request():
    return ReasoningRequest(
        request_id="r-1",
        task="critique decision outcome",
        structured_context={"decision_id": "d-4", "pnl_r": "-0.8"},
        evidence_refs=("decision:d-4",),
        prompt_template_version="reasoning-v1",
        system_policy_version="safety-v1",
    )


@pytest.mark.asyncio
async def test_groq_compatible_reasoning_returns_structured_artifact() -> None:
    transport = FakeTransport()
    adapter = OpenAICompatibleReasoningAdapter(
        config=groq_config(model_id="test-model", api_key="secret"),
        transport=transport,
    )
    result = await adapter.reason(_reasoning_request())
    assert result.status is ReasoningStatus.AVAILABLE
    assert result.provider == "groq"
    assert result.output["hypothesis"] == "test"
    url, headers, payload, _ = transport.calls[0]
    assert url.endswith("/chat/completions")
    assert headers["Authorization"] == "Bearer secret"
    assert payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_llm_outage_is_degraded_not_trading_failure() -> None:
    adapter = OpenAICompatibleReasoningAdapter(
        config=groq_config(model_id="test-model"),
        transport=FakeTransport(fail=True),
    )
    result = await adapter.reason(_reasoning_request())
    assert result.status is ReasoningStatus.DEGRADED
    assert result.error_code == "TIMEOUTERROR"
    assert result.output["reasoning_available"] is False


def test_ollama_config_is_local_and_keyless() -> None:
    config = ollama_config(model_id="qwen3:8b")
    assert config.provider == "ollama"
    assert config.api_key is None
    assert config.base_url == "http://127.0.0.1:11434/v1"


def test_decision_domain_has_no_core_execution_or_provider_dependencies() -> None:
    import apps.decision_intelligence.domain.decision as module

    source = inspect.getsource(module)
    for forbidden in (
        "apps.core",
        "VenueAdapter",
        "ExecutionCoordinator",
        "Groq",
        "Ollama",
        "sqlalchemy",
        "fastapi",
    ):
        assert forbidden not in source
