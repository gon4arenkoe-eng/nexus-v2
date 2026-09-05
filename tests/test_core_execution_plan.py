from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apps.core.domain.execution import ExecutionLegPlan, ExecutionPlan
from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.orders import OrderType
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _identities(
    venue_name: str = "BINGX",
) -> tuple[AccountId, InstrumentId]:
    venue_id = VenueId(venue_name)

    account_id = AccountId(
        venue_id=venue_id,
        value=1,
    )

    instrument_id = InstrumentId(
        venue_id=venue_id,
        native_symbol="BTC-USDT",
        instrument_type=next(iter(InstrumentType)),
        asset_class=next(iter(AssetClass)),
    )

    return account_id, instrument_id


def _leg(
    *,
    leg_id: str = "leg-1",
    order_id: str = "order-1",
    client_order_id: str = "client-1",
    venue_name: str = "BINGX",
    side: TradeSide = TradeSide.BUY,
    quantity: Decimal = Decimal("1"),
    order_type: OrderType = OrderType.MARKET,
    limit_price: Decimal | None = None,
    reduce_only: bool = False,
) -> ExecutionLegPlan:
    account_id, instrument_id = _identities(venue_name)

    return ExecutionLegPlan(
        leg_id=leg_id,
        order_id=order_id,
        client_order_id=client_order_id,
        account_id=account_id,
        instrument_id=instrument_id,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        reduce_only=reduce_only,
    )


def _plan(
    *,
    shape: TradeIntentShape = TradeIntentShape.SINGLE_LEG,
    legs: tuple[ExecutionLegPlan, ...] | None = None,
    created_at: datetime | None = None,
) -> ExecutionPlan:
    if legs is None:
        legs = (_leg(),)

    if created_at is None:
        created_at = datetime(
            2026,
            9,
            5,
            12,
            0,
            tzinfo=timezone.utc,
        )

    return ExecutionPlan(
        plan_id="plan-1",
        intent_id="intent-1",
        user_id=1,
        shape=shape,
        strategy="trend",
        strategy_version="v1",
        source="strategy",
        legs=legs,
        created_at=created_at,
    )


def test_market_execution_leg_is_valid() -> None:
    leg = _leg()

    assert leg.quantity == Decimal("1")
    assert leg.order_type is OrderType.MARKET
    assert leg.limit_price is None


def test_limit_execution_leg_requires_positive_decimal_price() -> None:
    leg = _leg(
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
    )

    assert leg.limit_price == Decimal("100")

    with pytest.raises(ValueError):
        _leg(
            order_type=OrderType.LIMIT,
            limit_price=None,
        )

    with pytest.raises(ValueError):
        _leg(
            order_type=OrderType.LIMIT,
            limit_price=Decimal("0"),
        )


def test_market_execution_leg_rejects_limit_price() -> None:
    with pytest.raises(ValueError):
        _leg(
            order_type=OrderType.MARKET,
            limit_price=Decimal("100"),
        )


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_execution_leg_rejects_invalid_quantity(
    quantity: Decimal,
) -> None:
    with pytest.raises(ValueError):
        _leg(quantity=quantity)


def test_execution_leg_rejects_float_quantity() -> None:
    with pytest.raises(ValueError):
        _leg(quantity=1.0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "leg_id",
        "order_id",
        "client_order_id",
    ],
)
def test_execution_leg_requires_non_empty_ids(
    field_name: str,
) -> None:
    kwargs = {field_name: "   "}

    with pytest.raises(ValueError):
        _leg(**kwargs)


def test_execution_leg_requires_account_instrument_same_venue() -> None:
    bingx = VenueId("BINGX")
    binance = VenueId("BINANCE")

    account_id = AccountId(
        venue_id=bingx,
        value=1,
    )

    instrument_id = InstrumentId(
        venue_id=binance,
        native_symbol="BTC-USDT",
        instrument_type=next(iter(InstrumentType)),
        asset_class=next(iter(AssetClass)),
    )

    with pytest.raises(ValueError):
        ExecutionLegPlan(
            leg_id="leg-1",
            order_id="order-1",
            client_order_id="client-1",
            account_id=account_id,
            instrument_id=instrument_id,
            side=TradeSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.MARKET,
        )


def test_execution_leg_requires_boolean_reduce_only() -> None:
    with pytest.raises(ValueError):
        _leg(reduce_only=1)  # type: ignore[arg-type]


def test_single_leg_plan_requires_exactly_one_leg() -> None:
    _plan()

    with pytest.raises(ValueError):
        _plan(
            shape=TradeIntentShape.SINGLE_LEG,
            legs=(
                _leg(),
                _leg(
                    leg_id="leg-2",
                    order_id="order-2",
                    client_order_id="client-2",
                ),
            ),
        )


def test_pair_plan_requires_exactly_two_legs() -> None:
    legs = (
        _leg(),
        _leg(
            leg_id="leg-2",
            order_id="order-2",
            client_order_id="client-2",
            side=TradeSide.SELL,
        ),
    )

    plan = _plan(
        shape=TradeIntentShape.PAIR,
        legs=legs,
    )

    assert len(plan.legs) == 2

    with pytest.raises(ValueError):
        _plan(
            shape=TradeIntentShape.PAIR,
            legs=(legs[0],),
        )


def test_cross_venue_pair_is_valid() -> None:
    plan = _plan(
        shape=TradeIntentShape.PAIR,
        legs=(
            _leg(
                venue_name="BINGX",
            ),
            _leg(
                leg_id="leg-2",
                order_id="order-2",
                client_order_id="client-2",
                venue_name="BINANCE",
                side=TradeSide.SELL,
            ),
        ),
    )

    assert (
        plan.legs[0].account_id.venue_id
        != plan.legs[1].account_id.venue_id
    )


def test_basket_requires_at_least_two_legs() -> None:
    with pytest.raises(ValueError):
        _plan(
            shape=TradeIntentShape.BASKET,
            legs=(_leg(),),
        )


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("leg_id", "leg_id"),
        ("order_id", "order_id"),
        ("client_order_id", "client_order_id"),
    ],
)
def test_execution_plan_rejects_duplicate_execution_ids(
    first: str,
    second: str,
) -> None:
    leg1 = _leg()

    values = {
        "leg_id": "leg-2",
        "order_id": "order-2",
        "client_order_id": "client-2",
    }

    values[second] = getattr(leg1, first)

    leg2 = _leg(
        leg_id=values["leg_id"],
        order_id=values["order_id"],
        client_order_id=values["client_order_id"],
    )

    with pytest.raises(ValueError):
        _plan(
            shape=TradeIntentShape.PAIR,
            legs=(leg1, leg2),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("plan_id", ""),
        ("intent_id", ""),
        ("strategy", ""),
        ("source", ""),
    ],
)
def test_execution_plan_requires_non_empty_text(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "plan_id": "plan-1",
        "intent_id": "intent-1",
        "user_id": 1,
        "shape": TradeIntentShape.SINGLE_LEG,
        "strategy": "trend",
        "strategy_version": "v1",
        "source": "strategy",
        "legs": (_leg(),),
        "created_at": datetime(
            2026,
            9,
            5,
            tzinfo=timezone.utc,
        ),
    }

    kwargs[field_name] = value

    with pytest.raises(ValueError):
        ExecutionPlan(**kwargs)


@pytest.mark.parametrize(
    "user_id",
    [0, -1, True],
)
def test_execution_plan_requires_positive_integer_user(
    user_id: int,
) -> None:
    with pytest.raises(ValueError):
        ExecutionPlan(
            plan_id="plan-1",
            intent_id="intent-1",
            user_id=user_id,
            shape=TradeIntentShape.SINGLE_LEG,
            strategy="trend",
            strategy_version="v1",
            source="strategy",
            legs=(_leg(),),
            created_at=datetime(
                2026,
                9,
                5,
                tzinfo=timezone.utc,
            ),
        )


def test_execution_plan_requires_tuple_legs() -> None:
    with pytest.raises(ValueError):
        ExecutionPlan(
            plan_id="plan-1",
            intent_id="intent-1",
            user_id=1,
            shape=TradeIntentShape.SINGLE_LEG,
            strategy="trend",
            strategy_version="v1",
            source="strategy",
            legs=[_leg()],  # type: ignore[arg-type]
            created_at=datetime(
                2026,
                9,
                5,
                tzinfo=timezone.utc,
            ),
        )


def test_execution_plan_normalizes_created_at_to_utc() -> None:
    source_timezone = timezone(timedelta(hours=3))

    plan = _plan(
        created_at=datetime(
            2026,
            9,
            5,
            15,
            0,
            tzinfo=source_timezone,
        ),
    )

    assert plan.created_at == datetime(
        2026,
        9,
        5,
        12,
        0,
        tzinfo=timezone.utc,
    )


def test_execution_plan_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError):
        _plan(
            created_at=datetime(
                2026,
                9,
                5,
                12,
                0,
            ),
        )


def test_execution_contracts_are_immutable() -> None:
    leg = _leg()
    plan = _plan()

    with pytest.raises(FrozenInstanceError):
        leg.quantity = Decimal("2")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        plan.plan_id = "other"  # type: ignore[misc]
