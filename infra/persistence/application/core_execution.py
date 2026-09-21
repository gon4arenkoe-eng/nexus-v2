"""Transactional application service for Core execution-root persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from apps.core.domain.execution import ExecutionPlan
from apps.core.domain.execution_orders import ExecutionOrder
from apps.core.domain.positions import PositionGroup, PositionLeg
from infra.persistence.repositories.core_execution import (
    CoreExecutionPersistenceRepository,
)


class CoreExecutionPersistenceService:
    """Persist one canonical execution ownership root atomically."""

    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = factory

    async def persist_root(
        self,
        *,
        plan: ExecutionPlan,
        group: PositionGroup,
        position_legs: tuple[PositionLeg, ...],
        order: ExecutionOrder,
        recorded_at: datetime | None = None,
    ) -> None:
        self._validate_graph(
            plan=plan,
            group=group,
            position_legs=position_legs,
            order=order,
        )

        observed_at = (
            datetime.now(UTC)
            if recorded_at is None
            else recorded_at
        )

        async with self._factory() as session:
            repository = CoreExecutionPersistenceRepository(
                session
            )

            try:
                await repository.persist_root(
                    plan=plan,
                    group=group,
                    position_legs=position_legs,
                    order=order,
                    recorded_at=observed_at,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    def _validate_graph(
        *,
        plan: ExecutionPlan,
        group: PositionGroup,
        position_legs: tuple[PositionLeg, ...],
        order: ExecutionOrder,
    ) -> None:
        if group.plan_id != plan.plan_id:
            raise ValueError(
                "position group plan_id must match execution plan"
            )

        if group.user_id != plan.user_id:
            raise ValueError(
                "position group user_id must match execution plan"
            )

        if (
            group.shape is not plan.shape
            or group.strategy != plan.strategy
            or group.strategy_version != plan.strategy_version
            or group.trade_source != plan.source
        ):
            raise ValueError(
                "position group lineage must match execution plan"
            )

        plan_legs = {
            leg.leg_id: leg
            for leg in plan.legs
        }
        position_by_id = {
            leg.leg_id: leg
            for leg in position_legs
        }

        if set(position_by_id) != set(plan_legs):
            raise ValueError(
                "position legs must exactly match execution plan legs"
            )

        for leg_id, position_leg in position_by_id.items():
            planned = plan_legs[leg_id]

            if position_leg.group_id != group.group_id:
                raise ValueError(
                    "position leg group_id must match position group"
                )

            if (
                position_leg.account_id != planned.account_id
                or position_leg.instrument_id != planned.instrument_id
                or position_leg.side is not planned.side
                or position_leg.target_quantity != planned.quantity
            ):
                raise ValueError(
                    "position leg identity must match execution plan leg"
                )

        planned_order = next(
            (
                leg
                for leg in plan.legs
                if leg.leg_id == order.leg_id
            ),
            None,
        )

        if planned_order is None:
            raise ValueError(
                "execution order leg_id is not present in execution plan"
            )

        if (
            order.plan_id != plan.plan_id
            or order.group_id != group.group_id
            or order.order_id != planned_order.order_id
            or order.client_order_id
            != planned_order.client_order_id
            or order.account_id != planned_order.account_id
            or order.instrument_id != planned_order.instrument_id
            or order.side.value != planned_order.side.value
            or order.order_type is not planned_order.order_type
            or order.requested_quantity
            != planned_order.quantity
            or order.limit_price != planned_order.limit_price
            or order.reduce_only != planned_order.reduce_only
        ):
            raise ValueError(
                "execution order identity must match execution plan leg"
            )
