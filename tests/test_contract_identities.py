from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    FillId,
    InstrumentId,
    OrderId,
    VenueFillId,
    VenueOrderId,
    InstrumentType,
    VenueId,
)


def test_venue_id_is_normalized() -> None:
    assert VenueId(" bingx ").value == "BINGX"


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_venue_id_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError):
        VenueId(value)


def test_venue_id_is_immutable() -> None:
    venue_id = VenueId("BINGX")

    with pytest.raises(FrozenInstanceError):
        venue_id.value = "BINANCE"  # type: ignore[misc]


@pytest.mark.parametrize("value", [0, -1])
def test_account_id_requires_positive_integer(value: int) -> None:
    with pytest.raises(ValueError):
        AccountId(VenueId("BINGX"), value)


@pytest.mark.parametrize("value", [True, 1.5, "1"])
def test_account_id_rejects_non_integer_identity(value: object) -> None:
    with pytest.raises(ValueError):
        AccountId(VenueId("BINGX"), value)  # type: ignore[arg-type]


def test_account_id_is_venue_aware() -> None:
    assert AccountId(VenueId("BINGX"), 1) != AccountId(
        VenueId("BINANCE"),
        1,
    )


def test_instrument_id_normalizes_native_symbol() -> None:
    instrument_id = InstrumentId(
        venue_id=VenueId("bingx"),
        native_symbol=" btc-usdt ",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    assert instrument_id.venue_id == VenueId("BINGX")
    assert instrument_id.native_symbol == "BTC-USDT"


def test_same_native_symbol_on_different_venues_is_not_same_identity() -> None:
    bingx = InstrumentId(
        venue_id=VenueId("BINGX"),
        native_symbol="BTC-USDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )
    binance = InstrumentId(
        venue_id=VenueId("BINANCE"),
        native_symbol="BTC-USDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    assert bingx != binance


def test_instrument_type_is_part_of_identity() -> None:
    spot = InstrumentId(
        venue_id=VenueId("BINGX"),
        native_symbol="BTC-USDT",
        instrument_type=InstrumentType.SPOT,
        asset_class=AssetClass.CRYPTO,
    )
    perpetual = InstrumentId(
        venue_id=VenueId("BINGX"),
        native_symbol="BTC-USDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    assert spot != perpetual


def test_instrument_id_rejects_empty_native_symbol() -> None:
    with pytest.raises(ValueError):
        InstrumentId(
            venue_id=VenueId("BINGX"),
            native_symbol=" ",
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        )


def test_identity_enums_match_approved_contract() -> None:
    assert {item.value for item in AssetClass} == {
        "CRYPTO",
        "EQUITY",
        "ETF",
        "FOREX",
        "COMMODITY",
        "FUTURE",
        "OPTION",
        "BOND",
        "INDEX",
        "CFD",
    }

    assert {item.value for item in InstrumentType} == {
        "SPOT",
        "PERPETUAL",
        "FUTURE",
        "OPTION",
        "STOCK",
        "ETF",
        "FX_PAIR",
        "CFD",
    }


def test_opaque_identity_ids_preserve_case_and_strip_only() -> None:
    assert str(OrderId(" order-A ")) == "order-A"
    assert str(ClientOrderId(" Client-A ")) == "Client-A"
    assert str(VenueOrderId(" VENUE-A ")) == "VENUE-A"
    assert str(FillId(" Fill-A ")) == "Fill-A"
    assert str(VenueFillId(" VenueFill-A ")) == "VenueFill-A"


def test_opaque_identity_ids_are_distinct_types() -> None:
    assert OrderId("same") != FillId("same")
    assert ClientOrderId("same") != VenueOrderId("same")
    assert VenueOrderId("same") != VenueFillId("same")


@pytest.mark.parametrize(
    ("identity_type", "field_name"),
    (
        (OrderId, "order_id"),
        (ClientOrderId, "client_order_id"),
        (VenueOrderId, "venue_order_id"),
        (FillId, "fill_id"),
        (VenueFillId, "venue_fill_id"),
    ),
)
def test_opaque_identity_ids_reject_blank(
    identity_type: type[object],
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        identity_type("   ")
