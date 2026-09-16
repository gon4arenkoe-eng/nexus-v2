"""Phase 13 local reconciliation snapshot provider tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
    ExecutionOrderStatus,
    OrderSide,
    OrderType,
)
from apps.core.domain.positions import (
    PositionLeg,
    PositionLegStatus,
    TradeSide,
)
from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshot,
)
from infra.persistence.repositories.reconciliation_snapshot import (
    LocalReconciliationSnapshotRepository,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    FillId,
    InstrumentId,
    InstrumentType,
    OrderId,
    VenueFillId,
    VenueId,
    VenueOrderId,
)


VENUE = VenueId("BYBIT")
ACCOUNT = AccountId(venue_id=VENUE, value=7)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
NAIVE_NOW = datetime(2026, 9, 16, 12, 0)


def _order_model(**overrides):
    values = dict(
        id=1,
        order_id="order-1",
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        user_id=11,
        venue_id="BYBIT",
        account_value=7,
        instrument_venue_id="BYBIT",
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL.value,
        asset_class=AssetClass.CRYPTO.value,
        client_order_id="client-1",
        venue_order_id="venue-order-1",
        side=OrderSide.BUY.value,
        order_type=OrderType.MARKET.value,
        reduce_only=False,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=None,
        local_status=ExecutionOrderStatus.ACCEPTED.value,
        rejection_reason=None,
        submitted_at=NAIVE_NOW,
        accepted_at=NAIVE_NOW,
        filled_at=None,
        cancelled_at=None,
        created_at=NAIVE_NOW,
        updated_at=NAIVE_NOW,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _fill_model(**overrides):
    values = dict(
        id=1,
        fill_id="fill-1",
        order_id="order-1",
        user_id=11,
        venue_id="BYBIT",
        account_value=7,
        venue_fill_id="venue-fill-1",
        quantity=Decimal("0.25"),
        price=Decimal("50000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=NAIVE_NOW,
        received_at=NAIVE_NOW,
        created_at=NAIVE_NOW,
        source="test",
        raw_evidence_hash=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _position_model(**overrides):
    values = dict(
        id=1,
        group_id="group-1",
        leg_id="leg-1",
        venue_id="BYBIT",
        account_value=7,
        instrument_venue_id="BYBIT",
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL.value,
        asset_class=AssetClass.CRYPTO.value,
        side=TradeSide.BUY.value,
        target_quantity=Decimal("1"),
        filled_quantity=Decimal("1"),
        current_quantity=Decimal("1"),
        average_entry_price=Decimal("50000"),
        average_exit_price=None,
        status=PositionLegStatus.OPEN.value,
        opened_at=NAIVE_NOW,
        closed_at=None,
        created_at=NAIVE_NOW,
        updated_at=NAIVE_NOW,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _order() -> ExecutionOrder:
    return LocalReconciliationSnapshotRepository._to_order(
        _order_model()
    )


def _fill() -> ExecutionFill:
    return LocalReconciliationSnapshotRepository._to_fill(
        _fill_model()
    )


def _position() -> PositionLeg:
    return LocalReconciliationSnapshotRepository._to_position(
        _position_model()
    )


def _sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_order_query_is_explicitly_user_account_instrument_scoped() -> None:
    text = _sql(
        LocalReconciliationSnapshotRepository._order_statement(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
    )

    assert "execution_orders.user_id = 11" in text
    assert "execution_orders.venue_id = 'BYBIT'" in text
    assert "execution_orders.account_value = 7" in text
    assert "execution_orders.native_symbol = 'BTCUSDT'" in text
    assert "execution_orders.instrument_type" in text
    assert "execution_orders.asset_class" in text
    assert "ORDER BY execution_orders.created_at ASC" in text
    assert "execution_orders.order_id ASC" in text


def test_fill_query_uses_owning_order_for_instrument_scope() -> None:
    text = _sql(
        LocalReconciliationSnapshotRepository._fill_statement(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
    )

    assert "JOIN execution_orders" in text
    assert "execution_fills.user_id = 11" in text
    assert "execution_orders.user_id = 11" in text
    assert "execution_fills.account_value = 7" in text
    assert "execution_orders.account_value = 7" in text
    assert "execution_orders.native_symbol = 'BTCUSDT'" in text
    assert "ORDER BY execution_fills.executed_at ASC" in text
    assert "execution_fills.fill_id ASC" in text


def test_position_query_joins_group_for_user_ownership() -> None:
    text = _sql(
        LocalReconciliationSnapshotRepository._position_statement(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
    )

    assert "JOIN position_groups" in text
    assert "position_groups.user_id = 11" in text
    assert "position_legs.account_value = 7" in text
    assert "position_legs.native_symbol = 'BTCUSDT'" in text
    assert "ORDER BY position_legs.created_at ASC" in text
    assert "position_legs.group_id ASC" in text
    assert "position_legs.leg_id ASC" in text


def test_order_hydration_restores_typed_identity_and_utc() -> None:
    order = _order()

    assert order.order_id == OrderId("order-1")
    assert order.client_order_id == ClientOrderId("client-1")
    assert order.venue_order_id == VenueOrderId("venue-order-1")
    assert order.account_id == ACCOUNT
    assert order.instrument_id == INSTRUMENT
    assert order.side is OrderSide.BUY
    assert order.status is ExecutionOrderStatus.ACCEPTED
    assert order.created_at.tzinfo is UTC
    assert order.updated_at.tzinfo is UTC


def test_fill_hydration_restores_identity_and_utc() -> None:
    fill = _fill()

    assert fill.fill_id == FillId("fill-1")
    assert fill.order_id == OrderId("order-1")
    assert fill.venue_fill_id == VenueFillId("venue-fill-1")
    assert fill.executed_at.tzinfo is UTC
    assert fill.created_at.tzinfo is UTC


def test_position_hydration_restores_scope_and_utc() -> None:
    position = _position()

    assert position.account_id == ACCOUNT
    assert position.instrument_id == INSTRUMENT
    assert position.side is TradeSide.BUY
    assert position.status is PositionLegStatus.OPEN
    assert position.opened_at is not None
    assert position.opened_at.tzinfo is UTC
    assert position.created_at.tzinfo is UTC


def test_snapshot_requires_fill_owning_order_in_same_scope() -> None:
    with pytest.raises(
        ValueError,
        match="no owning order",
    ):
        LocalReconciliationSnapshot(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            orders=(),
            fills=(_fill(),),
            positions=(),
        )


def test_snapshot_rejects_cross_account_position() -> None:
    other = LocalReconciliationSnapshotRepository._to_position(
        _position_model(account_value=8)
    )

    with pytest.raises(
        ValueError,
        match="position account outside snapshot scope",
    ):
        LocalReconciliationSnapshot(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            orders=(),
            fills=(),
            positions=(other,),
        )


class _Scalars:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _Result:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return _Scalars(self._values)


class _Session:
    def __init__(self):
        self.calls = 0

    async def execute(self, statement):
        self.calls += 1

        if self.calls == 1:
            return _Result((_order_model(),))

        if self.calls == 2:
            return _Result((_fill_model(),))

        if self.calls == 3:
            return _Result((_position_model(),))

        raise AssertionError("unexpected query")


def test_repository_load_returns_complete_canonical_snapshot() -> None:
    async def scenario():
        session = _Session()
        repository = LocalReconciliationSnapshotRepository(session)  # type: ignore[arg-type]
        snapshot = await repository.load(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
        return session, snapshot

    session, snapshot = asyncio.run(scenario())

    assert session.calls == 3
    assert snapshot.user_id == 11
    assert snapshot.account_id == ACCOUNT
    assert snapshot.instrument_id == INSTRUMENT
    assert len(snapshot.orders) == 1
    assert len(snapshot.fills) == 1
    assert len(snapshot.positions) == 1
    assert snapshot.fills[0].order_id == snapshot.orders[0].order_id


def test_scope_rejects_account_instrument_venue_mismatch() -> None:
    other = InstrumentId(
        venue_id=VenueId("BINANCE"),
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    with pytest.raises(
        ValueError,
        match="account venue must match instrument venue",
    ):
        LocalReconciliationSnapshotRepository._validate_scope(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=other,
        )
