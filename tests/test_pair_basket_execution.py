"""Phase 5 tests for pair/basket execution coordination."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.application.execution_coordinator import (
    ExecutionCoordinatorOutcome,
)
from apps.core.application.multi_leg_execution import (
    BasketExecutionCoordinator,
    PairExecutionCoordinator,
)
from apps.core.domain.execution import ExecutionLegPlan, ExecutionPlan
from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.multi_leg_execution import (
    MultiLegExecutionError,
    MultiLegExecutionState,
    MultiLegRecoveryPolicy,
)
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.multi_leg_execution import (
    MultiLegCheckpoint,
    MultiLegExecutionStateRecord,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    OrderId,
    VenueId,
)


NOW = datetime(2026, 9, 12, 13, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BINANCE"), 7)


def instrument(symbol: str) -> InstrumentId:
    return InstrumentId(
        VenueId("BINANCE"),
        symbol,
        InstrumentType.PERPETUAL,
        AssetClass.CRYPTO,
    )


def make_plan(
    *,
    shape: TradeIntentShape = TradeIntentShape.PAIR,
    leg_count: int = 2,
    reduce_only: bool = False,
    plan_id: str = "plan-pair-1",
) -> ExecutionPlan:
    legs = tuple(
        ExecutionLegPlan(
            leg_id=f"leg-{index}",
            order_id=OrderId(f"order-{index}"),
            client_order_id=ClientOrderId(f"client-{index}"),
            account_id=ACCOUNT,
            instrument_id=instrument(f"ASSET{index}USDT"),
            side=TradeSide.BUY if index % 2 == 1 else TradeSide.SELL,
            quantity=Decimal(str(index)),
            order_type=OrderType.MARKET,
            reduce_only=reduce_only,
        )
        for index in range(1, leg_count + 1)
    )
    return ExecutionPlan(
        plan_id=plan_id,
        intent_id=f"intent-{plan_id}",
        user_id=7,
        shape=shape,
        strategy="stat-arb",
        strategy_version="v1",
        source="test",
        legs=legs,
        created_at=NOW,
    )


def make_orders(
    plan: ExecutionPlan,
    *,
    group_id: str = "group-1",
) -> tuple[ExecutionOrder, ...]:
    return tuple(
        ExecutionOrder(
            order_id=leg.order_id,
            plan_id=plan.plan_id,
            group_id=group_id,
            leg_id=leg.leg_id,
            account_id=leg.account_id,
            instrument_id=leg.instrument_id,
            client_order_id=leg.client_order_id,
            venue_order_id=None,
            side=OrderSide(leg.side.value),
            order_type=leg.order_type,
            requested_quantity=leg.quantity,
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            limit_price=leg.limit_price,
            reduce_only=leg.reduce_only,
            status=ExecutionOrderStatus.PENDING,
            rejection_reason=None,
            submitted_at=None,
            accepted_at=None,
            filled_at=None,
            cancelled_at=None,
            created_at=NOW,
            updated_at=NOW,
        )
        for leg in plan.legs
    )


class MemoryMultiLegStore:

    def __init__(self) -> None:
        self.records: dict[tuple[int, str], MultiLegExecutionStateRecord] = {}

    async def load(self, *, user_id: int, plan_id: str):
        return self.records.get((user_id, plan_id))

    async def checkpoint(self, record: MultiLegExecutionStateRecord) -> None:
        self.records[(record.user_id, record.plan_id)] = record


class ScriptedSingleLeg:

    def __init__(self, execute_outcomes, recover_outcomes=None) -> None:
        self.execute_outcomes = list(execute_outcomes)
        self.recover_outcomes = list(recover_outcomes or [])
        self.execute_calls = 0
        self.recover_calls = 0

    async def execute(self, order: ExecutionOrder, *, now: datetime):
        self.execute_calls += 1
        spec = self.execute_outcomes.pop(0)
        if len(spec) == 3:
            state, filled, recovery = spec
            return outcome(
                order,
                state,
                filled,
                now=now,
                recovery=recovery,
            )
        state, filled = spec
        return outcome(order, state, filled, now=now)

    async def recover(self, order: ExecutionOrder, *, now: datetime):
        self.recover_calls += 1
        spec = self.recover_outcomes.pop(0)
        if len(spec) == 3:
            state, filled, recovery = spec
            return outcome(
                order,
                state,
                filled,
                now=now,
                recovery=recovery,
            )
        state, filled = spec
        return outcome(order, state, filled, now=now)


class Factory:

    def __init__(self, scripts: dict[str, ScriptedSingleLeg]) -> None:
        self.scripts = scripts

    def for_order(self, order: ExecutionOrder):
        return self.scripts[order.leg_id]


def outcome(
    order: ExecutionOrder,
    state: ExecutionCoordinatorState,
    filled: Decimal,
    *,
    now: datetime,
    recovery: bool = False,
) -> ExecutionCoordinatorOutcome:
    if filled == order.requested_quantity:
        status = ExecutionOrderStatus.FILLED
    elif filled > 0:
        status = ExecutionOrderStatus.PARTIALLY_FILLED
    elif state is ExecutionCoordinatorState.FAILED:
        status = ExecutionOrderStatus.REJECTED
    elif state is ExecutionCoordinatorState.RECOVERY:
        status = ExecutionOrderStatus.UNKNOWN
    else:
        status = ExecutionOrderStatus.ACCEPTED
    rejection = "rejected" if status is ExecutionOrderStatus.REJECTED else None
    updated = replace(
        order,
        status=status,
        filled_quantity=filled,
        average_fill_price=Decimal("100") if filled > 0 else None,
        rejection_reason=rejection,
        submitted_at=now,
        accepted_at=(
            now
            if status in (
                ExecutionOrderStatus.ACCEPTED,
                ExecutionOrderStatus.PARTIALLY_FILLED,
                ExecutionOrderStatus.FILLED,
            )
            else None
        ),
        filled_at=(now if status is ExecutionOrderStatus.FILLED else None),
        updated_at=now,
    )
    return ExecutionCoordinatorOutcome(
        order=updated,
        state=state,
        attempt=1,
        venue_result=None,
        requires_recovery=recovery,
    )


def test_pair_full_fill_opens_with_intact_hedge() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("1"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.OPEN
    assert result.hedge.intact is True
    assert result.hedge.max_ratio_drift == 0
    assert result.requires_recovery is False


def test_pair_partial_fill_ratio_mismatch_enters_recovery() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0.5"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0.4"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.RECOVERY
    assert result.hedge.intact is False
    assert result.requires_recovery is True


def test_pair_matched_partial_fill_remains_opening_and_hedged() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0.5"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("1.0"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.OPENING
    assert result.hedge.intact is True


def test_filled_first_leg_and_rejected_second_never_reports_open() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("1"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.FAILED, Decimal("0"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.RECOVERY
    assert result.requires_recovery is True


def test_unknown_first_leg_stops_before_creating_more_exposure() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.RECOVERY, Decimal("0"), True)]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        result = await coordinator.execute(plan, orders, now=NOW)
        return result, scripts["leg-2"].execute_calls
    result, second_calls = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.RECOVERY
    assert second_calls == 0


def test_partial_fill_recovery_can_restore_pair_integrity() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0.5"))],
            [(ExecutionCoordinatorState.OPEN, Decimal("1"))],
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0.4"))],
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))],
        ),
    }
    store = MemoryMultiLegStore()

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=store,
            single_leg_factory=Factory(scripts),
        )
        first = await coordinator.execute(plan, orders, now=NOW)
        current_orders = tuple(item.order for item in first.leg_outcomes)
        second = await coordinator.recover(plan, current_orders, now=NOW)
        return first, second
    first, second = asyncio.run(scenario())
    assert first.state is MultiLegExecutionState.RECOVERY
    assert second.state is MultiLegExecutionState.OPEN
    assert second.hedge.intact is True


def test_restart_execute_recovers_active_pair_instead_of_resubmitting(
) -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0"))],
            [(ExecutionCoordinatorState.OPEN, Decimal("1"))],
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPENING, Decimal("0"))],
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))],
        ),
    }
    store = MemoryMultiLegStore()

    async def scenario():
        first = PairExecutionCoordinator(
            user_id=7,
            state_store=store,
            single_leg_factory=Factory(scripts),
        )
        opened = await first.execute(plan, orders, now=NOW)
        current_orders = tuple(item.order for item in opened.leg_outcomes)
        restarted = PairExecutionCoordinator(
            user_id=7,
            state_store=store,
            single_leg_factory=Factory(scripts),
        )
        recovered = await restarted.execute(plan, current_orders, now=NOW)
        return recovered
    recovered = asyncio.run(scenario())
    assert recovered.state is MultiLegExecutionState.OPEN
    assert scripts["leg-1"].execute_calls == 1
    assert scripts["leg-2"].execute_calls == 1
    assert scripts["leg-1"].recover_calls == 1
    assert scripts["leg-2"].recover_calls == 1


def test_terminal_pair_execute_is_idempotent() -> None:
    plan = make_plan()
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("1"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))]
        ),
    }
    store = MemoryMultiLegStore()

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=store,
            single_leg_factory=Factory(scripts),
        )
        await coordinator.execute(plan, orders, now=NOW)
        return await coordinator.execute(plan, orders, now=NOW)
    duplicate = asyncio.run(scenario())
    assert duplicate.idempotent is True
    assert duplicate.state is MultiLegExecutionState.OPEN
    assert scripts["leg-1"].execute_calls == 1
    assert scripts["leg-2"].execute_calls == 1


def test_coordinated_pair_close_requires_reduce_only_and_closes_all_legs(
) -> None:
    plan = make_plan(reduce_only=True, plan_id="close-plan")
    orders = make_orders(plan)
    scripts = {
        "leg-1": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.CLOSED, Decimal("1"))]
        ),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.CLOSED, Decimal("2"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.coordinated_close(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.CLOSED
    assert result.hedge.intact is True


def test_basket_execution_owns_all_legs_and_opens_when_hedged() -> None:
    plan = make_plan(shape=TradeIntentShape.BASKET, leg_count=3)
    orders = make_orders(plan)
    scripts = {
        order.leg_id: ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, order.requested_quantity)]
        )
        for order in orders
    }

    async def scenario():
        coordinator = BasketExecutionCoordinator(
            user_id=7,
            state_store=MemoryMultiLegStore(),
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)
    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.OPEN
    assert len(result.leg_outcomes) == 3
    assert result.hedge.intact is True


def test_pair_rejects_cross_group_contamination() -> None:
    plan = make_plan()
    orders = list(make_orders(plan))
    orders[1] = replace(orders[1], group_id="other-group")
    coordinator = PairExecutionCoordinator(
        user_id=7,
        state_store=MemoryMultiLegStore(),
        single_leg_factory=Factory({}),
    )
    with pytest.raises(MultiLegExecutionError, match="share one group"):
        asyncio.run(coordinator.execute(plan, tuple(orders), now=NOW))


def test_pair_rejects_mixed_open_and_close_legs() -> None:
    plan = make_plan()
    orders = list(make_orders(plan))
    orders[1] = replace(orders[1], reduce_only=True)
    coordinator = PairExecutionCoordinator(
        user_id=7,
        state_store=MemoryMultiLegStore(),
        single_leg_factory=Factory({}),
    )
    with pytest.raises(MultiLegExecutionError, match="must not be mixed"):
        asyncio.run(coordinator.execute(plan, tuple(orders), now=NOW))


def test_pair_rejects_wrong_user_ownership() -> None:
    plan = replace(make_plan(), user_id=8)
    coordinator = PairExecutionCoordinator(
        user_id=7,
        state_store=MemoryMultiLegStore(),
        single_leg_factory=Factory({}),
    )
    with pytest.raises(MultiLegExecutionError, match="user ownership"):
        asyncio.run(coordinator.execute(plan, make_orders(plan), now=NOW))


def test_restart_after_first_leg_fill_executes_never_submitted_second_leg(
) -> None:
    plan = make_plan()
    orders = make_orders(plan)
    store = MemoryMultiLegStore()
    record = MultiLegExecutionStateRecord(
        user_id=7,
        plan_id=plan.plan_id,
        group_id="group-1",
        shape=TradeIntentShape.PAIR,
        state=MultiLegExecutionState.RECOVERY,
        recovery_policy=MultiLegRecoveryPolicy.FAIL_CLOSED,
        legs=(
            MultiLegCheckpoint(
                leg_id="leg-1",
                order_id=orders[0].order_id,
                state=ExecutionCoordinatorState.OPEN,
                requested_quantity=Decimal("1"),
                filled_quantity=Decimal("1"),
                reduce_only=False,
            ),
            MultiLegCheckpoint(
                leg_id="leg-2",
                order_id=orders[1].order_id,
                state=ExecutionCoordinatorState.PENDING,
                requested_quantity=Decimal("2"),
                filled_quantity=Decimal("0"),
                reduce_only=False,
            ),
        ),
        created_at=NOW,
        updated_at=NOW,
    )
    store.records[(7, plan.plan_id)] = record
    scripts = {
        "leg-1": ScriptedSingleLeg([]),
        "leg-2": ScriptedSingleLeg(
            [(ExecutionCoordinatorState.OPEN, Decimal("2"))]
        ),
    }

    async def scenario():
        coordinator = PairExecutionCoordinator(
            user_id=7,
            state_store=store,
            single_leg_factory=Factory(scripts),
        )
        return await coordinator.execute(plan, orders, now=NOW)

    result = asyncio.run(scenario())
    assert result.state is MultiLegExecutionState.OPEN
    assert scripts["leg-1"].execute_calls == 0
    assert scripts["leg-2"].execute_calls == 1
