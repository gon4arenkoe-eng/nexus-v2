"""Restart persistence and multi-user isolation tests for Grid Trading Desk."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.core.application.grid_trading import build_grid_levels
from apps.core.domain.grid_trading import (
    GridBias,
    GridConfiguration,
    GridCycle,
    GridCycleState,
    GridInstance,
    GridInstanceState,
    GridRiskBudget,
    GridSpacingType,
    GridStuckPositionPolicy,
)
from infra.persistence.application.grid_trading import SqlAlchemyGridInstanceStore  # noqa: E501
from infra.persistence.base import PersistenceBase
from infra.persistence.models.grid_trading import GridInstanceStateModel
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)

NOW = datetime(2026, 9, 12, 19, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BINANCE"), 7)
INSTRUMENT = InstrumentId(
    VenueId("BINANCE"),
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


def _instance(*, user_id: int = 7, instance_id: str = "grid-1") -> GridInstance:  # noqa: E501
    config = GridConfiguration(
        lower_price=Decimal("90"),
        upper_price=Decimal("110"),
        center_price=Decimal("100"),
        spacing_type=GridSpacingType.ARITHMETIC,
        levels_per_side=2,
        order_quantity=Decimal("1"),
        dynamic_step_ratio=Decimal("0.02"),
        bias=GridBias.NEUTRAL,
        recenter_threshold_ratio=Decimal("0.05"),
        maker_fee_rate=Decimal("0.001"),
        taker_fee_rate=Decimal("0.002"),
        max_slippage_bps=Decimal("25"),
        allowed_regimes=("SIDEWAYS", "TREND_UP"),
    )
    risk = GridRiskBudget(
        reserved_capital=Decimal("1000"),
        max_gross_exposure=Decimal("2000"),
        max_inventory_notional=Decimal("500"),
        max_drawdown_ratio=Decimal("0.1"),
        max_stuck_seconds=3600,
        stuck_policy=GridStuckPositionPolicy.HALT,
    )
    cycle = GridCycle(
        cycle_id=f"{instance_id}:1",
        sequence=1,
        state=GridCycleState.RECOVERY,
        center_price=Decimal("100"),
        levels=build_grid_levels(config),
        opened_at=NOW,
    )
    return GridInstance(
        instance_id=instance_id,
        program_id=f"program-{user_id}",
        user_id=user_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        state=GridInstanceState.RECOVERY,
        config=config,
        risk_budget=risk,
        cycle=cycle,
        inventory_quantity=Decimal("1"),
        created_at=NOW,
        updated_at=NOW,
    )


def test_grid_state_survives_fresh_session() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(GridInstanceStateModel.__table__,),
            )
        async with factory() as session:
            store = SqlAlchemyGridInstanceStore(session)
            await store.checkpoint(_instance())
            await session.commit()
        async with factory() as session:
            restored = await SqlAlchemyGridInstanceStore(session).load(
                user_id=7,
                instance_id="grid-1",
            )
        await engine.dispose()
        return restored

    restored = asyncio.run(scenario())
    assert restored is not None
    assert restored.state is GridInstanceState.RECOVERY
    assert restored.cycle.state is GridCycleState.RECOVERY
    assert restored.inventory_quantity == Decimal("1")
    assert restored.updated_at.tzinfo is not None


def test_grid_state_store_is_user_scoped() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)  # noqa: E501
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all,
                tables=(GridInstanceStateModel.__table__,),
            )
        async with factory() as session:
            store = SqlAlchemyGridInstanceStore(session)
            await store.checkpoint(_instance(user_id=7, instance_id="grid-a"))
            await store.checkpoint(_instance(user_id=8, instance_id="grid-b"))
            await session.commit()
        async with factory() as session:
            store = SqlAlchemyGridInstanceStore(session)
            user7 = await store.list_for_user(user_id=7)
            hidden = await store.load(user_id=7, instance_id="grid-b")
        await engine.dispose()
        return user7, hidden

    user7, hidden = asyncio.run(scenario())
    assert [item.instance_id for item in user7] == ["grid-a"]
    assert hidden is None


def test_grid_state_model_is_registered() -> None:
    assert "grid_instance_states" in PersistenceBase.metadata.tables


def test_grid_state_model_has_user_guard() -> None:
    checks = {
        str(constraint.sqltext)
        for constraint in GridInstanceStateModel.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "user_id > 0" in checks
