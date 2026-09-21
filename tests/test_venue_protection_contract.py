"""Canonical protective-order contract tests."""

from decimal import Decimal

import pytest

from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.venue import (
    VenueOrderRequest,
    VenuePositionSide,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueId,
)

VENUE = VenueId("BINGX")
ACCOUNT = AccountId(venue_id=VENUE, value=7)
INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)

def _request(
    order_type: OrderType,
    *,
    trigger_price: Decimal | None = None,
    position_side: VenuePositionSide | None = None,
) -> VenueOrderRequest:
    return VenueOrderRequest(
        client_order_id=ClientOrderId("protection-1"),
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=OrderSide.SELL,
        quantity=Decimal("0.01"),
        order_type=order_type,
        trigger_price=trigger_price,
        position_side=position_side,
    )

@pytest.mark.parametrize(
    "order_type",
    (OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET),
)
def test_protective_market_order_requires_trigger_price(
    order_type: OrderType,
) -> None:
    with pytest.raises(ValueError, match="requires trigger_price"):
        _request(
            order_type,
            position_side=VenuePositionSide.LONG,
        )

@pytest.mark.parametrize(
    "order_type",
    (OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET),
)
def test_protective_market_order_requires_position_side(
    order_type: OrderType,
) -> None:
    with pytest.raises(ValueError, match="requires position_side"):
        _request(
            order_type,
            trigger_price=Decimal("59000"),
        )

@pytest.mark.parametrize(
    "order_type",
    (OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET),
)
def test_protective_market_order_preserves_canonical_fields(
    order_type: OrderType,
) -> None:
    request = _request(
        order_type,
        trigger_price=Decimal("59000"),
        position_side=VenuePositionSide.LONG,
    )

    assert request.quantity == Decimal("0.01")
    assert request.trigger_price == Decimal("59000")
    assert request.position_side is VenuePositionSide.LONG
    assert request.limit_price is None
    assert request.reduce_only is False
