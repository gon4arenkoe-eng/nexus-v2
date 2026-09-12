"""Persistence tests for Phase 5 multi-leg execution state."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
from infra.persistence.application.multi_leg_execution import (
    SqlAlchemyMultiLegExecutionStateStore,
)
from infra.persistence.base import PersistenceBase
from infra.persistence.models import MultiLegExecutionStateModel
from packages.contracts.identities import OrderId


NOW = datetime(2026, 9, 12, 13, 0, tzinfo=UTC)


def make_record() -> MultiLegExecutionStateRecord:
    return MultiLegExecutionStateRecord(
        user_id=7,
        plan_id="plan-pair-1",
        group_id="group-1",
        shape=TradeIntentShape.PAIR,
        state=MultiLegExecutionState.RECOVERY,
        recovery_policy=MultiLegRecoveryPolicy.FAIL_CLOSED,
        legs=(
            MultiLegCheckpoint(
                leg_id="leg-1",
                order_id=OrderId("order-1"),
                state=ExecutionCoordinatorState.OPEN,
                requested_quantity=Decimal("1"),
                filled_quantity=Decimal("1"),
                reduce_only=False,
            ),
            MultiLegCheckpoint(
                leg_id="leg-2",
                order_id=OrderId("order-2"),
                state=ExecutionCoordinatorState.RECOVERY,
                requested_quantity=Decimal("2"),
                filled_quantity=Decimal("0"),
                reduce_only=False,
            ),
        ),
        created_at=NOW,
        updated_at=NOW,
    )


def test_multi_leg_table_registered() -> None:
    assert (
        MultiLegExecutionStateModel.__tablename__
        == "multi_leg_execution_states"
    )
    assert "multi_leg_execution_states" in PersistenceBase.metadata.tables


def test_multi_leg_state_survives_fresh_session() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(PersistenceBase.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            store = SqlAlchemyMultiLegExecutionStateStore(session)
            await store.checkpoint(make_record())
            await session.commit()
        async with session_factory() as session:
            store = SqlAlchemyMultiLegExecutionStateStore(session)
            restored = await store.load(
                user_id=7,
                plan_id="plan-pair-1",
            )
        await engine.dispose()
        return restored
    restored = asyncio.run(scenario())
    assert restored == make_record()
    assert restored.updated_at.tzinfo is not None


def test_state_record_rejects_single_leg_shape() -> None:
    with pytest.raises(ValueError, match="SINGLE_LEG"):
        MultiLegExecutionStateRecord(
            user_id=7,
            plan_id="plan-1",
            group_id="group-1",
            shape=TradeIntentShape.SINGLE_LEG,
            state=MultiLegExecutionState.OPEN,
            recovery_policy=MultiLegRecoveryPolicy.FAIL_CLOSED,
            legs=make_record().legs,
            created_at=NOW,
            updated_at=NOW,
        )


def test_multi_leg_model_preserves_plan_and_group_ownership() -> None:
    table = MultiLegExecutionStateModel.__table__
    plan_fk = next(iter(table.c.plan_id.foreign_keys))
    group_fk = next(iter(table.c.group_id.foreign_keys))
    assert plan_fk.target_fullname == "execution_plans.plan_id"
    assert group_fk.target_fullname == "position_groups.group_id"
    assert plan_fk.ondelete == "RESTRICT"
    assert group_fk.ondelete == "RESTRICT"


def test_multi_leg_model_has_positive_user_guard() -> None:
    checks = {
        str(constraint.sqltext)
        for constraint in MultiLegExecutionStateModel.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "user_id > 0" in checks
