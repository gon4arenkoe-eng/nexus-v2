"""Order comparison scope is distinct from fill ownership history."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.application.reconciliation_detector import (
    ReconciliationDetectionError,
    detect_reconciliation,
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
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancyKind,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.venue import (
    VenueFill,
    VenueOrderResult,
    VenueOrderState,
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


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)

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


def local_order(
    *,
    order_id: str,
    venue_order_id: str,
    status: ExecutionOrderStatus,
    filled: Decimal,
    average: Decimal | None,
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
            venue_order_id
        ),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        filled_quantity=filled,
        average_fill_price=average,
        limit_price=None,
        reduce_only=False,
        status=status,
        rejection_reason=None,
        submitted_at=NOW,
        accepted_at=NOW,
        filled_at=(
            NOW
            if status is ExecutionOrderStatus.FILLED
            else None
        ),
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def venue_order(
    *,
    order_id: str,
    venue_order_id: str,
) -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId(
            f"client-{order_id}"
        ),
        venue_order_id=VenueOrderId(
            venue_order_id
        ),
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
    )


def local_fill(
    *,
    order_id: str,
) -> ExecutionFill:
    return ExecutionFill(
        fill_id=FillId(f"fill-{order_id}"),
        order_id=OrderId(order_id),
        venue_fill_id=VenueFillId(
            f"venue-fill-{order_id}"
        ),
        quantity=Decimal("1"),
        price=Decimal("50000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=NOW,
        created_at=NOW,
    )


def venue_fill(
    *,
    order_id: str,
    venue_order_id: str,
) -> VenueFill:
    return VenueFill(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        venue_fill_id=VenueFillId(
            f"venue-fill-{order_id}"
        ),
        venue_order_id=VenueOrderId(
            venue_order_id
        ),
        client_order_id=ClientOrderId(
            f"client-{order_id}"
        ),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("50000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=NOW,
        observed_at=NOW,
    )


def detect(
    *,
    local_orders: tuple[ExecutionOrder, ...],
    venue_orders: tuple[VenueOrderResult, ...],
    local_fills: tuple[ExecutionFill, ...] = (),
    venue_fills: tuple[VenueFill, ...] = (),
    comparison: tuple[ExecutionOrder, ...] | None = None,
):
    return detect_reconciliation(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        local_orders=local_orders,
        venue_orders=venue_orders,
        local_fills=local_fills,
        venue_fills=venue_fills,
        local_positions=(),
        venue_positions=(),
        order_comparison_local_orders=comparison,
    )


def test_default_preserves_legacy_order_comparison_semantics() -> None:
    historical = local_order(
        order_id="old",
        venue_order_id="100",
        status=ExecutionOrderStatus.FILLED,
        filled=Decimal("1"),
        average=Decimal("50000"),
    )

    result = detect(
        local_orders=(historical,),
        venue_orders=(),
    )

    assert result.state is ReconciliationResultState.DISCREPANCY
    assert [
        item.kind
        for item in result.discrepancies
    ] == [
        ReconciliationDiscrepancyKind
        .LOCAL_ORDER_MISSING_ON_VENUE
    ]


def test_explicit_comparison_scope_can_exclude_historical_order() -> None:
    historical = local_order(
        order_id="old",
        venue_order_id="100",
        status=ExecutionOrderStatus.FILLED,
        filled=Decimal("1"),
        average=Decimal("50000"),
    )

    result = detect(
        local_orders=(historical,),
        venue_orders=(),
        comparison=(),
    )

    assert result.state is ReconciliationResultState.MATCHED
    assert result.discrepancies == ()


def test_excluded_historical_order_remains_fill_ownership_source() -> None:
    historical = local_order(
        order_id="old",
        venue_order_id="100",
        status=ExecutionOrderStatus.FILLED,
        filled=Decimal("1"),
        average=Decimal("50000"),
    )

    result = detect(
        local_orders=(historical,),
        venue_orders=(),
        local_fills=(
            local_fill(order_id="old"),
        ),
        venue_fills=(
            venue_fill(
                order_id="old",
                venue_order_id="100",
            ),
        ),
        comparison=(),
    )

    assert result.state is ReconciliationResultState.MATCHED
    assert result.discrepancies == ()


def test_active_order_can_still_be_compared_explicitly() -> None:
    active = local_order(
        order_id="active",
        venue_order_id="200",
        status=ExecutionOrderStatus.ACCEPTED,
        filled=Decimal("0"),
        average=None,
    )

    result = detect(
        local_orders=(active,),
        venue_orders=(
            venue_order(
                order_id="active",
                venue_order_id="200",
            ),
        ),
        comparison=(active,),
    )

    assert result.state is ReconciliationResultState.MATCHED


def test_comparison_scope_must_be_subset_of_local_orders() -> None:
    local = local_order(
        order_id="local",
        venue_order_id="300",
        status=ExecutionOrderStatus.ACCEPTED,
        filled=Decimal("0"),
        average=None,
    )

    foreign = local_order(
        order_id="foreign",
        venue_order_id="400",
        status=ExecutionOrderStatus.ACCEPTED,
        filled=Decimal("0"),
        average=None,
    )

    with pytest.raises(
        ReconciliationDetectionError,
        match="subset of local_orders",
    ):
        detect(
            local_orders=(local,),
            venue_orders=(),
            comparison=(foreign,),
        )


def test_comparison_scope_requires_tuple() -> None:
    local = local_order(
        order_id="local",
        venue_order_id="300",
        status=ExecutionOrderStatus.ACCEPTED,
        filled=Decimal("0"),
        average=None,
    )

    with pytest.raises(
        ReconciliationDetectionError,
        match="must be a tuple",
    ):
        detect_reconciliation(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=NOW,
            local_orders=(local,),
            venue_orders=(),
            local_fills=(),
            venue_fills=(),
            local_positions=(),
            venue_positions=(),
            order_comparison_local_orders=[local],  # type: ignore[arg-type]
        )
