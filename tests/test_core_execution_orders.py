from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.orders import OrderSide, OrderType
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


CREATED = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 5, 12, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 5, 12, 2, tzinfo=timezone.utc)
T3 = datetime(2026, 9, 5, 12, 3, tzinfo=timezone.utc)


def _identity(
    venue: str = "BINGX",
) -> tuple[AccountId, InstrumentId]:
    venue_id = VenueId(venue)

    return (
        AccountId(
            venue_id=venue_id,
            value=1,
        ),
        InstrumentId(
            venue_id=venue_id,
            native_symbol="BTC-USDT",
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        ),
    )


def _order(
    *,
    status: ExecutionOrderStatus = ExecutionOrderStatus.PENDING,
    order_type: OrderType = OrderType.MARKET,
    requested_quantity: Decimal = Decimal("1"),
    filled_quantity: Decimal = Decimal("0"),
    average_fill_price: Decimal | None = None,
    limit_price: Decimal | None = None,
    rejection_reason: str | None = None,
    submitted_at: datetime | None = None,
    accepted_at: datetime | None = None,
    filled_at: datetime | None = None,
    cancelled_at: datetime | None = None,
) -> ExecutionOrder:
    account_id, instrument_id = _identity()

    return ExecutionOrder(
        order_id="order-1",
        plan_id="plan-1",
        leg_id="leg-1",
        account_id=account_id,
        instrument_id=instrument_id,
        client_order_id="client-1",
        venue_order_id=None,
        side=OrderSide.BUY,
        order_type=order_type,
        requested_quantity=requested_quantity,
        filled_quantity=filled_quantity,
        average_fill_price=average_fill_price,
        limit_price=limit_price,
        reduce_only=False,
        status=status,
        rejection_reason=rejection_reason,
        submitted_at=submitted_at,
        accepted_at=accepted_at,
        filled_at=filled_at,
        cancelled_at=cancelled_at,
        created_at=CREATED,
        updated_at=T3,
    )


def test_pending_order_is_valid_zero_projection() -> None:
    order = _order()

    assert order.status is ExecutionOrderStatus.PENDING
    assert order.filled_quantity == Decimal("0")
    assert order.average_fill_price is None


def test_market_order_rejects_limit_price() -> None:
    with pytest.raises(ValueError):
        _order(limit_price=Decimal("100"))


def test_limit_order_requires_positive_limit_price() -> None:
    order = _order(
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
    )

    assert order.limit_price == Decimal("100")

    with pytest.raises(ValueError):
        _order(order_type=OrderType.LIMIT)


def test_partial_fill_requires_strict_partial_quantity() -> None:
    order = _order(
        status=ExecutionOrderStatus.PARTIALLY_FILLED,
        filled_quantity=Decimal("0.4"),
        average_fill_price=Decimal("100"),
        submitted_at=T1,
        accepted_at=T2,
    )

    assert order.filled_quantity == Decimal("0.4")

    with pytest.raises(ValueError):
        _order(
            status=ExecutionOrderStatus.PARTIALLY_FILLED,
            filled_quantity=Decimal("1"),
            average_fill_price=Decimal("100"),
        )


def test_filled_requires_full_requested_quantity() -> None:
    order = _order(
        status=ExecutionOrderStatus.FILLED,
        filled_quantity=Decimal("1"),
        average_fill_price=Decimal("100"),
        submitted_at=T1,
        accepted_at=T2,
        filled_at=T3,
    )

    assert order.status is ExecutionOrderStatus.FILLED

    with pytest.raises(ValueError):
        _order(
            status=ExecutionOrderStatus.FILLED,
            filled_quantity=Decimal("0.9"),
            average_fill_price=Decimal("100"),
        )


def test_cancelled_order_may_preserve_partial_fill_projection() -> None:
    order = _order(
        status=ExecutionOrderStatus.CANCELLED,
        filled_quantity=Decimal("0.4"),
        average_fill_price=Decimal("100"),
        submitted_at=T1,
        cancelled_at=T3,
    )

    assert order.filled_quantity == Decimal("0.4")
    assert order.cancelled_at == T3


def test_rejected_order_requires_reason() -> None:
    order = _order(
        status=ExecutionOrderStatus.REJECTED,
        rejection_reason="insufficient margin",
        submitted_at=T1,
    )

    assert order.rejection_reason == "insufficient margin"

    with pytest.raises(ValueError):
        _order(status=ExecutionOrderStatus.REJECTED)


def test_unknown_order_allows_recovery_projection() -> None:
    order = _order(
        status=ExecutionOrderStatus.UNKNOWN,
        filled_quantity=Decimal("0.4"),
        average_fill_price=Decimal("100"),
        submitted_at=T1,
    )

    assert order.status is ExecutionOrderStatus.UNKNOWN


def test_order_rejects_filled_quantity_above_requested() -> None:
    with pytest.raises(ValueError):
        _order(
            status=ExecutionOrderStatus.UNKNOWN,
            filled_quantity=Decimal("1.1"),
            average_fill_price=Decimal("100"),
        )


def test_order_rejects_account_instrument_venue_mismatch() -> None:
    account_id, _ = _identity("BINGX")
    _, instrument_id = _identity("BINANCE")

    with pytest.raises(ValueError):
        ExecutionOrder(
            order_id="order-1",
            plan_id="plan-1",
            leg_id="leg-1",
            account_id=account_id,
            instrument_id=instrument_id,
            client_order_id="client-1",
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
            created_at=CREATED,
            updated_at=CREATED,
        )


def test_order_timestamps_normalize_to_utc() -> None:
    plus_three = timezone(timedelta(hours=3))
    account_id, instrument_id = _identity()

    order = ExecutionOrder(
        order_id="order-1",
        plan_id="plan-1",
        leg_id="leg-1",
        account_id=account_id,
        instrument_id=instrument_id,
        client_order_id="client-1",
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
        created_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            tzinfo=plus_three,
        ),
        updated_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            tzinfo=plus_three,
        ),
    )

    assert order.created_at == CREATED


def test_execution_fill_is_valid_immutable_evidence() -> None:
    fill = ExecutionFill(
        fill_id="fill-1",
        order_id="order-1",
        venue_fill_id="venue-fill-1",
        quantity=Decimal("0.4"),
        price=Decimal("100"),
        fee=Decimal("0.01"),
        fee_currency="USDT",
        executed_at=T1,
        created_at=T2,
    )

    assert fill.quantity == Decimal("0.4")

    with pytest.raises(FrozenInstanceError):
        fill.quantity = Decimal("1")  # type: ignore[misc]


def test_execution_fill_allows_missing_venue_fill_id() -> None:
    fill = ExecutionFill(
        fill_id="deterministic-fill-1",
        order_id="order-1",
        venue_fill_id=None,
        quantity=Decimal("0.4"),
        price=Decimal("100"),
        fee=Decimal("0"),
        fee_currency=None,
        executed_at=T1,
        created_at=T2,
    )

    assert fill.venue_fill_id is None


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_fill_quantity_must_be_positive_finite(
    quantity: Decimal,
) -> None:
    with pytest.raises(ValueError):
        ExecutionFill(
            fill_id="fill-1",
            order_id="order-1",
            venue_fill_id=None,
            quantity=quantity,
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_currency=None,
            executed_at=T1,
            created_at=T2,
        )


def test_positive_fee_requires_currency() -> None:
    with pytest.raises(ValueError):
        ExecutionFill(
            fill_id="fill-1",
            order_id="order-1",
            venue_fill_id=None,
            quantity=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0.1"),
            fee_currency=None,
            executed_at=T1,
            created_at=T2,
        )


def test_fill_created_at_cannot_precede_execution() -> None:
    with pytest.raises(ValueError):
        ExecutionFill(
            fill_id="fill-1",
            order_id="order-1",
            venue_fill_id=None,
            quantity=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_currency=None,
            executed_at=T2,
            created_at=T1,
        )


def test_execution_order_is_immutable() -> None:
    order = _order()

    with pytest.raises(FrozenInstanceError):
        order.status = ExecutionOrderStatus.FILLED  # type: ignore[misc]
