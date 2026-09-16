from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from adapters.binance.venue import BINANCE_USDM_VENUE_ID, BinanceUsdMVenueAdapter
from apps.core.domain.orders import OrderSide
from apps.core.ports.venue import (
    VenueAccountState,
    VenueAccountObservationState,
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

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(BINANCE_USDM_VENUE_ID, 7)
INSTRUMENT = InstrumentId(
    venue_id=BINANCE_USDM_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
ORDER_ID = VenueOrderId("101")
CLIENT_ID = ClientOrderId("nexus-binance-contract")


class ContractTransport:
    async def request(self, method: str, path: str, params: Mapping[str, str]) -> object:
        if path == "/fapi/v1/order" and method == "GET":
            return {
                "symbol": "BTCUSDT",
                "orderId": 101,
                "clientOrderId": CLIENT_ID.value,
                "origQty": "1",
                "executedQty": "0",
                "avgPrice": "0",
                "status": "NEW",
            }
        if path == "/fapi/v1/openOrders":
            return [
                {
                    "symbol": "BTCUSDT",
                    "orderId": 101,
                    "clientOrderId": CLIENT_ID.value,
                    "origQty": "1",
                    "executedQty": "0",
                    "avgPrice": "0",
                    "status": "NEW",
                }
            ]
        if path == "/fapi/v2/positionRisk":
            return [
                {
                    "symbol": "BTCUSDT",
                    "positionSide": "BOTH",
                    "positionAmt": "1",
                    "entryPrice": "60000",
                }
            ]
        if path == "/fapi/v2/balance":
            return [{"asset": "USDT", "balance": "1000", "availableBalance": "800"}]
        if path == "/fapi/v1/userTrades":
            return [
                {
                    "symbol": "BTCUSDT",
                    "id": 501,
                    "orderId": 101,
                    "side": "BUY",
                    "price": "60000",
                    "qty": "0.25",
                    "commission": "0",
                    "commissionAsset": "USDT",
                    "time": 1789387200000,
                }
            ]
        raise AssertionError((method, path, params))


def test_binance_usdm_passes_generic_venue_read_contract() -> None:
    async def scenario() -> None:
        adapter = BinanceUsdMVenueAdapter(transport=ContractTransport(), clock=lambda: NOW)
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
                state=VenueAccountObservationState.CURRENT,
                balances=(VenueBalance("USDT", Decimal("1000"), Decimal("800")),),
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
