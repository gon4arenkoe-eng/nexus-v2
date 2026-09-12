"""Reusable canonical VenueAdapter reconciliation contract checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.core.ports.venue import (
    VenueAccountState,
    VenueAdapter,
    VenueCapability,
    VenueFill,
    VenueOrderResult,
    VenuePosition,
)
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
    VenueOrderId,
)


@dataclass(frozen=True, slots=True)
class VenueAdapterReadContractCase:
    """Expected canonical reads for one deterministic adapter case."""

    account_id: AccountId
    instrument_id: InstrumentId
    venue_order_id: VenueOrderId
    since: datetime
    order: VenueOrderResult
    open_orders: tuple[VenueOrderResult, ...]
    positions: tuple[VenuePosition, ...]
    account_state: VenueAccountState
    fills: tuple[VenueFill, ...]


async def verify_venue_adapter_read_contract(
    *,
    adapter: VenueAdapter,
    case: VenueAdapterReadContractCase,
) -> None:
    """Verify the common reconciliation read contract."""

    required = (
        VenueCapability.ORDER_QUERY,
        VenueCapability.OPEN_ORDER_QUERY,
        VenueCapability.POSITION_QUERY,
        VenueCapability.ACCOUNT_QUERY,
        VenueCapability.FILL_QUERY,
    )

    for capability in required:
        adapter.capabilities.require(capability)

    order = await adapter.get_order(
        account_id=case.account_id,
        instrument_id=case.instrument_id,
        venue_order_id=case.venue_order_id,
    )

    open_orders = await adapter.get_open_orders(
        account_id=case.account_id,
        instrument_id=case.instrument_id,
    )

    positions = await adapter.get_positions(
        account_id=case.account_id,
    )

    account_state = await adapter.get_account_state(
        account_id=case.account_id,
    )

    fills = await adapter.get_fills(
        account_id=case.account_id,
        instrument_id=case.instrument_id,
        since=case.since,
    )

    assert order == case.order
    assert open_orders == case.open_orders
    assert positions == case.positions
    assert account_state == case.account_state
    assert fills == case.fills
