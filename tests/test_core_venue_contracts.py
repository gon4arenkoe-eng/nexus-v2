from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.venue import (
    VenueCapabilities,
    VenueCapability,
    VenueOrderRequest,
    VenueOrderResult,
    VenueOrderState,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _identities(
    venue: str = "BINGX",
) -> tuple[AccountId, InstrumentId]:
    venue_id = VenueId(venue)

    account_id = AccountId(
        venue_id=venue_id,
        value=1,
    )

    instrument_id = InstrumentId(
        venue_id=venue_id,
        native_symbol="BTC-USDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    return account_id, instrument_id


def _request(
    *,
    order_type: OrderType = OrderType.MARKET,
    quantity: Decimal = Decimal("1"),
    limit_price: Decimal | None = None,
) -> VenueOrderRequest:
    account_id, instrument_id = _identities()

    return VenueOrderRequest(
        client_order_id="client-1",
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        reduce_only=False,
    )


def test_supported_capability_passes() -> None:
    caps = VenueCapabilities(
        frozenset({VenueCapability.ORDER_QUERY})
    )

    caps.require(VenueCapability.ORDER_QUERY)

    assert caps.supports(VenueCapability.ORDER_QUERY)


def test_unsupported_capability_fails_closed() -> None:
    caps = VenueCapabilities(frozenset())

    with pytest.raises(ValueError):
        caps.require(VenueCapability.ORDER_QUERY)


def test_unknown_capability_fails_closed() -> None:
    caps = VenueCapabilities(frozenset())

    assert caps.supports("ORDER_QUERY") is False  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        caps.require("ORDER_QUERY")  # type: ignore[arg-type]


def test_market_order_is_valid_without_limit_price() -> None:
    request = _request()

    assert request.limit_price is None


def test_market_order_rejects_limit_price() -> None:
    with pytest.raises(ValueError):
        _request(
            order_type=OrderType.MARKET,
            limit_price=Decimal("100"),
        )


def test_limit_order_requires_positive_limit_price() -> None:
    request = _request(
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
    )

    assert request.limit_price == Decimal("100")

    with pytest.raises(ValueError):
        _request(
            order_type=OrderType.LIMIT,
            limit_price=None,
        )

    with pytest.raises(ValueError):
        _request(
            order_type=OrderType.LIMIT,
            limit_price=Decimal("0"),
        )


def test_quantity_is_decimal_and_positive() -> None:
    request = _request(
        quantity=Decimal("0.10000001")
    )

    assert request.quantity == Decimal("0.10000001")
    assert isinstance(request.quantity, Decimal)

    with pytest.raises(ValueError):
        _request(quantity=Decimal("0"))


def test_float_quantity_fails_closed() -> None:
    with pytest.raises(ValueError):
        _request(quantity=0.1)  # type: ignore[arg-type]


def test_account_venue_must_match_instrument_venue() -> None:
    account_id, _ = _identities("BINGX")
    _, instrument_id = _identities("BINANCE")

    with pytest.raises(ValueError):
        VenueOrderRequest(
            client_order_id="client-1",
            account_id=account_id,
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.MARKET,
        )


def test_order_request_is_immutable() -> None:
    request = _request()

    with pytest.raises(FrozenInstanceError):
        request.quantity = Decimal("2")  # type: ignore[misc]


def test_partial_fill_result_is_supported() -> None:
    result = VenueOrderResult(
        client_order_id="client-1",
        venue_order_id="venue-1",
        state=VenueOrderState.PARTIALLY_FILLED,
        requested_quantity=Decimal("2"),
        filled_quantity=Decimal("1"),
        average_fill_price=Decimal("100"),
    )

    assert result.filled_quantity == Decimal("1")


def test_filled_requires_full_requested_quantity() -> None:
    with pytest.raises(ValueError):
        VenueOrderResult(
            client_order_id="client-1",
            venue_order_id="venue-1",
            state=VenueOrderState.FILLED,
            requested_quantity=Decimal("2"),
            filled_quantity=Decimal("1"),
            average_fill_price=Decimal("100"),
        )


def test_rejected_requires_reason() -> None:
    with pytest.raises(ValueError):
        VenueOrderResult(
            client_order_id="client-1",
            venue_order_id=None,
            state=VenueOrderState.REJECTED,
            requested_quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
        )


def test_unknown_state_is_explicit() -> None:
    result = VenueOrderResult(
        client_order_id="client-1",
        venue_order_id=None,
        state=VenueOrderState.UNKNOWN,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
    )

    assert result.state is VenueOrderState.UNKNOWN


def test_filled_quantity_cannot_exceed_requested() -> None:
    with pytest.raises(ValueError):
        VenueOrderResult(
            client_order_id="client-1",
            venue_order_id="venue-1",
            state=VenueOrderState.PARTIALLY_FILLED,
            requested_quantity=Decimal("1"),
            filled_quantity=Decimal("2"),
            average_fill_price=Decimal("100"),
        )


def test_nonzero_fill_requires_average_price() -> None:
    with pytest.raises(ValueError):
        VenueOrderResult(
            client_order_id="client-1",
            venue_order_id="venue-1",
            state=VenueOrderState.PARTIALLY_FILLED,
            requested_quantity=Decimal("2"),
            filled_quantity=Decimal("1"),
            average_fill_price=None,
        )
