from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from adapters.bybit.venue import BYBIT_VENUE_ID, BybitVenueAdapter
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

NOW = datetime(2026, 9, 15, 18, 0, tzinfo=UTC)
ACCOUNT = AccountId(BYBIT_VENUE_ID, 7)
INSTRUMENT = InstrumentId(
    venue_id=BYBIT_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
ORDER_ID = VenueOrderId("101")
CLIENT_ID = ClientOrderId("nexus-bybit-contract")


def _ok_list(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"retCode": 0, "retMsg": "OK", "result": {"list": rows}, "time": 1}


class ContractTransport:
    async def request(self, method: str, path: str, params: Mapping[str, str]) -> object:
        if path == "/v5/order/realtime" and method == "GET" and "orderId" in params:
            return _ok_list([
                {
                    "symbol": "BTCUSDT",
                    "orderId": "101",
                    "orderLinkId": CLIENT_ID.value,
                    "qty": "1",
                    "cumExecQty": "0",
                    "avgPrice": "",
                    "orderStatus": "New",
                }
            ])
        if path == "/v5/order/realtime":
            return _ok_list([
                {
                    "symbol": "BTCUSDT",
                    "orderId": "101",
                    "orderLinkId": CLIENT_ID.value,
                    "qty": "1",
                    "cumExecQty": "0",
                    "avgPrice": "",
                    "orderStatus": "New",
                }
            ])
        if path == "/v5/position/list":
            return _ok_list([
                {
                    "symbol": "BTCUSDT",
                    "positionIdx": 0,
                    "side": "Buy",
                    "size": "1",
                    "avgPrice": "60000",
                }
            ])
        if path == "/v5/account/wallet-balance":
            return _ok_list([
                {
                    "accountType": "UNIFIED",
                    "totalWalletBalance": "1000",
                    "totalAvailableBalance": "800",
                    "coin": [],
                }
            ])
        if path == "/v5/execution/list":
            return _ok_list([
                {
                    "symbol": "BTCUSDT",
                    "execId": "501",
                    "orderId": "101",
                    "orderLinkId": "",
                    "side": "Buy",
                    "execPrice": "60000",
                    "execQty": "0.25",
                    "execFee": "0",
                    "feeCurrency": "",
                    "execTime": 1789495200000,
                }
            ])
        raise AssertionError((method, path, params))


def test_bybit_passes_generic_venue_read_contract() -> None:
    async def scenario() -> None:
        adapter = BybitVenueAdapter(transport=ContractTransport(), clock=lambda: NOW)
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
                balances=(VenueBalance("USD", Decimal("1000"), Decimal("800")),),
                observed_at=NOW,
            ),
            fills=(
                VenueFill(
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    venue_fill_id=VenueFillId("501"),
                    venue_order_id=ORDER_ID,
                    client_order_id=None,
                    side=OrderSide.BUY,
                    quantity=Decimal("0.25"),
                    price=Decimal("60000"),
                    fee=Decimal("0"),
                    fee_currency=None,
                    executed_at=NOW,
                    observed_at=NOW,
                ),
            ),
        )
        await verify_venue_adapter_read_contract(adapter=adapter, case=case)

    asyncio.run(scenario())
