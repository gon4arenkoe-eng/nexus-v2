"""Deterministic Phase 3 reconciliation comparison logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from hashlib import sha256

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
)
from apps.core.domain.intents import TradeSide
from apps.core.domain.positions import PositionLeg
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancy,
    ReconciliationDiscrepancyKind,
    ReconciliationResult,
    ReconciliationSourceState,
    ReconciliationSubject,
    build_reconciliation_result,
)
from apps.core.ports.venue import (
    VenueFill,
    VenueOrderResult,
    VenuePosition,
    VenuePositionSide,
)
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
    VenueAccountState,
)


from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)


class ReconciliationDetectionError(ValueError):
    """Input snapshots cannot be reconciled deterministically."""


_SOURCE_KIND = {
    ReconciliationSourceState.STALE:
        ReconciliationDiscrepancyKind.SOURCE_STALE,
    ReconciliationSourceState.DEGRADED:
        ReconciliationDiscrepancyKind.SOURCE_DEGRADED,
    ReconciliationSourceState.UNAVAILABLE:
        ReconciliationDiscrepancyKind.SOURCE_UNAVAILABLE,
    ReconciliationSourceState.UNKNOWN:
        ReconciliationDiscrepancyKind.SOURCE_UNKNOWN,
}


def position_side_for_leg(
    side: TradeSide,
) -> VenuePositionSide:
    """Project immutable PositionLeg exposure into venue position side."""

    if side is TradeSide.BUY:
        return VenuePositionSide.LONG

    if side is TradeSide.SELL:
        return VenuePositionSide.SHORT

    raise ReconciliationDetectionError(
        "unsupported PositionLeg TradeSide"
    )


def _decimal_text(value: Decimal | None) -> str:
    if value is None:
        return "NONE"

    normalized = value.normalize()

    if normalized == Decimal("-0"):
        normalized = Decimal("0")

    return format(normalized, "f")


def _check_local_order_scope(
    order: ExecutionOrder,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
) -> None:
    if order.account_id != account_id:
        raise ReconciliationDetectionError(
            "local order account outside reconciliation scope"
        )

    if order.instrument_id != instrument_id:
        raise ReconciliationDetectionError(
            "local order instrument outside reconciliation scope"
        )


def _order_keys(
    *,
    venue_order_id: object | None,
    client_order_id: object,
) -> tuple[str, ...]:
    keys = [f"client:{client_order_id}"]

    if venue_order_id is not None:
        keys.insert(0, f"venue:{venue_order_id}")

    return tuple(keys)


def _order_projection(
    state: str,
    requested: Decimal,
    filled: Decimal,
    average: Decimal | None,
) -> str:
    return "|".join(
        (
            f"state={state}",
            f"requested={_decimal_text(requested)}",
            f"filled={_decimal_text(filled)}",
            f"average={_decimal_text(average)}",
        )
    )


def _detect_orders(
    *,
    user_id: int,
    account_id: AccountId,
    instrument_id: InstrumentId,
    observed_at: datetime,
    local_orders: tuple[ExecutionOrder, ...],
    venue_orders: tuple[VenueOrderResult, ...],
) -> list[ReconciliationDiscrepancy]:
    venue_index: dict[str, int] = {}

    for index, order in enumerate(venue_orders):
        for key in _order_keys(
            venue_order_id=order.venue_order_id,
            client_order_id=order.client_order_id,
        ):
            prior = venue_index.get(key)

            if prior is not None and prior != index:
                raise ReconciliationDetectionError(
                    "duplicate venue order identity"
                )

            venue_index[key] = index

    matched: set[int] = set()
    result: list[ReconciliationDiscrepancy] = []

    for local in local_orders:
        _check_local_order_scope(
            local,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        candidates = {
            venue_index[key]
            for key in _order_keys(
                venue_order_id=local.venue_order_id,
                client_order_id=local.client_order_id,
            )
            if key in venue_index
        }

        if len(candidates) > 1:
            raise ReconciliationDetectionError(
                "local order maps to multiple venue orders"
            )

        if not candidates:
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .LOCAL_ORDER_MISSING_ON_VENUE
                    ),
                    subject=ReconciliationSubject.ORDER,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=str(local.order_id),
                )
            )
            continue

        venue_index_value = next(iter(candidates))

        if venue_index_value in matched:
            raise ReconciliationDetectionError(
                "multiple local orders map to one venue order"
            )

        matched.add(venue_index_value)
        venue = venue_orders[venue_index_value]

        local_value = _order_projection(
            local.status.value,
            local.requested_quantity,
            local.filled_quantity,
            local.average_fill_price,
        )

        venue_value = _order_projection(
            venue.state.value,
            venue.requested_quantity,
            venue.filled_quantity,
            venue.average_fill_price,
        )

        if local_value != venue_value:
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .ORDER_STATE_DRIFT
                    ),
                    subject=ReconciliationSubject.ORDER,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=str(local.order_id),
                    venue_reference=(
                        str(venue.venue_order_id)
                        if venue.venue_order_id is not None
                        else str(venue.client_order_id)
                    ),
                    local_value=local_value,
                    venue_value=venue_value,
                )
            )

    for index, venue in enumerate(venue_orders):
        if index in matched:
            continue

        result.append(
            ReconciliationDiscrepancy(
                kind=(
                    ReconciliationDiscrepancyKind
                    .VENUE_ORDER_UNKNOWN_LOCALLY
                ),
                subject=ReconciliationSubject.ORDER,
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
                observed_at=observed_at,
                venue_reference=(
                    str(venue.venue_order_id)
                    if venue.venue_order_id is not None
                    else str(venue.client_order_id)
                ),
            )
        )

    return result


def _fill_material(
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
    venue_order_id: str,
    client_order_id: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    fee: Decimal,
    fee_currency: str | None,
    executed_at: datetime,
) -> str:
    return "|".join(
        (
            str(account_id.venue_id),
            str(account_id.value),
            str(instrument_id.venue_id),
            instrument_id.native_symbol,
            instrument_id.instrument_type.value,
            instrument_id.asset_class.value,
            venue_order_id,
            client_order_id,
            side,
            _decimal_text(quantity),
            _decimal_text(price),
            _decimal_text(fee),
            fee_currency or "",
            executed_at.isoformat(),
        )
    )


def _local_fill_key(
    fill: ExecutionFill,
    *,
    order: ExecutionOrder,
) -> str:
    if fill.venue_fill_id is not None:
        return f"venue:{fill.venue_fill_id}"

    material = _fill_material(
        account_id=order.account_id,
        instrument_id=order.instrument_id,
        venue_order_id=(
            str(order.venue_order_id)
            if order.venue_order_id is not None
            else ""
        ),
        client_order_id=str(order.client_order_id),
        side=order.side.value,
        quantity=fill.quantity,
        price=fill.price,
        fee=fill.fee,
        fee_currency=fill.fee_currency,
        executed_at=fill.executed_at,
    )

    return "fallback:" + sha256(
        material.encode("utf-8")
    ).hexdigest()


def _venue_fill_key(fill: VenueFill) -> str:
    if fill.venue_fill_id is not None:
        return f"venue:{fill.venue_fill_id}"

    material = _fill_material(
        account_id=fill.account_id,
        instrument_id=fill.instrument_id,
        venue_order_id=(
            str(fill.venue_order_id)
            if fill.venue_order_id is not None
            else ""
        ),
        client_order_id=(
            str(fill.client_order_id)
            if fill.client_order_id is not None
            else ""
        ),
        side=fill.side.value,
        quantity=fill.quantity,
        price=fill.price,
        fee=fill.fee,
        fee_currency=fill.fee_currency,
        executed_at=fill.executed_at,
    )

    return "fallback:" + sha256(
        material.encode("utf-8")
    ).hexdigest()


def _detect_fills(
    *,
    user_id: int,
    account_id: AccountId,
    instrument_id: InstrumentId,
    observed_at: datetime,
    local_orders: tuple[ExecutionOrder, ...],
    local_fills: tuple[ExecutionFill, ...],
    venue_fills: tuple[VenueFill, ...],
) -> list[ReconciliationDiscrepancy]:
    orders = {
        str(order.order_id): order
        for order in local_orders
    }

    local_keys: dict[str, int] = defaultdict(int)
    venue_keys: dict[str, int] = defaultdict(int)

    for fill in local_fills:
        order = orders.get(str(fill.order_id))

        if order is None:
            raise ReconciliationDetectionError(
                "local fill has no owning order in reconciliation scope"
            )

        _check_local_order_scope(
            order,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        local_keys[
            _local_fill_key(
                fill,
                order=order,
            )
        ] += 1

    for venue_fill in venue_fills:
        if venue_fill.account_id != account_id:
            raise ReconciliationDetectionError(
                "venue fill account outside reconciliation scope"
            )

        if venue_fill.instrument_id != instrument_id:
            raise ReconciliationDetectionError(
                "venue fill instrument outside reconciliation scope"
            )

        venue_keys[_venue_fill_key(venue_fill)] += 1

    result: list[ReconciliationDiscrepancy] = []

    for key in sorted(set(local_keys) | set(venue_keys)):
        local_count = local_keys.get(key, 0)
        venue_count = venue_keys.get(key, 0)

        if venue_count > local_count:
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .MISSING_LOCAL_FILL
                    ),
                    subject=ReconciliationSubject.FILL,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    venue_reference=key,
                    local_value=f"count={local_count}",
                    venue_value=f"count={venue_count}",
                )
            )

        if local_count > 1 or venue_count > 1:
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .DUPLICATE_OR_REPLAYED_FILL
                    ),
                    subject=ReconciliationSubject.FILL,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=(
                        key if local_count else None
                    ),
                    venue_reference=(
                        key if venue_count else None
                    ),
                    local_value=f"count={local_count}",
                    venue_value=f"count={venue_count}",
                )
            )

    return result


def _weighted_entry(
    values: list[tuple[Decimal, Decimal | None]],
) -> Decimal | None:
    active = [
        (quantity, price)
        for quantity, price in values
        if quantity > Decimal("0")
    ]

    if not active:
        return None

    if any(price is None for _, price in active):
        raise ReconciliationDetectionError(
            "active position lacks entry price"
        )

    quantity = sum(
        (item[0] for item in active),
        Decimal("0"),
    )

    weighted = sum(
        (
            item_quantity * item_price
            for item_quantity, item_price in active
            if item_price is not None
        ),
        Decimal("0"),
    )

    return weighted / quantity


def _detect_positions(
    *,
    user_id: int,
    account_id: AccountId,
    instrument_id: InstrumentId,
    observed_at: datetime,
    local_positions: tuple[PositionLeg, ...],
    venue_positions: tuple[VenuePosition, ...],
) -> list[ReconciliationDiscrepancy]:
    local_rows: dict[
        VenuePositionSide,
        list[tuple[Decimal, Decimal | None, str]],
    ] = defaultdict(list)

    venue_rows: dict[
        VenuePositionSide,
        list[tuple[Decimal, Decimal | None]],
    ] = defaultdict(list)

    for leg in local_positions:
        if leg.account_id != account_id:
            raise ReconciliationDetectionError(
                "PositionLeg account outside reconciliation scope"
            )

        if leg.instrument_id != instrument_id:
            raise ReconciliationDetectionError(
                "PositionLeg instrument outside reconciliation scope"
            )

        position_side = position_side_for_leg(leg.side)

        local_rows[position_side].append(
            (
                leg.current_quantity,
                leg.average_entry_price,
                f"{leg.group_id}:{leg.leg_id}",
            )
        )

    for position in venue_positions:
        if position.account_id != account_id:
            raise ReconciliationDetectionError(
                "venue position account outside reconciliation scope"
            )

        if position.instrument_id != instrument_id:
            raise ReconciliationDetectionError(
                "venue position instrument outside reconciliation scope"
            )

        venue_rows[position.side].append(
            (
                position.quantity,
                position.entry_price,
            )
        )

    result: list[ReconciliationDiscrepancy] = []

    for side in (
        VenuePositionSide.LONG,
        VenuePositionSide.SHORT,
    ):
        local_side_rows = local_rows.get(side, [])
        venue_side_rows = venue_rows.get(side, [])

        local_quantity = sum(
            (row[0] for row in local_side_rows),
            Decimal("0"),
        )
        venue_quantity = sum(
            (row[0] for row in venue_side_rows),
            Decimal("0"),
        )

        local_entry = _weighted_entry(
            [
                (row[0], row[1])
                for row in local_side_rows
            ]
        )
        venue_entry = _weighted_entry(
            list(venue_side_rows)
        )

        local_reference = ",".join(
            sorted(row[2] for row in local_side_rows)
        )

        if (
            local_quantity > Decimal("0")
            and venue_quantity == Decimal("0")
        ):
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .LOCAL_POSITION_MISSING_ON_VENUE
                    ),
                    subject=ReconciliationSubject.POSITION,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=local_reference,
                )
            )
            continue

        if (
            venue_quantity > Decimal("0")
            and local_quantity == Decimal("0")
        ):
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .VENUE_POSITION_MISSING_LOCALLY
                    ),
                    subject=ReconciliationSubject.POSITION,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    venue_reference=side.value,
                )
            )
            continue

        if local_quantity != venue_quantity:
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .POSITION_QUANTITY_DRIFT
                    ),
                    subject=ReconciliationSubject.POSITION,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=local_reference or None,
                    venue_reference=side.value,
                    local_value=_decimal_text(local_quantity),
                    venue_value=_decimal_text(venue_quantity),
                )
            )

        if (
            local_quantity > Decimal("0")
            and venue_quantity > Decimal("0")
            and local_entry is not None
            and venue_entry is not None
            and local_entry != venue_entry
        ):
            result.append(
                ReconciliationDiscrepancy(
                    kind=(
                        ReconciliationDiscrepancyKind
                        .POSITION_ENTRY_PRICE_DRIFT
                    ),
                    subject=ReconciliationSubject.POSITION,
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    observed_at=observed_at,
                    local_reference=local_reference or None,
                    venue_reference=side.value,
                    local_value=_decimal_text(local_entry),
                    venue_value=_decimal_text(venue_entry),
                )
            )

    local_active = {
        side
        for side, rows in local_rows.items()
        if sum(
            (row[0] for row in rows),
            Decimal("0"),
        ) > Decimal("0")
    }

    venue_active = {
        side
        for side, rows in venue_rows.items()
        if sum(
            (row[0] for row in rows),
            Decimal("0"),
        ) > Decimal("0")
    }

    if (
        len(local_active) == 1
        and len(venue_active) == 1
        and local_active != venue_active
    ):
        local_side = next(iter(local_active))
        venue_side = next(iter(venue_active))

        result.append(
            ReconciliationDiscrepancy(
                kind=(
                    ReconciliationDiscrepancyKind
                    .POSITION_SIDE_DRIFT
                ),
                subject=ReconciliationSubject.POSITION,
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
                observed_at=observed_at,
                local_value=local_side.value,
                venue_value=venue_side.value,
            )
        )

    return result


def _detect_account_observation(
    *,
    user_id: int,
    account_id: AccountId,
    venue_account: VenueAccountState | None,
) -> list[ReconciliationDiscrepancy]:
    if venue_account is None:
        return []

    if venue_account.account_id != account_id:
        raise ReconciliationDetectionError(
            "venue account observation outside reconciliation scope"
        )

    if (
        venue_account.state
        is VenueAccountObservationState.CURRENT
    ):
        return []

    if (
        venue_account.state
        is VenueAccountObservationState.STALE
    ):
        kind = (
            ReconciliationDiscrepancyKind
            .ACCOUNT_BALANCE_STALE
        )
    elif (
        venue_account.state
        is VenueAccountObservationState.UNAVAILABLE
    ):
        kind = (
            ReconciliationDiscrepancyKind
            .ACCOUNT_BALANCE_UNAVAILABLE
        )
    else:
        raise ReconciliationDetectionError(
            "unsupported venue account observation state"
        )

    return [
        ReconciliationDiscrepancy(
            kind=kind,
            subject=ReconciliationSubject.ACCOUNT,
            user_id=user_id,
            account_id=account_id,
            observed_at=venue_account.observed_at,
        )
    ]


def detect_reconciliation(
    *,
    user_id: int,
    account_id: AccountId,
    instrument_id: InstrumentId,
    source_state: ReconciliationSourceState,
    observed_at: datetime,
    local_orders: tuple[ExecutionOrder, ...],
    venue_orders: tuple[VenueOrderResult, ...],
    local_fills: tuple[ExecutionFill, ...],
    venue_fills: tuple[VenueFill, ...],
    local_positions: tuple[PositionLeg, ...],
    venue_positions: tuple[VenuePosition, ...],
    venue_account: VenueAccountState | None = None,
) -> ReconciliationResult:
    """Compare one canonical account/instrument reconciliation scope."""

    if account_id.venue_id != instrument_id.venue_id:
        raise ReconciliationDetectionError(
            "account venue must match instrument venue"
        )

    if source_state is not ReconciliationSourceState.CURRENT:
        discrepancy = ReconciliationDiscrepancy(
            kind=_SOURCE_KIND[source_state],
            subject=ReconciliationSubject.SOURCE,
            user_id=user_id,
            account_id=account_id,
            observed_at=observed_at,
        )

        return build_reconciliation_result(
            user_id=user_id,
            account_id=account_id,
            source_state=source_state,
            observed_at=observed_at,
            discrepancies=(discrepancy,),
        )

    discrepancies: list[ReconciliationDiscrepancy] = []

    discrepancies.extend(
        _detect_account_observation(
            user_id=user_id,
            account_id=account_id,
            venue_account=venue_account,
        )
    )

    discrepancies.extend(
        _detect_orders(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            observed_at=observed_at,
            local_orders=local_orders,
            venue_orders=venue_orders,
        )
    )

    discrepancies.extend(
        _detect_fills(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            observed_at=observed_at,
            local_orders=local_orders,
            local_fills=local_fills,
            venue_fills=venue_fills,
        )
    )

    discrepancies.extend(
        _detect_positions(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            observed_at=observed_at,
            local_positions=local_positions,
            venue_positions=venue_positions,
        )
    )

    return build_reconciliation_result(
        user_id=user_id,
        account_id=account_id,
        source_state=source_state,
        observed_at=observed_at,
        discrepancies=tuple(discrepancies),
    )
