"""Deterministic strategy-portfolio decision services.

The service produces typed recommendations only. PortfolioRisk and Core remain
separate mandatory authorities for any trading action.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from hashlib import sha256

from apps.decision_intelligence.domain.decision import (
    DecisionObjective,
    DecisionState,
    MarketDecisionSnapshot,
    OpportunityEligibility,
    StrategyAllocationRecommendation,
    StrategyOpportunityAssessment,
    StrategyPortfolioDecision,
)
from apps.intelligence.domain.market_context import MarketContext


_ZERO = Decimal("0")
_ONE = Decimal("1")


def _hash(*parts: object) -> str:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return sha256(payload).hexdigest()


class MarketContextDecisionBridge:
    """Create immutable decision evidence from canonical Intelligence output."""

    def build_snapshot(
        self,
        *,
        snapshot_id: str,
        workspace_id: str,
        user_id: int,
        created_at: datetime,
        context: MarketContext,
        available_strategy_versions: tuple[str, ...],
        decision_policy_version: str = "decision-v1",
    ) -> MarketDecisionSnapshot:
        context_hash = _hash(
            context.instrument_id,
            context.as_of.isoformat(),
            context.regime,
            context.volatility,
            context.trend,
            context.liquidity,
            context.funding,
            context.event_risk,
            context.data_quality,
            context.data_quality_score,
            context.latest_price,
            context.spread_ratio,
            context.visible_depth_notional,
            context.funding_rate,
            context.open_interest,
            context.sources,
            context.blockers,
        )
        uncertainty = _ONE - context.data_quality_score
        if context.blockers:
            uncertainty = max(uncertainty, Decimal("0.75"))
        return MarketDecisionSnapshot(
            snapshot_id=snapshot_id,
            workspace_id=workspace_id,
            user_id=user_id,
            created_at=created_at,
            market_context_hash=context_hash,
            market_context_as_of=context.as_of,
            instruments=(context.instrument_id,),
            data_quality_state=context.data_quality.value,
            data_quality_score=context.data_quality_score,
            market_uncertainty=min(_ONE, uncertainty),
            market_state_tags={
                "regime": context.regime.value,
                "volatility": context.volatility.value,
                "trend": context.trend.value,
                "liquidity": context.liquidity.value,
                "funding": context.funding.value,
                "event_risk": context.event_risk.value,
                "data_quality": context.data_quality.value,
            },
            active_blockers=context.blockers,
            available_strategy_versions=available_strategy_versions,
            decision_policy_version=decision_policy_version,
            evidence_refs=(f"market-context:{context_hash}",),
        )


class DeterministicStrategyPortfolioManager:
    """Build a bounded portfolio recommendation from precomputed assessments."""

    def decide(
        self,
        *,
        decision_id: str,
        snapshot: MarketDecisionSnapshot,
        objective: DecisionObjective,
        assessments: tuple[StrategyOpportunityAssessment, ...],
        created_at: datetime,
    ) -> StrategyPortfolioDecision:
        if any(item.snapshot_id != snapshot.snapshot_id for item in assessments):
            raise ValueError("assessment/snapshot lineage mismatch")

        common_refs = tuple(
            sorted(
                set(snapshot.evidence_refs).union(
                    *(set(item.supporting_evidence) for item in assessments)
                )
            )
        )
        if snapshot.active_blockers:
            return self._no_trade(
                decision_id=decision_id,
                snapshot=snapshot,
                objective=objective,
                created_at=created_at,
                reasons=("MARKET_CONTEXT_BLOCKED", *snapshot.active_blockers),
                evidence_refs=common_refs,
            )
        if snapshot.data_quality_score < objective.min_data_quality:
            return self._no_trade(
                decision_id=decision_id,
                snapshot=snapshot,
                objective=objective,
                created_at=created_at,
                reasons=("DATA_QUALITY_BELOW_OBJECTIVE",),
                evidence_refs=common_refs,
            )

        eligible = tuple(
            item
            for item in assessments
            if item.eligibility is OpportunityEligibility.ELIGIBLE
            and item.expected_net_edge >= objective.min_expected_net_edge
            and item.data_quality_score >= objective.min_data_quality
        )
        if not eligible:
            return self._no_trade(
                decision_id=decision_id,
                snapshot=snapshot,
                objective=objective,
                created_at=created_at,
                reasons=("NO_ELIGIBLE_POSITIVE_EDGE",),
                evidence_refs=common_refs,
            )

        scored = tuple(
            sorted(
                ((item, max(_ZERO, item.deterministic_score)) for item in eligible),
                key=lambda pair: (pair[1], pair[0].strategy_id, pair[0].strategy_version),
                reverse=True,
            )
        )
        score_total = sum((score for _, score in scored), _ZERO)
        if score_total <= _ZERO:
            return self._no_trade(
                decision_id=decision_id,
                snapshot=snapshot,
                objective=objective,
                created_at=created_at,
                reasons=("NON_POSITIVE_PORTFOLIO_SCORE",),
                evidence_refs=common_refs,
            )

        risk_budget = min(objective.max_portfolio_risk, _ONE)
        preliminary: list[StrategyAllocationRecommendation] = []
        for assessment, score in scored:
            raw_weight = risk_budget * score / score_total
            weight = min(raw_weight, objective.max_strategy_weight)
            if weight <= _ZERO:
                continue
            preliminary.append(
                StrategyAllocationRecommendation(
                    strategy_id=assessment.strategy_id,
                    strategy_version=assessment.strategy_version,
                    target_weight=weight,
                    max_weight=objective.max_strategy_weight,
                    confidence=assessment.confidence,
                    expected_contribution=assessment.expected_net_edge * weight,
                    expected_risk_contribution=(
                        (assessment.drawdown_risk + assessment.tail_risk_score) / Decimal("2")
                    ) * weight,
                    parameter_set_ref=assessment.recommended_parameters_ref,
                    reason_codes=("DETERMINISTIC_SCORE_ALLOCATION",),
                )
            )

        if not preliminary:
            return self._no_trade(
                decision_id=decision_id,
                snapshot=snapshot,
                objective=objective,
                created_at=created_at,
                reasons=("ZERO_ALLOCATION_AFTER_CAPS",),
                evidence_refs=common_refs,
            )

        confidence = sum(
            (item.confidence * item.target_weight for item in preliminary), _ZERO
        ) / sum((item.target_weight for item in preliminary), _ZERO)
        uncertainty = max(
            snapshot.market_uncertainty,
            sum((assessment.uncertainty for assessment, _ in scored), _ZERO)
            / Decimal(len(scored)),
        )
        return StrategyPortfolioDecision(
            decision_id=decision_id,
            snapshot_id=snapshot.snapshot_id,
            workspace_id=snapshot.workspace_id,
            user_id=snapshot.user_id,
            created_at=created_at,
            state=DecisionState.REBALANCE,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            portfolio_confidence=min(_ONE, confidence),
            portfolio_uncertainty=min(_ONE, uncertainty),
            allocations=tuple(preliminary),
            reason_codes=("PORTFOLIO_OPPORTUNITIES_AVAILABLE",),
            decision_policy_version=snapshot.decision_policy_version,
            evidence_refs=common_refs,
        )

    @staticmethod
    def _no_trade(
        *,
        decision_id: str,
        snapshot: MarketDecisionSnapshot,
        objective: DecisionObjective,
        created_at: datetime,
        reasons: tuple[str, ...],
        evidence_refs: tuple[str, ...],
    ) -> StrategyPortfolioDecision:
        return StrategyPortfolioDecision(
            decision_id=decision_id,
            snapshot_id=snapshot.snapshot_id,
            workspace_id=snapshot.workspace_id,
            user_id=snapshot.user_id,
            created_at=created_at,
            state=DecisionState.NO_TRADE,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            portfolio_confidence=Decimal("1") - snapshot.market_uncertainty,
            portfolio_uncertainty=snapshot.market_uncertainty,
            allocations=(),
            reason_codes=reasons,
            decision_policy_version=snapshot.decision_policy_version,
            evidence_refs=evidence_refs,
        )
