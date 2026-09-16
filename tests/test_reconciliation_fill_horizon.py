"""Tests for canonical reconciliation fill-history horizon."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.application.reconciliation_fill_horizon import (
    ReconciliationFillHorizonState,
    derive_reconciliation_fill_horizon,
)
from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.orders import (
    OrderSide,
    OrderType,
)
from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshot,
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
ACCOUNT = AccountId(
    venue_id=VENUE,
    value=7,
)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def order(
    *,
    order_id: str = "order-1",
    created_at: datetime = T1,
) -> ExecutionOrder:
    return ExecutionOrder(
        order_id=OrderId(order_id),
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=ClientOrderId(
            f"client-{order_id}"
        ),
        venue_order_id=VenueOrderId(
            f"venue-{order_id}"
        ),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=None,
        reduce_only=False,
        status=ExecutionOrderStatus.ACCEPTED,
        rejection_reason=None,
        submitted_at=created_at,
        accepted_at=created_at,
        filled_at=None,
        cancelled_at=None,
        created_at=created_at,
        updated_at=created_at,
    )


def fill(
    *,
    order_id: str = "order-1",
    executed_at: datetime = T2,
) -> ExecutionFill:
    return ExecutionFill(
        fill_id=FillId(
            f"fill-{order_id}"
        ),
        order_id=OrderId(order_id),
        venue_fill_id=VenueFillId(
            f"venue-fill-{order_id}"
        ),
        quantity=Decimal("0.25"),
        price=Decimal("50000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=executed_at,
        created_at=executed_at,
    )


def snapshot(
    *,
    orders: tuple[ExecutionOrder, ...] = (),
    fills: tuple[ExecutionFill, ...] = (),
) -> LocalReconciliationSnapshot:
    return LocalReconciliationSnapshot(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        orders=orders,
        fills=fills,
        positions=(),
    )


def test_empty_local_history_is_unknown() -> None:
    horizon = derive_reconciliation_fill_horizon(
        snapshot()
    )

    assert (
        horizon.state
        is ReconciliationFillHorizonState.UNKNOWN
    )
    assert horizon.since is None


def test_order_without_local_fill_bounds_venue_query() -> None:
    horizon = derive_reconciliation_fill_horizon(
        snapshot(
            orders=(
                order(created_at=T1),
            ),
        )
    )

    assert (
        horizon.state
        is ReconciliationFillHorizonState.BOUNDED
    )
    assert horizon.since == T1


def test_earlier_order_dominates_later_fill() -> None:
    horizon = derive_reconciliation_fill_horizon(
        snapshot(
            orders=(
                order(created_at=T0),
            ),
            fills=(
                fill(executed_at=T2),
            ),
        )
    )

    assert horizon.since == T0


def test_earlier_fill_dominates_later_order() -> None:
    local_order = order(created_at=T2)

    local_fill = fill(
        executed_at=T1,
    )

    # ExecutionFill only requires ownership identity;
    # snapshot supplies owning order in the same scope.
    horizon = derive_reconciliation_fill_horizon(
        snapshot(
            orders=(local_order,),
            fills=(local_fill,),
        )
    )

    assert horizon.since == T1


def test_multiple_orders_choose_earliest_creation() -> None:
    first = order(
        order_id="order-1",
        created_at=T0,
    )
    second = order(
        order_id="order-2",
        created_at=T2,
    )

    horizon = derive_reconciliation_fill_horizon(
        snapshot(
            orders=(second, first),
        )
    )

    assert horizon.since == T0


def test_rejects_non_snapshot_value() -> None:
    with pytest.raises(
        ValueError,
        match="LocalReconciliationSnapshot",
    ):
        derive_reconciliation_fill_horizon(
            object()  # type: ignore[arg-type]
        )
