from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.domain.intents import (
    TradeIntent,
    TradeIntentKind,
    TradeIntentShape,
    TradeLegIntent,
    TradeSide,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _leg(
    leg_id: str,
    *,
    venue: str = "BINGX",
    account_value: int = 1,
    quantity: Decimal | None = Decimal("1"),
) -> TradeLegIntent:
    venue_id = VenueId(venue)

    return TradeLegIntent(
        leg_id=leg_id,
        instrument_id=InstrumentId(
            venue_id=venue_id,
            native_symbol="BTC-USDT",
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        ),
        account_id=AccountId(
            venue_id=venue_id,
            value=account_value,
        ),
        side=TradeSide.BUY,
        quantity=quantity,
    )


def _intent(
    *,
    shape: TradeIntentShape,
    legs: tuple[TradeLegIntent, ...],
) -> TradeIntent:
    return TradeIntent(
        intent_id="intent-1",
        user_id=1,
        strategy="statistical_arbitrage",
        strategy_version="v2",
        source="STRATEGY_ENGINE",
        kind=TradeIntentKind.OPEN,
        shape=shape,
        legs=legs,
        created_at=datetime(
            2026,
            9,
            5,
            12,
            0,
            tzinfo=UTC,
        ),
        metadata={"evidence": "test"},
    )


def test_single_leg_requires_exactly_one_leg() -> None:
    _intent(
        shape=TradeIntentShape.SINGLE_LEG,
        legs=(_leg("A"),),
    )

    with pytest.raises(ValueError):
        _intent(
            shape=TradeIntentShape.SINGLE_LEG,
            legs=(_leg("A"), _leg("B")),
        )


def test_pair_requires_exactly_two_legs() -> None:
    _intent(
        shape=TradeIntentShape.PAIR,
        legs=(_leg("A"), _leg("B")),
    )

    with pytest.raises(ValueError):
        _intent(
            shape=TradeIntentShape.PAIR,
            legs=(_leg("A"),),
        )


def test_basket_requires_at_least_two_legs() -> None:
    _intent(
        shape=TradeIntentShape.BASKET,
        legs=(_leg("A"), _leg("B")),
    )

    with pytest.raises(ValueError):
        _intent(
            shape=TradeIntentShape.BASKET,
            legs=(_leg("A"),),
        )


def test_leg_ids_must_be_unique() -> None:
    with pytest.raises(ValueError):
        _intent(
            shape=TradeIntentShape.PAIR,
            legs=(_leg("A"), _leg("A")),
        )


def test_quantity_may_be_none() -> None:
    leg = _leg("A", quantity=None)

    assert leg.quantity is None


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_quantity_must_be_positive_when_present(
    quantity: Decimal,
) -> None:
    with pytest.raises(ValueError):
        _leg("A", quantity=quantity)


def test_account_venue_must_match_instrument_venue() -> None:
    instrument_venue = VenueId("BINGX")

    with pytest.raises(ValueError):
        TradeLegIntent(
            leg_id="A",
            instrument_id=InstrumentId(
                venue_id=instrument_venue,
                native_symbol="BTC-USDT",
                instrument_type=InstrumentType.PERPETUAL,
                asset_class=AssetClass.CRYPTO,
            ),
            account_id=AccountId(
                venue_id=VenueId("BINANCE"),
                value=1,
            ),
            side=TradeSide.BUY,
            quantity=Decimal("1"),
        )


def test_cross_venue_pair_is_supported_per_leg() -> None:
    intent = _intent(
        shape=TradeIntentShape.PAIR,
        legs=(
            _leg("A", venue="BINGX"),
            _leg("B", venue="BINANCE"),
        ),
    )

    assert (
        intent.legs[0].instrument_id.venue_id
        != intent.legs[1].instrument_id.venue_id
    )


def test_trade_intent_is_immutable() -> None:
    intent = _intent(
        shape=TradeIntentShape.SINGLE_LEG,
        legs=(_leg("A"),),
    )

    with pytest.raises(FrozenInstanceError):
        intent.intent_id = "changed"  # type: ignore[misc]


def test_metadata_is_immutable_copy() -> None:
    source_metadata = {"key": "value"}

    intent = TradeIntent(
        intent_id="intent-1",
        user_id=1,
        strategy="strategy",
        strategy_version="v1",
        source="STRATEGY_ENGINE",
        kind=TradeIntentKind.OPEN,
        shape=TradeIntentShape.SINGLE_LEG,
        legs=(_leg("A"),),
        created_at=datetime.now(UTC),
        metadata=source_metadata,
    )

    source_metadata["key"] = "changed"

    assert intent.metadata["key"] == "value"

    with pytest.raises(TypeError):
        intent.metadata["key"] = "x"  # type: ignore[index]


def test_empty_intent_id_fails_closed() -> None:
    with pytest.raises(ValueError):
        TradeIntent(
            intent_id="   ",
            user_id=1,
            strategy="strategy",
            strategy_version="v1",
            source="STRATEGY_ENGINE",
            kind=TradeIntentKind.OPEN,
            shape=TradeIntentShape.SINGLE_LEG,
            legs=(_leg("A"),),
            created_at=datetime.now(UTC),
        )


def test_created_at_is_normalized_to_utc() -> None:
    intent = _intent(
        shape=TradeIntentShape.SINGLE_LEG,
        legs=(_leg("A"),),
    )

    assert intent.created_at.tzinfo is UTC
