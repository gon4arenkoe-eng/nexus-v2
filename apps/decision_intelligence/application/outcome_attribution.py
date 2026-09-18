"""Ledger-only attribution of immutable DecisionOutcome records."""

from __future__ import annotations

from collections.abc import Sequence

from decimal import Decimal
from hashlib import sha256

from apps.decision_intelligence.domain.decision import DecisionOutcome
from apps.decision_intelligence.ports.attribution import (
    DecisionExecutionLinkStore,
    ExecutionPlanLineageReader,
    LedgerAttributionReader,
)
from apps.decision_intelligence.ports.memory import DecisionMemoryStore


class DecisionOutcomeAttributionError(ValueError):
    """Attribution evidence is incomplete, inconsistent, or cross-owned."""


class LedgerDecisionOutcomeAttributionService:
    """Build one DecisionOutcome exclusively from canonical Ledger evidence."""

    def __init__(
        self,
        *,
        links: DecisionExecutionLinkStore,
        plans: ExecutionPlanLineageReader,
        ledger: LedgerAttributionReader,
        memory: DecisionMemoryStore,
    ) -> None:
        self._links = links
        self._plans = plans
        self._ledger = ledger
        self._memory = memory

    async def attribute(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
        outcome_id: str,
    ) -> DecisionOutcome:
        memory = await self._memory.rebuild(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
        )
        if memory is None:
            raise DecisionOutcomeAttributionError(
                "decision attribution requires existing same-owner decision memory"
            )
        if memory.outcome is not None:
            if memory.outcome.outcome_id != outcome_id:
                raise DecisionOutcomeAttributionError(
                    "decision already has a different immutable outcome"
                )
            return memory.outcome

        links = await self._links.list_for_decision(
            workspace_id=workspace_id,
            user_id=user_id,
            decision_id=decision_id,
        )
        if not links:
            raise DecisionOutcomeAttributionError(
                "trade decision requires at least one decision execution link"
            )

        intent_ids = tuple(sorted({item.intent_id for item in links}))
        plans = await self._plans.list_for_intents(
            user_id=user_id,
            intent_ids=intent_ids,
        )
        if not plans:
            raise DecisionOutcomeAttributionError(
                "no execution plans found for linked TradeIntent values"
            )

        linked_by_intent = {item.intent_id: item for item in links}
        plan_intents = {item.intent_id for item in plans}
        missing = set(intent_ids) - plan_intents
        if missing:
            raise DecisionOutcomeAttributionError(
                "linked TradeIntent has no canonical execution plan"
            )

        for plan in plans:
            link = linked_by_intent.get(plan.intent_id)
            if link is None or plan.user_id != user_id:
                raise DecisionOutcomeAttributionError("execution-plan ownership mismatch")
            if (
                plan.strategy_id != link.strategy_id
                or plan.strategy_version != link.strategy_version
            ):
                raise DecisionOutcomeAttributionError(
                    "execution-plan strategy lineage mismatch"
                )

        evidence = []
        seen_event_ids: set[str] = set()
        for plan in sorted(plans, key=lambda item: item.plan_id):
            events = await self._ledger.list_for_plan(
                user_id=user_id,
                plan_id=plan.plan_id,
            )
            if not events:
                raise DecisionOutcomeAttributionError(
                    "execution plan has no complete Ledger attribution evidence"
                )
            for event in events:
                if event.user_id != user_id or event.plan_id != plan.plan_id:
                    raise DecisionOutcomeAttributionError("Ledger ownership/plan mismatch")
                if event.event_id in seen_event_ids:
                    raise DecisionOutcomeAttributionError(
                        "duplicate Ledger attribution event_id"
                    )
                seen_event_ids.add(event.event_id)
                evidence.append(event)

        if not evidence:
            raise DecisionOutcomeAttributionError("no Ledger attribution evidence")

        evidence.sort(key=lambda item: (item.occurred_at, item.event_id))
        zero = Decimal("0")
        outcome = DecisionOutcome(
            outcome_id=outcome_id,
            decision_id=decision_id,
            evaluated_at=max(item.occurred_at for item in evidence),
            realized_pnl=sum((item.realized_pnl for item in evidence), zero),
            realized_r_multiple=sum(
                (item.realized_r_multiple for item in evidence), zero
            ),
            fees=sum((item.fees for item in evidence), zero),
            funding=sum((item.funding for item in evidence), zero),
            slippage=sum((item.slippage for item in evidence), zero),
            execution_quality_ref=_evidence_ref(evidence),
            reconciliation_evidence_refs=(),
        )
        await self._memory.append_outcome(
            workspace_id=workspace_id,
            user_id=user_id,
            value=outcome,
        )
        return outcome


def _evidence_ref(evidence: Sequence[object]) -> str:
    raw = "|".join(
        f"{item.event_id}:{item.plan_id}:{item.occurred_at.isoformat()}"  # type: ignore[attr-defined]
        for item in evidence
    )
    return f"ledger-attribution:{sha256(raw.encode('utf-8')).hexdigest()}"
