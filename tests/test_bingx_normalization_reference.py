from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from apps.core.ports.venue import VenueCapability
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueOrderId,
)
from packages.testkit.venue_normalization_contracts import (
    assert_canonical_value_has_venue,
)


NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(venue_id=BINGX_VENUE_ID, value=1)
INSTRUMENT = InstrumentId(
    venue_id=BINGX_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
ORDER_ID = VenueOrderId("101")


class ReferenceTransport:
    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        if path.endswith("/trade/order") and method == "GET":
            return {
                "code": 0,
                "data": {
                    "orderId": 101,
                    "clientOrderId": "nexus-ref",
                    "origQty": "1",
                    "executedQty": "0",
                    "avgPrice": "0",
                    "status": "NEW",
                },
            }
        if path.endswith("/trade/openOrders"):
            return {"code": 0, "data": []}
        if path.endswith("/user/positions"):
            return {
                "code": 0,
                "data": [
                    {
                        "symbol": "BTC-USDT",
                        "positionSide": "LONG",
                        "positionAmt": "1",
                        "avgPrice": "60000",
                    }
                ],
            }
        if path.endswith("/user/balance"):
            return {
                "code": 0,
                "data": {
                    "balance": {
                        "asset": "VST",
                        "balance": "1000",
                        "availableMargin": "900",
                    }
                },
            }
        if path.endswith("/trade/allFillOrders"):
            return {
                "code": 0,
                "data": [
                    {
                        "tradeId": "fill-1",
                        "orderId": 101,
                        "clientOrderId": "nexus-ref",
                        "symbol": "BTC-USDT",
                        "side": "BUY",
                        "qty": "0.25",
                        "price": "60000",
                        "fee": "0",
                        "closeTime": 1789387200000,
                    }
                ],
            }
        raise AssertionError((method, path, params))


async def _snapshot(adapter: BingXVenueAdapter) -> tuple[object, ...]:
    order = await adapter.get_order(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        venue_order_id=ORDER_ID,
    )
    positions = await adapter.get_positions(account_id=ACCOUNT)
    account = await adapter.get_account_state(account_id=ACCOUNT)
    fills = await adapter.get_fills(
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        since=NOW,
    )
    return (order, *positions, account, *account.balances, *fills)


def test_bingx_reference_normalization_exposes_only_canonical_values() -> None:
    async def scenario() -> None:
        adapter = BingXVenueAdapter(transport=ReferenceTransport(), clock=lambda: NOW)
        required = (
            VenueCapability.ORDER_QUERY,
            VenueCapability.OPEN_ORDER_QUERY,
            VenueCapability.POSITION_QUERY,
            VenueCapability.ACCOUNT_QUERY,
            VenueCapability.FILL_QUERY,
        )
        for capability in required:
            adapter.capabilities.require(capability)
        for value in await _snapshot(adapter):
            assert_canonical_value_has_venue(value, venue_id=BINGX_VENUE_ID)

    asyncio.run(scenario())


def test_bingx_recreated_adapter_replays_same_canonical_snapshot() -> None:
    async def scenario() -> None:
        first = BingXVenueAdapter(transport=ReferenceTransport(), clock=lambda: NOW)
        second = BingXVenueAdapter(transport=ReferenceTransport(), clock=lambda: NOW)
        assert await _snapshot(first) == await _snapshot(second)

    asyncio.run(scenario())


def test_bingx_reference_quantities_remain_exact_decimals() -> None:
    async def scenario() -> None:
        adapter = BingXVenueAdapter(transport=ReferenceTransport(), clock=lambda: NOW)
        values = await _snapshot(adapter)
        quantities = [getattr(value, "quantity") for value in values if hasattr(value, "quantity")]
        assert Decimal("1") in quantities
        assert Decimal("0.25") in quantities

    asyncio.run(scenario())
