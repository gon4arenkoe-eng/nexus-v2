"""SQLAlchemy adapters for DecisionOutcome attribution ports."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.decision_intelligence.domain.attribution import (
    DecisionExecutionLink,
    ExecutionPlanLineage,
    LedgerAttributionEvent,
)
from apps.decision_intelligence.ports.attribution import (
    DecisionExecutionLinkStore,
    ExecutionPlanLineageReader,
    LedgerAttributionReader,
)
from infra.persistence.models.execution import ExecutionPlanModel
from infra.persistence.repositories.decision_intelligence import (
    DecisionIntelligenceRecordRepository,
    DecisionStoredRecord,
)
from infra.persistence.repositories.ledger import ExecutionLedgerRepository


def _serialize_link(value: DecisionExecutionLink) -> str:
    return json.dumps(
        {
            "link_id": value.link_id,
            "workspace_id": value.workspace_id,
            "user_id": value.user_id,
            "decision_id": value.decision_id,
            "intent_id": value.intent_id,
            "strategy_id": value.strategy_id,
            "strategy_version": value.strategy_version,
            "linked_at": value.linked_at.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _link(payload_json: str) -> DecisionExecutionLink:
    value = json.loads(payload_json)
    if not isinstance(value, dict):
        raise ValueError("DecisionExecutionLink payload must be an object")
    return DecisionExecutionLink(
        link_id=str(value["link_id"]),
        workspace_id=str(value["workspace_id"]),
        user_id=int(value["user_id"]),
        decision_id=str(value["decision_id"]),
        intent_id=str(value["intent_id"]),
        strategy_id=str(value["strategy_id"]),
        strategy_version=str(value["strategy_version"]),
        linked_at=datetime.fromisoformat(str(value["linked_at"])),
    )


class DecisionExecutionLinkPersistenceStore(DecisionExecutionLinkStore):
    """Append-only decision -> TradeIntent lineage in the decision journal."""

    def __init__(self, repository: DecisionIntelligenceRecordRepository) -> None:
        self._repository = repository

    async def append(self, value: DecisionExecutionLink) -> None:
        decision = await self._repository.get(
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            record_type="decision",
            record_id=value.decision_id,
        )
        if decision is None:
            raise ValueError("execution link requires existing same-owner decision")

        existing = await self.list_for_decision(
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            decision_id=value.decision_id,
        )
        for item in existing:
            if item.intent_id == value.intent_id and item.link_id != value.link_id:
                raise ValueError(
                    "decision already links this TradeIntent with a different immutable link"
                )

        payload = _serialize_link(value)
        from hashlib import sha256

        await self._repository.append(
            DecisionStoredRecord(
                workspace_id=value.workspace_id,
                user_id=value.user_id,
                record_type="execution_link",
                record_id=value.link_id,
                parent_record_id=value.decision_id,
                content_hash=sha256(payload.encode("utf-8")).hexdigest(),
                payload_json=payload,
                created_at=value.linked_at,
            )
        )

    async def list_for_decision(
        self,
        *,
        workspace_id: str,
        user_id: int,
        decision_id: str,
    ) -> tuple[DecisionExecutionLink, ...]:
        records = await self._repository.list_children(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="execution_link",
            parent_record_id=decision_id,
        )
        return tuple(_link(item.payload_json) for item in records)


class ExecutionPlanPersistenceLineageReader(ExecutionPlanLineageReader):
    """Read canonical execution-plan lineage by TradeIntent identity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_intents(
        self,
        *,
        user_id: int,
        intent_ids: tuple[str, ...],
    ) -> tuple[ExecutionPlanLineage, ...]:
        if not intent_ids:
            return ()
        result = await self._session.execute(
            select(ExecutionPlanModel)
            .where(
                ExecutionPlanModel.user_id == user_id,
                ExecutionPlanModel.intent_id.in_(intent_ids),
            )
            .order_by(ExecutionPlanModel.intent_id, ExecutionPlanModel.plan_id)
        )
        values = []
        for model in result.scalars().all():
            if model.strategy_version is None:
                raise ValueError("execution plan attribution requires strategy_version")
            values.append(
                ExecutionPlanLineage(
                    plan_id=model.plan_id,
                    intent_id=model.intent_id,
                    user_id=model.user_id,
                    strategy_id=model.strategy,
                    strategy_version=model.strategy_version,
                )
            )
        return tuple(values)


def _restore_utc(value: datetime) -> datetime:
    """Restore UTC when a persistence backend drops timezone metadata."""

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


class LedgerPersistenceAttributionReader(LedgerAttributionReader):
    """Project explicit accounting fields from canonical FILL_RECORDED Ledger events."""

    def __init__(self, repository: ExecutionLedgerRepository) -> None:
        self._repository = repository

    async def list_for_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> tuple[LedgerAttributionEvent, ...]:
        events = await self._repository.list_for_plan(
            user_id=user_id,
            plan_id=plan_id,
        )
        result: list[LedgerAttributionEvent] = []
        for event in events:
            if event.event_type != "FILL_RECORDED":
                continue
            evidence = event.payload.get("decision_attribution")
            if evidence is None:
                continue
            if not isinstance(evidence, Mapping):
                raise ValueError("decision_attribution Ledger payload must be an object")
            if evidence.get("schema_version") != 1:
                raise ValueError("unsupported decision_attribution schema_version")
            result.append(
                LedgerAttributionEvent(
                    event_id=event.event_id,
                    plan_id=plan_id,
                    user_id=event.user_id,
                    occurred_at=_restore_utc(event.occurred_at),
                    realized_pnl=_decimal(evidence, "realized_pnl"),
                    realized_r_multiple=_decimal(evidence, "realized_r_multiple"),
                    fees=_decimal(evidence, "fees"),
                    funding=_decimal(evidence, "funding"),
                    slippage=_decimal(evidence, "slippage"),
                )
            )
        return tuple(result)


def _decimal(value: Mapping[str, object], field: str) -> Decimal:
    if field not in value:
        raise ValueError(f"decision_attribution payload missing {field}")
    try:
        result = Decimal(str(value[field]))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"decision_attribution {field} must be Decimal-compatible") from exc
    if not result.is_finite():
        raise ValueError(f"decision_attribution {field} must be finite")
    return result
