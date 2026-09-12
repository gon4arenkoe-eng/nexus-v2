"""Restart persistence tests for Execution Coordinator state."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from apps.core.application.execution_coordinator import (
    SingleLegExecutionCoordinator,
)
from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.venue import (
    VenueOrderResult,
    VenueOrderState,
)
from infra.persistence.application.execution_coordinator import (
    SqlAlchemyExecutionCoordinatorStateStore,
)
from infra.persistence.base import PersistenceBase
from infra.persistence.models.execution_coordinator import (
    ExecutionCoordinatorStateModel,
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


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BINANCE"), 7)
INSTRUMENT = InstrumentId(
    VenueId("BINANCE"),
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


def make_order() -> ExecutionOrder:
    return ExecutionOrder(
        order_id=OrderId("order-persist-1"),
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=ClientOrderId("client-persist-1"),
        venue_order_id=None,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=None,
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


class Venue:
    @property
    def capabilities(self):
        return frozenset()

    async def submit_order(self, request):
        return VenueOrderResult(
            client_order_id=request.client_order_id,
            venue_order_id=None,
            state=VenueOrderState.ACCEPTED,
            requested_quantity=request.quantity,
            filled_quantity=Decimal("0"),
        )

    async def cancel_order(self, **kwargs):
        raise NotImplementedError

    async def get_order(self, **kwargs):
        raise NotImplementedError

    async def get_open_orders(self, **kwargs):
        return ()

    async def get_positions(self, **kwargs):
        return ()

    async def get_account_state(self, **kwargs):
        raise NotImplementedError

    async def get_fills(self, **kwargs):
        return ()


def test_coordinator_state_survives_fresh_session() -> None:
    async def scenario():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            future=True,
        )
        factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(ExecutionCoordinatorStateModel.__table__,),
            )

        store = SqlAlchemyExecutionCoordinatorStateStore(
            factory
        )
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=Venue(),
            state_store=store,
        )

        await coordinator.execute(
            make_order(),
            now=NOW,
        )

        # Fresh coordinator instance, same persistent database/session factory.
        restored_store = SqlAlchemyExecutionCoordinatorStateStore(
            factory
        )
        restored = await restored_store.load(
            user_id=7,
            order_id=OrderId("order-persist-1"),
        )

        await engine.dispose()

        return restored

    restored = asyncio.run(scenario())

    assert restored is not None
    assert restored.state is ExecutionCoordinatorState.OPENING
    assert restored.attempt == 1
    assert restored.client_order_id == ClientOrderId(
        "client-persist-1"
    )


def test_execution_coordinator_state_model_has_database_guards() -> None:
    checks = {
        str(constraint.sqltext)
        for constraint in ExecutionCoordinatorStateModel.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }

    assert "user_id > 0" in checks
    assert "account_value > 0" in checks
    assert "attempt >= 0" in checks


def test_execution_coordinator_state_model_is_registered() -> None:
    assert "execution_coordinator_states" in (
        PersistenceBase.metadata.tables
    )


def test_execution_coordinator_state_model_preserves_order_ownership() -> None:
    foreign_keys = (
        ExecutionCoordinatorStateModel.__table__
        .c.order_id
        .foreign_keys
    )

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == (
        "execution_orders.order_id"
    )
    assert foreign_key.ondelete == "RESTRICT"
