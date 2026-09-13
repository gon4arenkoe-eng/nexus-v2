from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.aiea.application.drift_monitor import (
    AdaptationAction,
    ComparisonState,
    DriftMonitorService,
    DriftObservation,
)
from apps.aiea.domain.research import DriftState

NOW = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)


def obs(**overrides):
    values = dict(
        workspace_id="ws-1", user_id=7, strategy_id="trend-v2",
        champion_version="2.0.0", observed_at=NOW,
        evidence_at=NOW - timedelta(days=1), baseline_score=Decimal("1"),
        current_score=Decimal("0.90"), evidence_hash="champ-evidence",
    )
    values.update(overrides)
    return DriftObservation(**values)


def test_freshness_is_computed_from_evidence_age_not_supplied_ratio() -> None:
    decision = DriftMonitorService().assess(obs())
    assert decision.state is DriftState.HEALTHY
    assert Decimal("0") < decision.freshness_ratio < Decimal("1")
    assert decision.live_mutation_allowed is False


def test_stale_evidence_is_unknown_and_triggers_research_only() -> None:
    decision = DriftMonitorService().assess(obs(evidence_at=NOW - timedelta(days=8)))
    assert decision.state is DriftState.UNKNOWN
    assert decision.action is AdaptationAction.RESEARCH_CHALLENGER
    assert decision.comparison is ComparisonState.NOT_AVAILABLE
    assert decision.live_mutation_allowed is False


def test_degradation_triggers_challenger_research_without_activation() -> None:
    decision = DriftMonitorService().assess(obs(current_score=Decimal("0.40")))
    assert decision.state is DriftState.DEGRADED
    assert decision.action is AdaptationAction.RESEARCH_CHALLENGER
    assert decision.live_mutation_allowed is False


def test_challenger_material_lift_reaches_promotion_review_not_activation() -> None:
    decision = DriftMonitorService().assess(obs(
        current_score=Decimal("0.70"), challenger_version="2.1.0",
        challenger_score=Decimal("0.80"), challenger_evidence_hash="chall-evidence",
    ))
    assert decision.comparison is ComparisonState.CHALLENGER_PROMOTION_REVIEW
    assert decision.action is AdaptationAction.PROMOTION_REVIEW
    assert decision.challenger_lift is not None and decision.challenger_lift > Decimal("0.08")
    assert decision.live_mutation_allowed is False


def test_weak_challenger_retains_champion() -> None:
    decision = DriftMonitorService().assess(obs(
        challenger_version="2.1.0", challenger_score=Decimal("0.91"),
        challenger_evidence_hash="chall-evidence",
    ))
    assert decision.comparison is ComparisonState.CHAMPION_RETAINS
    assert decision.action is AdaptationAction.NONE
