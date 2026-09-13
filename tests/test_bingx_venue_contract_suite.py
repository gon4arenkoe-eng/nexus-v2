"""BingX adapter coverage against the reusable VenueAdapter read suite."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from apps.core.domain.orders import OrderSide
from apps.core.ports.venue import (
    VenueAccountState,
    VenueBalance,
    VenueFill,
    VenueOrderResult,
    VenueOrderState,
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
    VenueOrderId,
)
from packages.testkit.venue_adapter_contracts import (
    VenueAdapterReadContractCase,
    verify_venue_adapter_read_contract,
)


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(venue_id=BINGX_VENUE_ID, value=1)
INSTRUMENT = InstrumentId(
    venue_id=BINGX_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
ORDER_ID = VenueOrderId("101")
CLIENT_ID = ClientOrderId("nexus-contract")


class ContractTransport:
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
                    "clientOrderId": CLIENT_ID.value,
                    "origQty": "1",
                    "executedQty": "0",
                    "avgPrice": "0",
                    "status": "NEW",
                },
            }
        if path.endswith("/trade/openOrders"):
            return {
                "code": 0,
                "data": [
                    {
                        "orderId": 101,
                        "clientOrderId": CLIENT_ID.value,
                        "origQty": "1",
                        "executedQty": "0",
                        "avgPrice": "0",
                        "status": "NEW",
                    }
                ],
            }
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
                        "availableMargin": "800",
                    }
                },
            }
        if path.endswith("/trade/fillHistory"):
            return {
                "code": 0,
                "data": {
                    "fill_orders": [
                        {
                            "tradeId": "fill-1",
                            "orderId": 101,
                            "clientOrderId": CLIENT_ID.value,
                            "symbol": "BTC-USDT",
                            "side": "BUY",
                            "qty": "0.25",
                            "price": "60000",
                            "commission": "1",
                            "commissionAsset": "VST",
                            "time": 1789214400000,
                        }
                    ]
                },
            }
        raise AssertionError((method, path, params))


def test_bingx_passes_generic_venue_read_contract() -> None:
    async def scenario() -> None:
        adapter = BingXVenueAdapter(
            transport=ContractTransport(),
            clock=lambda: NOW,
        )
        case = VenueAdapterReadContractCase(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=ORDER_ID,
            since=NOW,
            order=VenueOrderResult(
                client_order_id=CLIENT_ID,
                venue_order_id=ORDER_ID,
                state=VenueOrderState.ACCEPTED,
                requested_quantity=Decimal("1"),
                filled_quantity=Decimal("0"),
            ),
            open_orders=(
                VenueOrderResult(
                    client_order_id=CLIENT_ID,
                    venue_order_id=ORDER_ID,
                    state=VenueOrderState.ACCEPTED,
                    requested_quantity=Decimal("1"),
                    filled_quantity=Decimal("0"),
                ),
            ),
            positions=(
                VenuePosition(
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    side=VenuePositionSide.LONG,
                    quantity=Decimal("1"),
                    entry_price=Decimal("60000"),
                    observed_at=NOW,
                ),
            ),
            account_state=VenueAccountState(
                account_id=ACCOUNT,
                balances=(
                    VenueBalance(
                        currency="VST",
                        total=Decimal("1000"),
                        available=Decimal("800"),
                    ),
                ),
                observed_at=NOW,
            ),
            fills=(
                VenueFill(
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    venue_fill_id=VenueFillId("fill-1"),
                    venue_order_id=ORDER_ID,
                    client_order_id=CLIENT_ID,
                    side=OrderSide.BUY,
                    quantity=Decimal("0.25"),
                    price=Decimal("60000"),
                    fee=Decimal("1"),
                    fee_currency="VST",
                    executed_at=NOW,
                    observed_at=NOW,
                ),
            ),
        )
        await verify_venue_adapter_read_contract(adapter=adapter, case=case)

    asyncio.run(scenario())
