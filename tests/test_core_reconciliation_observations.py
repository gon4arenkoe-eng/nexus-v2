"""Phase 3 canonical reconciliation observation contracts."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apps.core.domain.orders import OrderSide
from apps.core.ports.venue import (
    VenueAccountState,
    VenueBalance,
    VenueCapabilities,
    VenueCapability,
    VenueFill,
    VenuePosition,
    VenuePositionSide,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueFillId,
    VenueId,
    VenueOrderId,
)


def _venue(value: str = "BINANCE") -> VenueId:
    return VenueId(value)


def _account(value: int = 7) -> AccountId:
    return AccountId(
        venue_id=_venue(),
        value=value,
    )


def _instrument(
    venue: str = "BINANCE",
) -> InstrumentId:
    return InstrumentId(
        venue_id=VenueId(venue),
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _time(second: int = 0) -> datetime:
    return datetime(
        2026,
        9,
        12,
        10,
        0,
        second,
        tzinfo=UTC,
    )


def test_reconciliation_query_capabilities_are_explicit() -> None:
    capabilities = VenueCapabilities(
        frozenset(
            {
                VenueCapability.POSITION_QUERY,
                VenueCapability.ACCOUNT_QUERY,
                VenueCapability.FILL_QUERY,
            }
        )
    )

    assert capabilities.supports(
        VenueCapability.POSITION_QUERY
    )
    assert capabilities.supports(
        VenueCapability.ACCOUNT_QUERY
    )
    assert capabilities.supports(
        VenueCapability.FILL_QUERY
    )


def test_position_preserves_hedge_side_identity() -> None:
    long_position = VenuePosition(
        account_id=_account(),
        instrument_id=_instrument(),
        side=VenuePositionSide.LONG,
        quantity=Decimal("2"),
        entry_price=Decimal("62000"),
        observed_at=_time(),
    )
    short_position = VenuePosition(
        account_id=_account(),
        instrument_id=_instrument(),
        side=VenuePositionSide.SHORT,
        quantity=Decimal("1"),
        entry_price=Decimal("63000"),
        observed_at=_time(),
    )

    assert long_position.instrument_id == short_position.instrument_id
    assert long_position.side is VenuePositionSide.LONG
    assert short_position.side is VenuePositionSide.SHORT


def test_position_rejects_cross_venue_identity() -> None:
    with pytest.raises(
        ValueError,
        match="account venue must match instrument venue",
    ):
        VenuePosition(
            account_id=_account(),
            instrument_id=_instrument("BYBIT"),
            side=VenuePositionSide.LONG,
            quantity=Decimal("1"),
            entry_price=Decimal("62000"),
            observed_at=_time(),
        )


def test_flat_position_cannot_have_entry_price() -> None:
    position = VenuePosition(
        account_id=_account(),
        instrument_id=_instrument(),
        side=VenuePositionSide.LONG,
        quantity=Decimal("0"),
        entry_price=None,
        observed_at=_time(),
    )

    assert position.entry_price is None

    with pytest.raises(
        ValueError,
        match="flat venue position",
    ):
        VenuePosition(
            account_id=_account(),
            instrument_id=_instrument(),
            side=VenuePositionSide.LONG,
            quantity=Decimal("0"),
            entry_price=Decimal("1"),
            observed_at=_time(),
        )


def test_open_position_requires_entry_price() -> None:
    with pytest.raises(
        ValueError,
        match="requires entry_price",
    ):
        VenuePosition(
            account_id=_account(),
            instrument_id=_instrument(),
            side=VenuePositionSide.SHORT,
            quantity=Decimal("1"),
            entry_price=None,
            observed_at=_time(),
        )


def test_account_state_normalizes_balance_and_time() -> None:
    observed = datetime(
        2026,
        9,
        12,
        13,
        0,
        tzinfo=timezone(timedelta(hours=3)),
    )

    state = VenueAccountState(
        account_id=_account(),
        balances=(
            VenueBalance(
                currency=" usdt ",
                total=Decimal("1000"),
                available=Decimal("750"),
            ),
        ),
        observed_at=observed,
    )

    assert state.balances[0].currency == "USDT"
    assert state.observed_at.tzinfo is UTC
    assert state.observed_at.hour == 10


def test_account_state_rejects_duplicate_currency() -> None:
    balance = VenueBalance(
        currency="USDT",
        total=Decimal("100"),
        available=Decimal("100"),
    )

    with pytest.raises(
        ValueError,
        match="duplicate currency",
    ):
        VenueAccountState(
            account_id=_account(),
            balances=(balance, balance),
            observed_at=_time(),
        )


def test_balance_requires_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="total must be finite",
    ):
        VenueBalance(
            currency="USDT",
            total=Decimal("NaN"),
            available=Decimal("1"),
        )


def test_fill_preserves_identity_and_fee_evidence() -> None:
    fill = VenueFill(
        account_id=_account(),
        instrument_id=_instrument(),
        venue_fill_id=VenueFillId("trade-1"),
        venue_order_id=VenueOrderId("order-1"),
        client_order_id=ClientOrderId("client-1"),
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        price=Decimal("62000"),
        fee=Decimal("1.25"),
        fee_currency=" usdt ",
        executed_at=_time(),
        observed_at=_time(1),
    )

    assert fill.venue_fill_id == VenueFillId("trade-1")
    assert fill.fee_currency == "USDT"


def test_fill_allows_missing_venue_fill_id() -> None:
    fill = VenueFill(
        account_id=_account(),
        instrument_id=_instrument(),
        venue_fill_id=None,
        venue_order_id=VenueOrderId("order-1"),
        client_order_id=None,
        side=OrderSide.SELL,
        quantity=Decimal("0.2"),
        price=Decimal("61000"),
        fee=Decimal("0"),
        fee_currency=None,
        executed_at=_time(),
        observed_at=_time(),
    )

    assert fill.venue_fill_id is None


def test_positive_fee_requires_currency() -> None:
    with pytest.raises(
        ValueError,
        match="positive fee requires fee_currency",
    ):
        VenueFill(
            account_id=_account(),
            instrument_id=_instrument(),
            venue_fill_id=None,
            venue_order_id=None,
            client_order_id=None,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("1"),
            fee_currency=None,
            executed_at=_time(),
            observed_at=_time(),
        )


def test_fill_observation_cannot_precede_execution() -> None:
    with pytest.raises(
        ValueError,
        match="observed_at must not precede executed_at",
    ):
        VenueFill(
            account_id=_account(),
            instrument_id=_instrument(),
            venue_fill_id=None,
            venue_order_id=None,
            client_order_id=None,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_currency=None,
            executed_at=_time(1),
            observed_at=_time(),
        )


def test_fill_rejects_cross_venue_identity() -> None:
    with pytest.raises(
        ValueError,
        match="account venue must match instrument venue",
    ):
        VenueFill(
            account_id=_account(),
            instrument_id=_instrument("OKX"),
            venue_fill_id=None,
            venue_order_id=None,
            client_order_id=None,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_currency=None,
            executed_at=_time(),
            observed_at=_time(),
        )


def test_contracts_have_no_raw_payload_field() -> None:
    for contract in (
        VenuePosition,
        VenueAccountState,
        VenueFill,
    ):
        names = {
            field.name
            for field in fields(contract)
        }

        assert "raw" not in names
        assert "payload" not in names
        assert "raw_payload" not in names
