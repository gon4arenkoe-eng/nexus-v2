from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.domain.execution import (
    ExecutionLegPlan,
    ExecutionPlan,
)
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.domain.positions import (
    PositionGroup,
    PositionGroupStatus,
    PositionLeg,
    PositionLegStatus,
)
from infra.persistence.application.core_execution import (
    CoreExecutionPersistenceService,
)
from infra.persistence.models.execution import (
    ExecutionPlanLegModel,
    ExecutionPlanModel,
)
from infra.persistence.models.execution_orders import (
    ExecutionOrderModel,
)
from infra.persistence.models.positions import (
    PositionGroupModel,
    PositionLegModel,
)
from infra.persistence.repositories.core_execution import (
    CoreExecutionPersistenceRepository,
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


NOW = datetime(2026, 9, 21, 15, 0, tzinfo=UTC)
VENUE = VenueId("SIM")
ACCOUNT = AccountId(VENUE, 1)
INSTRUMENT = InstrumentId(
    VENUE,
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    def __init__(self, *, fail_flush: bool = False) -> None:
        self.by_type: dict[type, object] = {}
        self.added: list[object] = []
        self.flushes = 0
        self.commits = 0
        self.rollbacks = 0
        self.fail_flush = fail_flush

    async def execute(self, statement):
        entity = statement.column_descriptions[0]["entity"]
        return FakeResult(self.by_type.get(entity))

    def add(self, model) -> None:
        self.added.append(model)
        self.by_type[type(model)] = model

    async def flush(self) -> None:
        self.flushes += 1
        if self.fail_flush:
            raise RuntimeError("simulated persistence failure")

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class SessionContext:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeFactory:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def __call__(self):
        return SessionContext(self.session)


def make_graph():
    planned_leg = ExecutionLegPlan(
        leg_id="leg-1",
        order_id=OrderId("order-1"),
        client_order_id=ClientOrderId("client-1"),
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=TradeSide.BUY,
        quantity=Decimal("0.001"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
        reduce_only=False,
    )

    plan = ExecutionPlan(
        plan_id="plan-1",
        intent_id="intent-1",
        user_id=1,
        shape=TradeIntentShape.SINGLE_LEG,
        strategy="phase14-persistence",
        strategy_version="1",
        source="SHADOW",
        legs=(planned_leg,),
        created_at=NOW,
    )

    group = PositionGroup(
        group_id="group-1",
        plan_id=plan.plan_id,
        user_id=plan.user_id,
        shape=plan.shape,
        strategy=plan.strategy,
        strategy_version=plan.strategy_version,
        trade_source=plan.source,
        status=PositionGroupStatus.PENDING,
        opened_at=None,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    position_leg = PositionLeg(
        group_id=group.group_id,
        leg_id=planned_leg.leg_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=TradeSide.BUY,
        target_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
        current_quantity=Decimal("0"),
        average_entry_price=None,
        average_exit_price=None,
        status=PositionLegStatus.PENDING,
        opened_at=None,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    order = ExecutionOrder(
        order_id=planned_leg.order_id,
        plan_id=plan.plan_id,
        group_id=group.group_id,
        leg_id=planned_leg.leg_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=planned_leg.client_order_id,
        venue_order_id=None,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=Decimal("100"),
        reduce_only=False,
        status=ExecutionOrderStatus.PENDING,
        rejection_reason=None,
        submitted_at=None,
        accepted_at=None,
        filled_at=None,
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    return plan, group, (position_leg,), order


def test_repository_persists_fk_graph_in_canonical_order() -> None:
    plan, group, legs, order = make_graph()
    session = FakeSession()

    asyncio.run(
        CoreExecutionPersistenceRepository(session).persist_root(
            plan=plan,
            group=group,
            position_legs=legs,
            order=order,
            recorded_at=NOW,
        )
    )

    assert [type(item) for item in session.added] == [
        ExecutionPlanModel,
        ExecutionPlanLegModel,
        PositionGroupModel,
        PositionLegModel,
        ExecutionOrderModel,
    ]
    assert session.flushes == 5


def test_repository_repeat_is_idempotent_for_same_graph() -> None:
    plan, group, legs, order = make_graph()
    session = FakeSession()
    repository = CoreExecutionPersistenceRepository(session)

    asyncio.run(
        repository.persist_root(
            plan=plan,
            group=group,
            position_legs=legs,
            order=order,
            recorded_at=NOW,
        )
    )
    first_added = len(session.added)

    asyncio.run(
        repository.persist_root(
            plan=plan,
            group=group,
            position_legs=legs,
            order=order,
            recorded_at=NOW,
        )
    )

    assert first_added == 5
    assert len(session.added) == 5


def test_service_rolls_back_transaction_on_persistence_failure() -> None:
    plan, group, legs, order = make_graph()
    session = FakeSession(fail_flush=True)
    service = CoreExecutionPersistenceService(FakeFactory(session))

    with pytest.raises(
        RuntimeError,
        match="simulated persistence failure",
    ):
        asyncio.run(
            service.persist_root(
                plan=plan,
                group=group,
                position_legs=legs,
                order=order,
                recorded_at=NOW,
            )
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_service_commits_exactly_once() -> None:
    plan, group, legs, order = make_graph()
    session = FakeSession()
    service = CoreExecutionPersistenceService(FakeFactory(session))

    asyncio.run(
        service.persist_root(
            plan=plan,
            group=group,
            position_legs=legs,
            order=order,
            recorded_at=NOW,
        )
    )

    assert session.commits == 1
    assert session.rollbacks == 0


def test_service_rejects_mismatched_graph_before_database_write() -> None:
    plan, group, legs, order = make_graph()

    bad_group = PositionGroup(
        group_id=group.group_id,
        plan_id="wrong-plan",
        user_id=group.user_id,
        shape=group.shape,
        strategy=group.strategy,
        strategy_version=group.strategy_version,
        trade_source=group.trade_source,
        status=group.status,
        opened_at=group.opened_at,
        closed_at=group.closed_at,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )

    session = FakeSession()
    service = CoreExecutionPersistenceService(FakeFactory(session))

    with pytest.raises(
        ValueError,
        match="plan_id must match",
    ):
        asyncio.run(
            service.persist_root(
                plan=plan,
                group=bad_group,
                position_legs=legs,
                order=order,
                recorded_at=NOW,
            )
        )

    assert session.added == []
    assert session.commits == 0
