from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.core.application.strategy_portfolio import (
    CANONICAL_FAMILY_SHORTLIST,
    LEGACY_STRATEGY_INVENTORY,
    RESEARCH_STRATEGY_CATALOG,
    STRATEGY_FAMILY_BENCHMARKS,
    StrategyAttributionAnalytics,
    StrategyRuntime,
    StrategyRuntimeError,
    StrategySemanticParity,
)
from apps.core.domain.intents import (
    TradeIntent,
    TradeIntentKind,
    TradeIntentShape,
    TradeLegIntent,
    TradeSide,
)
from apps.core.domain.strategy_portfolio import (
    LegacyStrategyDisposition,
    StrategyActivationState,
    StrategyAttributionEvent,
    StrategyCatalog,
    StrategyEvaluationContext,
    StrategyFamily,
    StrategyManifest,
    StrategyResearchScorecard,
    StrategyReturnObservation,
    StrategyRuntimeMode,
    StrategyScorecardDecision,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
VENUE = VenueId("SIM")
ACCOUNT = AccountId(venue_id=VENUE, value=1)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


class IdentityAllocation:
    def allocate(self, intent, context):
        return intent


class HalfAllocation:
    def allocate(self, intent, context):
        legs = tuple(
            replace(
                leg,
                quantity=(
                    leg.quantity / Decimal("2")
                    if leg.quantity is not None
                    else None
                ),
            )
            for leg in intent.legs
        )
        return replace(intent, legs=legs)


class DeterministicPlugin:
    strategy_id = "trend-alpha"
    version = "1.0.0"

    def evaluate(self, context):
        return TradeIntent(
            intent_id="intent-001",
            user_id=context.user_id,
            strategy=self.strategy_id,
            strategy_version=self.version,
            source="strategy-runtime",
            kind=TradeIntentKind.OPEN,
            shape=TradeIntentShape.SINGLE_LEG,
            legs=(
                TradeLegIntent(
                    leg_id="leg-1",
                    instrument_id=INSTRUMENT,
                    account_id=ACCOUNT,
                    side=TradeSide.BUY,
                    quantity=Decimal("2"),
                ),
            ),
            created_at=context.observed_at,
            metadata={"edge": "trend"},
        )


def _manifest(
    *,
    activation_state=StrategyActivationState.RESEARCH_ONLY,
):
    return StrategyManifest(
        strategy_id="trend-alpha",
        version="1.0.0",
        family=StrategyFamily.TREND_MOMENTUM,
        hypothesis="Directional persistence after costs.",
        parameter_schema_version="1",
        data_requirements=("bars",),
        risk_requirements=("portfolio-risk-v2",),
        artifact_hash="sha256:test",
        validation_evidence=("shadow-evidence",)
        if activation_state is StrategyActivationState.SHADOW_ONLY
        else (),
        activation_state=activation_state,
    )


def _context():
    return StrategyEvaluationContext(
        user_id=7,
        observed_at=NOW,
        features={"close": Decimal("100")},
    )


def test_legacy_inventory_is_complete_and_unique() -> None:
    assert len(LEGACY_STRATEGY_INVENTORY) == 17
    names = tuple(item.legacy_name for item in LEGACY_STRATEGY_INVENTORY)
    assert len(set(names)) == 17
    assert "grid_combo" in names


def test_grid_is_transferred_out_of_normal_strategy_portfolio() -> None:
    grid = next(
        item
        for item in LEGACY_STRATEGY_INVENTORY
        if item.legacy_name == "grid_combo"
    )
    assert grid.family is None
    assert grid.disposition is LegacyStrategyDisposition.REBUILD
    assert "Phase 7G" in grid.target


def test_canonical_shortlist_has_seven_distinct_economic_families() -> None:
    assert len(CANONICAL_FAMILY_SHORTLIST) == 7
    assert set(CANONICAL_FAMILY_SHORTLIST) == set(StrategyFamily)


def test_every_family_has_reference_benchmark() -> None:
    assert {item.family for item in STRATEGY_FAMILY_BENCHMARKS} == set(
        StrategyFamily
    )
    assert all(item.references for item in STRATEGY_FAMILY_BENCHMARKS)
    assert all(
        item.production_status is StrategyActivationState.RESEARCH_ONLY
        for item in STRATEGY_FAMILY_BENCHMARKS
    )


def test_research_catalog_is_versioned_and_not_live_approved() -> None:
    assert RESEARCH_STRATEGY_CATALOG.catalog_version == "phase7-research-v1"
    assert len(RESEARCH_STRATEGY_CATALOG.entries) == 7
    assert all(
        entry.activation_state is StrategyActivationState.RESEARCH_ONLY
        for entry in RESEARCH_STRATEGY_CATALOG.entries
    )


def test_catalog_rejects_duplicate_strategy_versions() -> None:
    entry = _manifest()
    with pytest.raises(ValueError, match="duplicate strategy/version"):
        StrategyCatalog(
            catalog_version="1",
            entries=(entry, entry),
        )


def test_shadow_manifest_requires_validation_evidence() -> None:
    with pytest.raises(ValueError, match="validation evidence"):
        StrategyManifest(
            strategy_id="x",
            version="1",
            family=StrategyFamily.TREND_MOMENTUM,
            hypothesis="x",
            parameter_schema_version="1",
            data_requirements=(),
            risk_requirements=(),
            artifact_hash="hash",
            validation_evidence=(),
            activation_state=StrategyActivationState.SHADOW_ONLY,
        )


def test_scorecard_is_multi_objective_and_falsification_first() -> None:
    strong = StrategyResearchScorecard(
        oos_expectancy=Decimal("0.8"),
        profit_factor_score=Decimal("0.8"),
        drawdown_resilience=Decimal("0.8"),
        walk_forward_stability=Decimal("0.8"),
        parameter_stability=Decimal("0.8"),
        cross_symbol_stability=Decimal("0.8"),
        regime_stability=Decimal("0.8"),
        capacity_score=Decimal("0.8"),
        cost_robustness=Decimal("0.8"),
        tail_risk_resilience=Decimal("0.8"),
        incremental_diversification=Decimal("0.8"),
        falsification_passed=True,
    )
    assert strong.decision is StrategyScorecardDecision.FAMILY_CANDIDATE
    rejected = replace(strong, falsification_passed=False)
    assert rejected.decision is StrategyScorecardDecision.REJECT


def test_runtime_produces_intent_without_execution_authority() -> None:
    catalog = StrategyCatalog("1", (_manifest(),))
    runtime = StrategyRuntime(catalog=catalog, allocation=IdentityAllocation())
    result = runtime.evaluate(
        plugin=DeterministicPlugin(),
        context=_context(),
        mode=StrategyRuntimeMode.SHADOW,
    )
    assert result.intent is not None
    assert result.intent.strategy == "trend-alpha"
    source = __import__(
        "inspect"
    ).getsource(StrategyRuntime)
    assert "VenueAdapter" not in source
    assert "submit_order" not in source
    assert "ExecutionCoordinator" not in source


def test_runtime_rejects_wrong_strategy_lineage() -> None:
    class WrongPlugin(DeterministicPlugin):
        def evaluate(self, context):
            return replace(
                super().evaluate(context),
                strategy="wrong",
            )

    runtime = StrategyRuntime(
        catalog=StrategyCatalog("1", (_manifest(),)),
        allocation=IdentityAllocation(),
    )
    with pytest.raises(StrategyRuntimeError, match="ID mismatch"):
        runtime.evaluate(
            plugin=WrongPlugin(),
            context=_context(),
            mode=StrategyRuntimeMode.BACKTEST,
        )


def test_allocation_runs_between_strategy_and_risk_boundary() -> None:
    runtime = StrategyRuntime(
        catalog=StrategyCatalog("1", (_manifest(),)),
        allocation=HalfAllocation(),
    )
    result = runtime.evaluate(
        plugin=DeterministicPlugin(),
        context=_context(),
        mode=StrategyRuntimeMode.PAPER,
    )
    assert result.intent is not None
    assert result.intent.legs[0].quantity == Decimal("1")


def test_backtest_and_live_semantics_are_identical() -> None:
    runtime = StrategyRuntime(
        catalog=StrategyCatalog("1", (_manifest(),)),
        allocation=IdentityAllocation(),
    )
    parity = StrategySemanticParity(runtime)
    left, right = parity.assert_equivalent(
        plugin=DeterministicPlugin(),
        context=_context(),
        left_mode=StrategyRuntimeMode.BACKTEST,
        right_mode=StrategyRuntimeMode.LIVE_SEMANTICS,
    )
    assert left.intent == right.intent


def test_pnl_attribution_is_per_strategy_and_no_double_count() -> None:
    events = (
        StrategyAttributionEvent(
            "e1",
            "a",
            "1",
            NOW,
            Decimal("10"),
            fees=Decimal("1"),
        ),
        StrategyAttributionEvent(
            "e2",
            "a",
            "1",
            NOW + timedelta(minutes=1),
            Decimal("5"),
            funding=Decimal("0.5"),
        ),
        StrategyAttributionEvent(
            "e3",
            "b",
            "1",
            NOW,
            Decimal("3"),
        ),
    )
    result = StrategyAttributionAnalytics.pnl(events)
    assert result[0].strategy_id == "a"
    assert result[0].net_pnl == Decimal("14.5")
    assert result[0].event_count == 2
    assert result[1].net_pnl == Decimal("3")
    with pytest.raises(ValueError, match="duplicate attribution"):
        StrategyAttributionAnalytics.pnl((events[0], events[0]))


def test_correlation_uses_only_overlapping_periods() -> None:
    observations = (
        StrategyReturnObservation("a", "1", NOW, Decimal("0.01")),
        StrategyReturnObservation(
            "a",
            "1",
            NOW + timedelta(days=1),
            Decimal("0.02"),
        ),
        StrategyReturnObservation("b", "1", NOW, Decimal("0.02")),
        StrategyReturnObservation(
            "b",
            "1",
            NOW + timedelta(days=1),
            Decimal("0.04"),
        ),
        StrategyReturnObservation(
            "b",
            "1",
            NOW + timedelta(days=2),
            Decimal("-0.01"),
        ),
    )
    result = StrategyAttributionAnalytics.correlations(observations)
    assert len(result) == 1
    assert result[0].overlapping_periods == 2
    assert result[0].correlation == Decimal("1")


def test_zero_variance_correlation_is_zero() -> None:
    observations = (
        StrategyReturnObservation("a", "1", NOW, Decimal("0.01")),
        StrategyReturnObservation(
            "a",
            "1",
            NOW + timedelta(days=1),
            Decimal("0.01"),
        ),
        StrategyReturnObservation("b", "1", NOW, Decimal("0.02")),
        StrategyReturnObservation(
            "b",
            "1",
            NOW + timedelta(days=1),
            Decimal("0.03"),
        ),
    )
    result = StrategyAttributionAnalytics.correlations(observations)
    assert result[0].correlation == Decimal("0")
