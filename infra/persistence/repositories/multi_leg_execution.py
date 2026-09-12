"""Repository for durable pair/basket execution state."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.intents import TradeIntentShape
from apps.core.domain.multi_leg_execution import (
    MultiLegExecutionState,
    MultiLegRecoveryPolicy,
)
from apps.core.ports.multi_leg_execution import (
    MultiLegCheckpoint,
    MultiLegExecutionStateRecord,
)
from infra.persistence.models.multi_leg_execution import (
    MultiLegExecutionStateModel,
)
from packages.contracts.identities import OrderId


class MultiLegExecutionStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> MultiLegExecutionStateRecord | None:
        result = await self._session.execute(
            select(MultiLegExecutionStateModel).where(
                MultiLegExecutionStateModel.user_id == user_id,
                MultiLegExecutionStateModel.plan_id == plan_id,
            )
        )
        model = result.scalar_one_or_none()
        return None if model is None else self._to_record(model)

    async def upsert(self, record: MultiLegExecutionStateRecord) -> None:
        model = await self._session.get(
            MultiLegExecutionStateModel,
            (record.user_id, record.plan_id),
        )
        payload = self._serialize_legs(record.legs)
        if model is None:
            self._session.add(
                MultiLegExecutionStateModel(
                    user_id=record.user_id,
                    plan_id=record.plan_id,
                    group_id=record.group_id,
                    shape=record.shape.value,
                    state=record.state.value,
                    recovery_policy=record.recovery_policy.value,
                    legs_json=payload,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                )
            )
            return
        if (
            model.group_id != record.group_id
            or model.shape != record.shape.value
        ):
            raise ValueError("persisted multi-leg ownership conflict")
        model.state = record.state.value
        model.recovery_policy = record.recovery_policy.value
        model.legs_json = payload
        model.updated_at = record.updated_at

    @staticmethod
    def _serialize_legs(legs: tuple[MultiLegCheckpoint, ...]) -> str:
        return json.dumps(
            [
                {
                    "leg_id": item.leg_id,
                    "order_id": str(item.order_id),
                    "state": item.state.value,
                    "requested_quantity": str(item.requested_quantity),
                    "filled_quantity": str(item.filled_quantity),
                    "reduce_only": item.reduce_only,
                }
                for item in legs
            ],
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _restore_utc(value):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @classmethod
    def _to_record(
        cls,
        model: MultiLegExecutionStateModel,
    ) -> MultiLegExecutionStateRecord:
        raw = json.loads(model.legs_json)
        legs = tuple(
            MultiLegCheckpoint(
                leg_id=item["leg_id"],
                order_id=OrderId(item["order_id"]),
                state=ExecutionCoordinatorState(item["state"]),
                requested_quantity=Decimal(item["requested_quantity"]),
                filled_quantity=Decimal(item["filled_quantity"]),
                reduce_only=item["reduce_only"],
            )
            for item in raw
        )
        return MultiLegExecutionStateRecord(
            user_id=model.user_id,
            plan_id=model.plan_id,
            group_id=model.group_id,
            shape=TradeIntentShape(model.shape),
            state=MultiLegExecutionState(model.state),
            recovery_policy=MultiLegRecoveryPolicy(model.recovery_policy),
            legs=legs,
            created_at=cls._restore_utc(model.created_at),
            updated_at=cls._restore_utc(model.updated_at),
        )
