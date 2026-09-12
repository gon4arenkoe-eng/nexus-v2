"""Deterministic pair and basket execution coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from apps.core.application.execution_coordinator import (
    ExecutionCoordinatorOutcome,
)
from apps.core.domain.execution import ExecutionPlan
from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.execution_orders import ExecutionOrder
from apps.core.domain.intents import TradeIntentShape
from apps.core.domain.multi_leg_execution import (
    MultiLegExecutionError,
    MultiLegExecutionState,
    MultiLegRecoveryPolicy,
)
from apps.core.ports.multi_leg_execution import (
    MultiLegCheckpoint,
    MultiLegExecutionStateRecord,
    MultiLegExecutionStateStore,
)
from packages.contracts.primitives import require_non_negative_decimal


class SingleLegCoordinatorPort(Protocol):
    async def execute(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        ...

    async def recover(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        ...


class SingleLegCoordinatorFactory(Protocol):
    def for_order(
        self,
        order: ExecutionOrder,
    ) -> SingleLegCoordinatorPort:
        ...


@dataclass(frozen=True, slots=True)
class HedgeIntegrity:
    intact: bool
    max_ratio_drift: Decimal
    ratios: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class MultiLegExecutionOutcome:
    state: MultiLegExecutionState
    leg_outcomes: tuple[ExecutionCoordinatorOutcome, ...]
    hedge: HedgeIntegrity
    requires_recovery: bool
    idempotent: bool = False


def _checkpoint_from_outcome(
    outcome: ExecutionCoordinatorOutcome,
) -> MultiLegCheckpoint:
    return MultiLegCheckpoint(
        leg_id=outcome.order.leg_id,
        order_id=outcome.order.order_id,
        state=outcome.state,
        requested_quantity=outcome.order.requested_quantity,
        filled_quantity=outcome.order.filled_quantity,
        reduce_only=outcome.order.reduce_only,
    )


def _checkpoint_from_order(
    order: ExecutionOrder,
    state: ExecutionCoordinatorState,
) -> MultiLegCheckpoint:
    return MultiLegCheckpoint(
        leg_id=order.leg_id,
        order_id=order.order_id,
        state=state,
        requested_quantity=order.requested_quantity,
        filled_quantity=order.filled_quantity,
        reduce_only=order.reduce_only,
    )


class MultiLegExecutionCoordinator:
    """Own deterministic pair/basket workflow above single-leg coordinators."""

    def __init__(
        self,
        *,
        user_id: int,
        state_store: MultiLegExecutionStateStore,
        single_leg_factory: SingleLegCoordinatorFactory,
        shape: TradeIntentShape,
        recovery_policy: MultiLegRecoveryPolicy = (
            MultiLegRecoveryPolicy.FAIL_CLOSED
        ),
        hedge_tolerance: Decimal = Decimal("0"),
    ) -> None:
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")
        if shape is TradeIntentShape.SINGLE_LEG:
            raise ValueError("multi-leg coordinator requires PAIR or BASKET")
        if not isinstance(recovery_policy, MultiLegRecoveryPolicy):
            raise ValueError("invalid recovery_policy")
        tolerance = require_non_negative_decimal(
            hedge_tolerance,
            field_name="hedge_tolerance",
        )
        if tolerance > Decimal("1"):
            raise ValueError("hedge_tolerance must not exceed 1")
        self._user_id = user_id
        self._state_store = state_store
        self._single_leg_factory = single_leg_factory
        self._shape = shape
        self._recovery_policy = recovery_policy
        self._hedge_tolerance = tolerance

    async def execute(
        self,
        plan: ExecutionPlan,
        orders: tuple[ExecutionOrder, ...],
        *,
        now: datetime,
    ) -> MultiLegExecutionOutcome:
        ordered = self._validate(plan, orders)
        existing = await self._state_store.load(
            user_id=self._user_id,
            plan_id=plan.plan_id,
        )
        if existing is not None:
            if existing.group_id != ordered[0].group_id:
                raise MultiLegExecutionError(
                    "persisted multi-leg group identity mismatch"
                )
            if existing.state in (
                MultiLegExecutionState.OPEN,
                MultiLegExecutionState.CLOSED,
                MultiLegExecutionState.FAILED,
            ):
                hedge = self._hedge(existing.legs)
                return MultiLegExecutionOutcome(
                    state=existing.state,
                    leg_outcomes=(),
                    hedge=hedge,
                    requires_recovery=False,
                    idempotent=True,
                )
            return await self.recover(plan, orders, now=now)

        opening = not ordered[0].reduce_only
        initial_state = (
            MultiLegExecutionState.OPENING
            if opening
            else MultiLegExecutionState.CLOSING
        )
        initial = MultiLegExecutionStateRecord(
            user_id=self._user_id,
            plan_id=plan.plan_id,
            group_id=ordered[0].group_id,
            shape=self._shape,
            state=initial_state,
            recovery_policy=self._recovery_policy,
            legs=tuple(
                _checkpoint_from_order(
                    order,
                    ExecutionCoordinatorState.PENDING,
                )
                for order in ordered
            ),
            created_at=now,
            updated_at=now,
        )
        await self._state_store.checkpoint(initial)

        outcomes: list[ExecutionCoordinatorOutcome] = []
        checkpoints: list[MultiLegCheckpoint] = []
        for order in ordered:
            coordinator = self._single_leg_factory.for_order(order)
            outcome = await coordinator.execute(order, now=now)
            outcomes.append(outcome)
            checkpoints.append(_checkpoint_from_outcome(outcome))
            remaining = ordered[len(checkpoints):]
            provisional = tuple(checkpoints) + tuple(
                _checkpoint_from_order(
                    item,
                    ExecutionCoordinatorState.PENDING,
                )
                for item in remaining
            )
            state = self._derive_state(provisional, opening=opening)
            await self._state_store.checkpoint(
                MultiLegExecutionStateRecord(
                    user_id=self._user_id,
                    plan_id=plan.plan_id,
                    group_id=ordered[0].group_id,
                    shape=self._shape,
                    state=state,
                    recovery_policy=self._recovery_policy,
                    legs=provisional,
                    created_at=initial.created_at,
                    updated_at=now,
                )
            )
            if outcome.requires_recovery:
                break
            if outcome.state is ExecutionCoordinatorState.FAILED:
                break

        record = await self._state_store.load(
            user_id=self._user_id,
            plan_id=plan.plan_id,
        )
        if record is None:
            raise MultiLegExecutionError("multi-leg checkpoint disappeared")
        hedge = self._hedge(record.legs)
        return MultiLegExecutionOutcome(
            state=record.state,
            leg_outcomes=tuple(outcomes),
            hedge=hedge,
            requires_recovery=(
                record.state is MultiLegExecutionState.RECOVERY
            ),
        )

    async def recover(
        self,
        plan: ExecutionPlan,
        orders: tuple[ExecutionOrder, ...],
        *,
        now: datetime,
    ) -> MultiLegExecutionOutcome:
        ordered = self._validate(plan, orders)
        record = await self._state_store.load(
            user_id=self._user_id,
            plan_id=plan.plan_id,
        )
        if record is None:
            raise MultiLegExecutionError("recovery requires persisted state")
        if record.group_id != ordered[0].group_id:
            raise MultiLegExecutionError("multi-leg recovery group mismatch")
        if record.state in (
            MultiLegExecutionState.OPEN,
            MultiLegExecutionState.CLOSED,
            MultiLegExecutionState.FAILED,
        ):
            return MultiLegExecutionOutcome(
                state=record.state,
                leg_outcomes=(),
                hedge=self._hedge(record.legs),
                requires_recovery=False,
                idempotent=True,
            )

        prior = {item.leg_id: item for item in record.legs}
        outcomes: list[ExecutionCoordinatorOutcome] = []
        checkpoints: list[MultiLegCheckpoint] = []
        for order in ordered:
            previous = prior[order.leg_id]
            coordinator = self._single_leg_factory.for_order(order)
            if previous.state is ExecutionCoordinatorState.PENDING:
                outcome = await coordinator.execute(order, now=now)
                outcomes.append(outcome)
                checkpoints.append(_checkpoint_from_outcome(outcome))
            elif previous.state in (
                ExecutionCoordinatorState.OPENING,
                ExecutionCoordinatorState.CLOSING,
                ExecutionCoordinatorState.RECOVERY,
            ):
                outcome = await coordinator.recover(order, now=now)
                outcomes.append(outcome)
                checkpoints.append(_checkpoint_from_outcome(outcome))
            else:
                checkpoints.append(previous)

        opening = not ordered[0].reduce_only
        state = self._derive_state(tuple(checkpoints), opening=opening)
        updated = MultiLegExecutionStateRecord(
            user_id=self._user_id,
            plan_id=plan.plan_id,
            group_id=record.group_id,
            shape=record.shape,
            state=state,
            recovery_policy=record.recovery_policy,
            legs=tuple(checkpoints),
            created_at=record.created_at,
            updated_at=now,
        )
        await self._state_store.checkpoint(updated)
        hedge = self._hedge(updated.legs)
        return MultiLegExecutionOutcome(
            state=state,
            leg_outcomes=tuple(outcomes),
            hedge=hedge,
            requires_recovery=(
                state is MultiLegExecutionState.RECOVERY
            ),
        )

    async def coordinated_close(
        self,
        plan: ExecutionPlan,
        orders: tuple[ExecutionOrder, ...],
        *,
        now: datetime,
    ) -> MultiLegExecutionOutcome:
        ordered = self._validate(plan, orders)
        if not all(order.reduce_only for order in ordered):
            raise MultiLegExecutionError(
                "coordinated close requires reduce-only orders"
            )
        return await self.execute(plan, orders, now=now)

    def _validate(
        self,
        plan: ExecutionPlan,
        orders: tuple[ExecutionOrder, ...],
    ) -> tuple[ExecutionOrder, ...]:
        if plan.user_id != self._user_id:
            raise MultiLegExecutionError("plan user ownership mismatch")
        if plan.shape is not self._shape:
            raise MultiLegExecutionError("execution plan shape mismatch")
        if not isinstance(orders, tuple):
            raise ValueError("orders must be a tuple")
        expected_count = 2 if self._shape is TradeIntentShape.PAIR else None
        if expected_count is not None and len(orders) != expected_count:
            raise MultiLegExecutionError("PAIR requires exactly two orders")
        if self._shape is TradeIntentShape.BASKET and len(orders) < 2:
            raise MultiLegExecutionError("BASKET requires at least two orders")
        by_leg = {order.leg_id: order for order in orders}
        if len(by_leg) != len(orders):
            raise MultiLegExecutionError("order leg IDs must be unique")
        if set(by_leg) != {leg.leg_id for leg in plan.legs}:
            raise MultiLegExecutionError("orders must exactly match plan legs")
        ordered = tuple(by_leg[leg.leg_id] for leg in plan.legs)
        group_ids = {order.group_id for order in ordered}
        if len(group_ids) != 1:
            raise MultiLegExecutionError("all legs must share one group_id")
        reduce_modes = {order.reduce_only for order in ordered}
        if len(reduce_modes) != 1:
            raise MultiLegExecutionError(
                "opening and closing legs must not be mixed"
            )
        for leg, order in zip(plan.legs, ordered, strict=True):
            if order.plan_id != plan.plan_id:
                raise MultiLegExecutionError("order plan ownership mismatch")
            if order.order_id != leg.order_id:
                raise MultiLegExecutionError("order_id does not match plan")
            if order.client_order_id != leg.client_order_id:
                raise MultiLegExecutionError(
                    "client_order_id does not match plan"
                )
            if order.account_id != leg.account_id:
                raise MultiLegExecutionError("account does not match plan")
            if order.instrument_id != leg.instrument_id:
                raise MultiLegExecutionError("instrument does not match plan")
            if order.requested_quantity != leg.quantity:
                raise MultiLegExecutionError("quantity does not match plan")
            if order.side.value != leg.side.value:
                raise MultiLegExecutionError("side does not match plan")
            if order.reduce_only != leg.reduce_only:
                raise MultiLegExecutionError(
                    "reduce_only does not match plan"
                )
        return ordered

    def _hedge(
        self,
        legs: tuple[MultiLegCheckpoint, ...],
    ) -> HedgeIntegrity:
        ratios = tuple(
            leg.filled_quantity / leg.requested_quantity
            for leg in legs
        )
        drift = max(ratios) - min(ratios)
        return HedgeIntegrity(
            intact=drift <= self._hedge_tolerance,
            max_ratio_drift=drift,
            ratios=ratios,
        )

    def _derive_state(
        self,
        legs: tuple[MultiLegCheckpoint, ...],
        *,
        opening: bool,
    ) -> MultiLegExecutionState:
        hedge = self._hedge(legs)
        states = tuple(item.state for item in legs)
        any_exposure = any(
            item.filled_quantity > 0
            for item in legs
        )
        if any(
            state is ExecutionCoordinatorState.RECOVERY
            for state in states
        ):
            return MultiLegExecutionState.RECOVERY
        if any(state is ExecutionCoordinatorState.FAILED for state in states):
            return (
                MultiLegExecutionState.RECOVERY
                if any_exposure
                else MultiLegExecutionState.FAILED
            )
        if not hedge.intact and any_exposure:
            return MultiLegExecutionState.RECOVERY
        if opening:
            if all(
                state is ExecutionCoordinatorState.OPEN
                for state in states
            ):
                return MultiLegExecutionState.OPEN
            if all(
                state is ExecutionCoordinatorState.CLOSED
                for state in states
            ):
                return MultiLegExecutionState.FAILED
            return MultiLegExecutionState.OPENING
        if all(state is ExecutionCoordinatorState.CLOSED for state in states):
            return MultiLegExecutionState.CLOSED
        return MultiLegExecutionState.CLOSING


class PairExecutionCoordinator(MultiLegExecutionCoordinator):
    def __init__(self, **kwargs) -> None:
        super().__init__(shape=TradeIntentShape.PAIR, **kwargs)


class BasketExecutionCoordinator(MultiLegExecutionCoordinator):
    def __init__(self, **kwargs) -> None:
        super().__init__(shape=TradeIntentShape.BASKET, **kwargs)
