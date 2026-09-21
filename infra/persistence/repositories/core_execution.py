"""Persistence repository for the canonical Core execution ownership graph."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.execution import ExecutionPlan
from apps.core.domain.execution_orders import ExecutionOrder
from apps.core.domain.positions import PositionGroup, PositionLeg
from infra.persistence.models.execution import (
    ExecutionPlanLegModel,
    ExecutionPlanModel,
)
from infra.persistence.models.execution_orders import ExecutionOrderModel
from infra.persistence.models.positions import (
    PositionGroupModel,
    PositionLegModel,
)


class CoreExecutionPersistenceRepository:
    """Flush-only writer for one canonical execution ownership root."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def persist_root(
        self,
        *,
        plan: ExecutionPlan,
        group: PositionGroup,
        position_legs: tuple[PositionLeg, ...],
        order: ExecutionOrder,
        recorded_at: datetime,
    ) -> None:
        await self._persist_plan(
            plan=plan,
            recorded_at=recorded_at,
        )

        for leg in plan.legs:
            await self._persist_plan_leg(
                plan_id=plan.plan_id,
                leg=leg,
                created_at=plan.created_at,
            )

        await self._persist_group(group)

        for leg in position_legs:
            await self._persist_position_leg(leg)

        await self._persist_order(
            user_id=plan.user_id,
            order=order,
        )

    async def _persist_plan(
        self,
        *,
        plan: ExecutionPlan,
        recorded_at: datetime,
    ) -> None:
        result = await self._session.execute(
            select(ExecutionPlanModel).where(
                ExecutionPlanModel.plan_id == plan.plan_id
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = ExecutionPlanModel(
                plan_id=plan.plan_id,
                intent_id=plan.intent_id,
                user_id=plan.user_id,
                shape=plan.shape.value,
                strategy=plan.strategy,
                strategy_version=plan.strategy_version,
                source=plan.source,
                created_at=plan.created_at,
                recorded_at=recorded_at,
                schema_version=1,
                metadata_payload={},
            )
            self._session.add(model)
        else:
            expected = (
                plan.intent_id,
                plan.user_id,
                plan.shape.value,
                plan.strategy,
                plan.strategy_version,
                plan.source,
                plan.created_at,
            )
            actual = (
                model.intent_id,
                model.user_id,
                model.shape,
                model.strategy,
                model.strategy_version,
                model.source,
                model.created_at,
            )
            if actual != expected:
                raise ValueError(
                    "persisted execution plan identity conflicts "
                    "with canonical plan"
                )

        await self._session.flush()

    async def _persist_plan_leg(
        self,
        *,
        plan_id: str,
        leg,
        created_at: datetime,
    ) -> None:
        result = await self._session.execute(
            select(ExecutionPlanLegModel).where(
                ExecutionPlanLegModel.plan_id == plan_id,
                ExecutionPlanLegModel.leg_id == leg.leg_id,
            )
        )
        model = result.scalar_one_or_none()

        expected = (
            str(leg.order_id),
            str(leg.client_order_id),
            str(leg.account_id.venue_id),
            leg.account_id.value,
            str(leg.instrument_id.venue_id),
            leg.instrument_id.native_symbol,
            leg.instrument_id.instrument_type.value,
            leg.instrument_id.asset_class.value,
            leg.side.value,
            leg.quantity,
            leg.order_type.value,
            leg.limit_price,
            leg.reduce_only,
        )

        if model is None:
            model = ExecutionPlanLegModel(
                plan_id=plan_id,
                leg_id=leg.leg_id,
                order_id=str(leg.order_id),
                client_order_id=str(leg.client_order_id),
                venue_id=str(leg.account_id.venue_id),
                account_value=leg.account_id.value,
                instrument_venue_id=str(
                    leg.instrument_id.venue_id
                ),
                native_symbol=leg.instrument_id.native_symbol,
                instrument_type=leg.instrument_id.instrument_type.value,
                asset_class=leg.instrument_id.asset_class.value,
                side=leg.side.value,
                quantity=leg.quantity,
                order_type=leg.order_type.value,
                limit_price=leg.limit_price,
                reduce_only=leg.reduce_only,
                created_at=created_at,
            )
            self._session.add(model)
        else:
            actual = (
                model.order_id,
                model.client_order_id,
                model.venue_id,
                model.account_value,
                model.instrument_venue_id,
                model.native_symbol,
                model.instrument_type,
                model.asset_class,
                model.side,
                model.quantity,
                model.order_type,
                model.limit_price,
                model.reduce_only,
            )
            if actual != expected:
                raise ValueError(
                    "persisted execution plan leg conflicts "
                    "with canonical leg"
                )

        await self._session.flush()

    async def _persist_group(
        self,
        group: PositionGroup,
    ) -> None:
        result = await self._session.execute(
            select(PositionGroupModel).where(
                PositionGroupModel.group_id == group.group_id
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = PositionGroupModel(
                group_id=group.group_id,
                plan_id=group.plan_id,
                user_id=group.user_id,
                shape=group.shape.value,
                strategy=group.strategy,
                strategy_version=group.strategy_version,
                trade_source=group.trade_source,
                status=group.status.value,
                opened_at=group.opened_at,
                closed_at=group.closed_at,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )
            self._session.add(model)
        else:
            if (
                model.plan_id != group.plan_id
                or model.user_id != group.user_id
            ):
                raise ValueError(
                    "persisted position group identity conflicts "
                    "with canonical group"
                )

            model.shape = group.shape.value
            model.strategy = group.strategy
            model.strategy_version = group.strategy_version
            model.trade_source = group.trade_source
            model.status = group.status.value
            model.opened_at = group.opened_at
            model.closed_at = group.closed_at
            model.updated_at = group.updated_at

        await self._session.flush()

    async def _persist_position_leg(
        self,
        leg: PositionLeg,
    ) -> None:
        result = await self._session.execute(
            select(PositionLegModel).where(
                PositionLegModel.group_id == leg.group_id,
                PositionLegModel.leg_id == leg.leg_id,
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = PositionLegModel(
                group_id=leg.group_id,
                leg_id=leg.leg_id,
                venue_id=str(leg.account_id.venue_id),
                account_value=leg.account_id.value,
                instrument_venue_id=str(
                    leg.instrument_id.venue_id
                ),
                native_symbol=leg.instrument_id.native_symbol,
                instrument_type=leg.instrument_id.instrument_type.value,
                asset_class=leg.instrument_id.asset_class.value,
                side=leg.side.value,
                target_quantity=leg.target_quantity,
                filled_quantity=leg.filled_quantity,
                current_quantity=leg.current_quantity,
                average_entry_price=leg.average_entry_price,
                average_exit_price=leg.average_exit_price,
                status=leg.status.value,
                opened_at=leg.opened_at,
                closed_at=leg.closed_at,
                created_at=leg.created_at,
                updated_at=leg.updated_at,
            )
            self._session.add(model)
        else:
            identity = (
                str(leg.account_id.venue_id),
                leg.account_id.value,
                str(leg.instrument_id.venue_id),
                leg.instrument_id.native_symbol,
                leg.instrument_id.instrument_type.value,
                leg.instrument_id.asset_class.value,
                leg.side.value,
                leg.target_quantity,
            )
            persisted_identity = (
                model.venue_id,
                model.account_value,
                model.instrument_venue_id,
                model.native_symbol,
                model.instrument_type,
                model.asset_class,
                model.side,
                model.target_quantity,
            )

            if persisted_identity != identity:
                raise ValueError(
                    "persisted position leg identity conflicts "
                    "with canonical leg"
                )

            model.filled_quantity = leg.filled_quantity
            model.current_quantity = leg.current_quantity
            model.average_entry_price = leg.average_entry_price
            model.average_exit_price = leg.average_exit_price
            model.status = leg.status.value
            model.opened_at = leg.opened_at
            model.closed_at = leg.closed_at
            model.updated_at = leg.updated_at

        await self._session.flush()

    async def _persist_order(
        self,
        *,
        user_id: int,
        order: ExecutionOrder,
    ) -> None:
        result = await self._session.execute(
            select(ExecutionOrderModel).where(
                ExecutionOrderModel.order_id == str(order.order_id)
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = ExecutionOrderModel(
                order_id=str(order.order_id),
                plan_id=order.plan_id,
                group_id=order.group_id,
                leg_id=order.leg_id,
                user_id=user_id,
                venue_id=str(order.account_id.venue_id),
                account_value=order.account_id.value,
                instrument_venue_id=str(
                    order.instrument_id.venue_id
                ),
                native_symbol=order.instrument_id.native_symbol,
                instrument_type=order.instrument_id.instrument_type.value,
                asset_class=order.instrument_id.asset_class.value,
                client_order_id=str(order.client_order_id),
                venue_order_id=(
                    str(order.venue_order_id)
                    if order.venue_order_id is not None
                    else None
                ),
                side=order.side.value,
                order_type=order.order_type.value,
                reduce_only=order.reduce_only,
                requested_quantity=order.requested_quantity,
                filled_quantity=order.filled_quantity,
                average_fill_price=order.average_fill_price,
                limit_price=order.limit_price,
                local_status=order.status.value,
                last_venue_status=None,
                last_venue_observed_at=None,
                venue_observation_source=None,
                rejection_reason=order.rejection_reason,
                submitted_at=order.submitted_at,
                accepted_at=order.accepted_at,
                filled_at=order.filled_at,
                cancelled_at=order.cancelled_at,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
            self._session.add(model)
        else:
            persisted_identity = (
                model.plan_id,
                model.group_id,
                model.leg_id,
                model.user_id,
                model.venue_id,
                model.account_value,
                model.instrument_venue_id,
                model.native_symbol,
                model.instrument_type,
                model.asset_class,
                model.client_order_id,
                model.side,
                model.order_type,
                model.reduce_only,
                model.requested_quantity,
                model.limit_price,
            )
            canonical_identity = (
                order.plan_id,
                order.group_id,
                order.leg_id,
                user_id,
                str(order.account_id.venue_id),
                order.account_id.value,
                str(order.instrument_id.venue_id),
                order.instrument_id.native_symbol,
                order.instrument_id.instrument_type.value,
                order.instrument_id.asset_class.value,
                str(order.client_order_id),
                order.side.value,
                order.order_type.value,
                order.reduce_only,
                order.requested_quantity,
                order.limit_price,
            )

            if persisted_identity != canonical_identity:
                raise ValueError(
                    "persisted execution order identity conflicts "
                    "with canonical order"
                )

            model.venue_order_id = (
                str(order.venue_order_id)
                if order.venue_order_id is not None
                else None
            )
            model.filled_quantity = order.filled_quantity
            model.average_fill_price = order.average_fill_price
            model.local_status = order.status.value
            model.rejection_reason = order.rejection_reason
            model.submitted_at = order.submitted_at
            model.accepted_at = order.accepted_at
            model.filled_at = order.filled_at
            model.cancelled_at = order.cancelled_at
            model.updated_at = order.updated_at

        await self._session.flush()


def leg_created_at_placeholder(plan_id: str):
    raise AssertionError(
        "ExecutionPlanLegModel.created_at must be supplied "
        f"from ExecutionPlan for plan {plan_id}"
    )
