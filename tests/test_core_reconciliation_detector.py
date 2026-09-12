"""Tests for deterministic Phase 3 reconciliation detection."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import inspect

from apps.core.application.reconciliation_detector import (
    detect_reconciliation,
    position_side_for_leg,
)
from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.intents import TradeSide
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.domain.positions import (
    PositionLeg,
    PositionLegStatus,
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
    VenuePosition,
    VenuePositionSide,
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


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
VENUE = VenueId("BINANCE")
ACCOUNT = AccountId(venue_id=VENUE, value=7)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _local_order(
    *,
    order_id: str = "order-1",
    client_id: str = "client-1",
    venue_order_id: str = "venue-order-1",
    status: ExecutionOrderStatus = ExecutionOrderStatus.ACCEPTED,
) -> ExecutionOrder:
    return ExecutionOrder(
        order_id=OrderId(order_id),
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=ClientOrderId(client_id),
        venue_order_id=VenueOrderId(venue_order_id),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=None,
        reduce_only=False,
        status=status,
        rejection_reason=None,
        submitted_at=NOW,
        accepted_at=NOW,
        filled_at=None,
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _venue_order(
    *,
    client_id: str = "client-1",
    venue_order_id: str = "venue-order-1",
    state: VenueOrderState = VenueOrderState.ACCEPTED,
) -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId(client_id),
        venue_order_id=VenueOrderId(venue_order_id),
        state=state,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        rejection_reason=None,
    )


def _local_fill() -> ExecutionFill:
    return ExecutionFill(
        fill_id=FillId("fill-1"),
        order_id=OrderId("order-1"),
        venue_fill_id=VenueFillId("venue-fill-1"),
        quantity=Decimal("0.25"),
        price=Decimal("60000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=NOW,
        created_at=NOW,
    )


def _venue_fill(
    venue_fill_id: str = "venue-fill-1",
) -> VenueFill:
    return VenueFill(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        venue_fill_id=VenueFillId(venue_fill_id),
        venue_order_id=VenueOrderId("venue-order-1"),
        client_order_id=ClientOrderId("client-1"),
        side=OrderSide.BUY,
        quantity=Decimal("0.25"),
        price=Decimal("60000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=NOW,
        observed_at=NOW,
    )


def _local_position(
    side: TradeSide = TradeSide.BUY,
    *,
    quantity: Decimal = Decimal("1"),
    entry: Decimal = Decimal("60000"),
) -> PositionLeg:
    return PositionLeg(
        group_id="group-1",
        leg_id=f"leg-{side.value.lower()}",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=side,
        target_quantity=Decimal("1"),
        filled_quantity=Decimal("1"),
        current_quantity=quantity,
        average_entry_price=entry,
        average_exit_price=None,
        status=PositionLegStatus.OPEN,
        opened_at=NOW,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _venue_position(
    side: VenuePositionSide = VenuePositionSide.LONG,
    *,
    quantity: Decimal = Decimal("1"),
    entry: Decimal = Decimal("60000"),
) -> VenuePosition:
    return VenuePosition(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=side,
        quantity=quantity,
        entry_price=entry,
        observed_at=NOW,
    )


def _detect(
    *,
    source: ReconciliationSourceState = (
        ReconciliationSourceState.CURRENT
    ),
    local_orders=(),
    venue_orders=(),
    local_fills=(),
    venue_fills=(),
    local_positions=(),
    venue_positions=(),
):
    return detect_reconciliation(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        source_state=source,
        observed_at=NOW,
        local_orders=tuple(local_orders),
        venue_orders=tuple(venue_orders),
        local_fills=tuple(local_fills),
        venue_fills=tuple(venue_fills),
        local_positions=tuple(local_positions),
        venue_positions=tuple(venue_positions),
    )


def _kinds(result):
    return {
        item.kind
        for item in result.discrepancies
    }


def test_position_projection_is_explicit_and_scoped() -> None:
    assert (
        position_side_for_leg(TradeSide.BUY)
        is VenuePositionSide.LONG
    )
    assert (
        position_side_for_leg(TradeSide.SELL)
        is VenuePositionSide.SHORT
    )


def test_matching_long_snapshot_is_green() -> None:
    result = _detect(
        local_orders=(_local_order(),),
        venue_orders=(_venue_order(),),
        local_fills=(_local_fill(),),
        venue_fills=(_venue_fill(),),
        local_positions=(_local_position(TradeSide.BUY),),
        venue_positions=(
            _venue_position(VenuePositionSide.LONG),
        ),
    )

    assert result.state is ReconciliationResultState.MATCHED
    assert result.discrepancies == ()


def test_matching_short_position_is_green() -> None:
    result = _detect(
        local_positions=(_local_position(TradeSide.SELL),),
        venue_positions=(
            _venue_position(VenuePositionSide.SHORT),
        ),
    )

    assert result.state is ReconciliationResultState.MATCHED


def test_detects_missing_and_unknown_orders() -> None:
    result = _detect(
        local_orders=(
            _local_order(
                order_id="local-order",
                client_id="local-client",
                venue_order_id="local-venue",
            ),
        ),
        venue_orders=(
            _venue_order(
                client_id="external-client",
                venue_order_id="external-venue",
            ),
        ),
    )

    assert _kinds(result) == {
        (
            ReconciliationDiscrepancyKind
            .LOCAL_ORDER_MISSING_ON_VENUE
        ),
        (
            ReconciliationDiscrepancyKind
            .VENUE_ORDER_UNKNOWN_LOCALLY
        ),
    }


def test_detects_order_state_drift() -> None:
    result = _detect(
        local_orders=(_local_order(),),
        venue_orders=(
            _venue_order(
                state=VenueOrderState.CANCELLED,
            ),
        ),
    )

    assert _kinds(result) == {
        ReconciliationDiscrepancyKind.ORDER_STATE_DRIFT
    }


def test_detects_missing_local_fill() -> None:
    result = _detect(
        local_orders=(_local_order(),),
        venue_orders=(_venue_order(),),
        venue_fills=(_venue_fill(),),
    )

    assert _kinds(result) == {
        ReconciliationDiscrepancyKind.MISSING_LOCAL_FILL
    }


def test_detects_duplicate_fill() -> None:
    result = _detect(
        local_orders=(_local_order(),),
        venue_orders=(_venue_order(),),
        venue_fills=(
            _venue_fill(),
            _venue_fill(),
        ),
    )

    assert (
        ReconciliationDiscrepancyKind
        .DUPLICATE_OR_REPLAYED_FILL
    ) in _kinds(result)


def test_detects_position_quantity_entry_and_side_drift() -> None:
    quantity_entry = _detect(
        local_positions=(
            _local_position(
                TradeSide.BUY,
                quantity=Decimal("1"),
                entry=Decimal("60000"),
            ),
        ),
        venue_positions=(
            _venue_position(
                VenuePositionSide.LONG,
                quantity=Decimal("2"),
                entry=Decimal("61000"),
            ),
        ),
    )

    assert _kinds(quantity_entry) == {
        ReconciliationDiscrepancyKind.POSITION_QUANTITY_DRIFT,
        (
            ReconciliationDiscrepancyKind
            .POSITION_ENTRY_PRICE_DRIFT
        ),
    }

    side = _detect(
        local_positions=(_local_position(TradeSide.BUY),),
        venue_positions=(
            _venue_position(VenuePositionSide.SHORT),
        ),
    )

    assert (
        ReconciliationDiscrepancyKind.POSITION_SIDE_DRIFT
        in _kinds(side)
    )


def test_detects_orphaned_local_and_missing_local_position() -> None:
    orphan = _detect(
        local_positions=(_local_position(),),
    )

    assert (
        ReconciliationDiscrepancyKind
        .LOCAL_POSITION_MISSING_ON_VENUE
    ) in _kinds(orphan)

    missing = _detect(
        venue_positions=(_venue_position(),),
    )

    assert (
        ReconciliationDiscrepancyKind
        .VENUE_POSITION_MISSING_LOCALLY
    ) in _kinds(missing)


def test_non_current_source_never_runs_negative_compare() -> None:
    result = _detect(
        source=ReconciliationSourceState.STALE,
        local_orders=(_local_order(),),
    )

    assert result.state is ReconciliationResultState.STALE
    assert _kinds(result) == {
        ReconciliationDiscrepancyKind.SOURCE_STALE
    }


def test_input_order_is_deterministic() -> None:
    first = _local_order(
        order_id="a",
        client_id="ca",
        venue_order_id="va",
    )
    second = _local_order(
        order_id="b",
        client_id="cb",
        venue_order_id="vb",
    )

    left = _detect(local_orders=(first, second))
    right = _detect(local_orders=(second, first))

    assert left == right


def test_detector_has_no_write_authority() -> None:
    import apps.core.application.reconciliation_detector as detector

    source = inspect.getsource(detector)

    forbidden = (
        "sqlalchemy",
        "AsyncSession",
        ".commit(",
        ".rollback(",
        "submit_order(",
        "cancel_order(",
        "ExecutionCoordinator",
    )

    assert not any(
        value in source
        for value in forbidden
    )
