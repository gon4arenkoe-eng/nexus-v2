from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.positions import (
    PositionGroup,
    PositionGroupStatus,
    PositionLeg,
    PositionLegStatus,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


CREATED = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
OPENED = datetime(2026, 9, 5, 12, 1, tzinfo=timezone.utc)
CLOSED = datetime(2026, 9, 5, 12, 2, tzinfo=timezone.utc)


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


def _group(
    *,
    status: PositionGroupStatus = PositionGroupStatus.PENDING,
    opened_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> PositionGroup:
    return PositionGroup(
        group_id="group-1",
        plan_id="plan-1",
        user_id=1,
        shape=TradeIntentShape.PAIR,
        strategy="trend",
        strategy_version="v1",
        trade_source="strategy",
        status=status,
        opened_at=opened_at,
        closed_at=closed_at,
        created_at=CREATED,
        updated_at=CLOSED,
    )


def _leg(
    *,
    status: PositionLegStatus = PositionLegStatus.PENDING,
    filled_quantity: Decimal = Decimal("0"),
    current_quantity: Decimal = Decimal("0"),
    average_entry_price: Decimal | None = None,
    average_exit_price: Decimal | None = None,
    opened_at: datetime | None = None,
    closed_at: datetime | None = None,
    venue: str = "BINGX",
) -> PositionLeg:
    account_id, instrument_id = _identity(venue)

    return PositionLeg(
        group_id="group-1",
        leg_id="leg-1",
        account_id=account_id,
        instrument_id=instrument_id,
        side=TradeSide.BUY,
        target_quantity=Decimal("1"),
        filled_quantity=filled_quantity,
        current_quantity=current_quantity,
        average_entry_price=average_entry_price,
        average_exit_price=average_exit_price,
        status=status,
        opened_at=opened_at,
        closed_at=closed_at,
        created_at=CREATED,
        updated_at=CLOSED,
    )


def test_pending_group_is_valid() -> None:
    group = _group()

    assert group.status is PositionGroupStatus.PENDING
    assert group.opened_at is None
    assert group.closed_at is None


@pytest.mark.parametrize(
    "status",
    [
        PositionGroupStatus.OPEN,
        PositionGroupStatus.CLOSING,
    ],
)
def test_active_group_states_require_opened_at(
    status: PositionGroupStatus,
) -> None:
    with pytest.raises(ValueError):
        _group(status=status)

    group = _group(
        status=status,
        opened_at=OPENED,
    )

    assert group.opened_at == OPENED


def test_opening_group_allows_pre_fill_state() -> None:
    group = _group(
        status=PositionGroupStatus.OPENING,
    )

    assert group.opened_at is None


def test_closed_group_requires_open_and_close_times() -> None:
    group = _group(
        status=PositionGroupStatus.CLOSED,
        opened_at=OPENED,
        closed_at=CLOSED,
    )

    assert group.status is PositionGroupStatus.CLOSED

    with pytest.raises(ValueError):
        _group(
            status=PositionGroupStatus.CLOSED,
            opened_at=OPENED,
        )


def test_group_timestamps_normalize_to_utc() -> None:
    plus_three = timezone(timedelta(hours=3))

    group = PositionGroup(
        group_id="group-1",
        plan_id="plan-1",
        user_id=1,
        shape=TradeIntentShape.SINGLE_LEG,
        strategy="trend",
        strategy_version=None,
        trade_source="strategy",
        status=PositionGroupStatus.PENDING,
        opened_at=None,
        closed_at=None,
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

    assert group.created_at == CREATED


def test_pending_leg_is_zero_projection() -> None:
    leg = _leg()

    assert leg.status is PositionLegStatus.PENDING
    assert leg.filled_quantity == Decimal("0")
    assert leg.current_quantity == Decimal("0")


def test_pending_leg_rejects_execution_projection() -> None:
    with pytest.raises(ValueError):
        _leg(
            filled_quantity=Decimal("1"),
        )


def test_open_leg_requires_exposure_and_entry_evidence() -> None:
    leg = _leg(
        status=PositionLegStatus.OPEN,
        filled_quantity=Decimal("1"),
        current_quantity=Decimal("0.4"),
        average_entry_price=Decimal("100"),
        opened_at=OPENED,
    )

    assert leg.current_quantity == Decimal("0.4")

    with pytest.raises(ValueError):
        _leg(
            status=PositionLegStatus.OPEN,
            filled_quantity=Decimal("1"),
            current_quantity=Decimal("0"),
            average_entry_price=Decimal("100"),
            opened_at=OPENED,
        )


def test_open_leg_allows_partial_exit_projection() -> None:
    leg = _leg(
        status=PositionLegStatus.OPEN,
        filled_quantity=Decimal("1"),
        current_quantity=Decimal("0.5"),
        average_entry_price=Decimal("100"),
        average_exit_price=Decimal("110"),
        opened_at=OPENED,
    )

    assert leg.average_exit_price == Decimal("110")


def test_closed_leg_requires_flat_exposure_and_prices() -> None:
    leg = _leg(
        status=PositionLegStatus.CLOSED,
        filled_quantity=Decimal("1"),
        current_quantity=Decimal("0"),
        average_entry_price=Decimal("100"),
        average_exit_price=Decimal("110"),
        opened_at=OPENED,
        closed_at=CLOSED,
    )

    assert leg.current_quantity == Decimal("0")

    with pytest.raises(ValueError):
        _leg(
            status=PositionLegStatus.CLOSED,
            filled_quantity=Decimal("1"),
            current_quantity=Decimal("0.1"),
            average_entry_price=Decimal("100"),
            average_exit_price=Decimal("110"),
            opened_at=OPENED,
            closed_at=CLOSED,
        )


def test_leg_rejects_account_instrument_venue_mismatch() -> None:
    account_id, _ = _identity("BINGX")
    _, instrument_id = _identity("BINANCE")

    with pytest.raises(ValueError):
        PositionLeg(
            group_id="group-1",
            leg_id="leg-1",
            account_id=account_id,
            instrument_id=instrument_id,
            side=TradeSide.BUY,
            target_quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            current_quantity=Decimal("0"),
            average_entry_price=None,
            average_exit_price=None,
            status=PositionLegStatus.PENDING,
            opened_at=None,
            closed_at=None,
            created_at=CREATED,
            updated_at=CREATED,
        )


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_target_quantity_must_be_positive_finite_decimal(
    value: Decimal,
) -> None:
    account_id, instrument_id = _identity()

    with pytest.raises(ValueError):
        PositionLeg(
            group_id="group-1",
            leg_id="leg-1",
            account_id=account_id,
            instrument_id=instrument_id,
            side=TradeSide.BUY,
            target_quantity=value,
            filled_quantity=Decimal("0"),
            current_quantity=Decimal("0"),
            average_entry_price=None,
            average_exit_price=None,
            status=PositionLegStatus.PENDING,
            opened_at=None,
            closed_at=None,
            created_at=CREATED,
            updated_at=CREATED,
        )


def test_position_contracts_are_immutable() -> None:
    group = _group()
    leg = _leg()

    with pytest.raises(FrozenInstanceError):
        group.status = PositionGroupStatus.OPEN  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        leg.current_quantity = Decimal("1")  # type: ignore[misc]
