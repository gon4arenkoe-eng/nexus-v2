from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from adapters.binance.venue import (
    BINANCE_USDM_VENUE_ID,
    BinanceUsdMApiError,
    BinanceUsdMNormalizer,
    BinanceUsdMTestnetConfig,
    BinanceUsdMVenueAdapter,
)
from adapters.common.normalization import NormalizationEntity
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.venue import (
    VenueCapability,
    VenueOrderRequest,
    VenueOrderState,
    VenuePositionSide,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueOrderId,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(BINANCE_USDM_VENUE_ID, 7)
INSTRUMENT = InstrumentId(
    venue_id=BINANCE_USDM_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


class FakeTransport:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, Mapping[str, str]]] = []

    async def request(self, method: str, path: str, params: Mapping[str, str]) -> object:
        self.calls.append((method, path, dict(params)))
        if not self.responses:
            raise AssertionError("unexpected transport call")
        return self.responses.pop(0)


def test_normalizer_profile_covers_all_canonical_entities() -> None:
    profile = BinanceUsdMNormalizer().profile
    assert profile.venue_id == BINANCE_USDM_VENUE_ID
    assert profile.supported == frozenset(NormalizationEntity)


def test_config_is_testnet_only_and_fail_closed_to_oneway() -> None:
    assert BinanceUsdMTestnetConfig().environment == "TESTNET"
    with pytest.raises(ValueError, match="TESTNET only"):
        BinanceUsdMTestnetConfig(environment="LIVE")
    with pytest.raises(ValueError, match="ONEWAY"):
        BinanceUsdMTestnetConfig(position_mode="HEDGE")


def test_capabilities_are_explicit_and_do_not_claim_hedge_mode() -> None:
    adapter = BinanceUsdMVenueAdapter(transport=FakeTransport([]))
    for capability in (
        VenueCapability.ORDER_QUERY,
        VenueCapability.OPEN_ORDER_QUERY,
        VenueCapability.POSITION_QUERY,
        VenueCapability.ACCOUNT_QUERY,
        VenueCapability.FILL_QUERY,
    ):
        assert adapter.capabilities.supports(capability)
    assert not adapter.capabilities.supports(VenueCapability.HEDGE_MODE)


def test_reads_normalize_order_position_balance_and_fill() -> None:
    async def scenario() -> None:
        transport = FakeTransport(
            [
                {
                    "symbol": "BTCUSDT",
                    "orderId": 11,
                    "clientOrderId": "nexus-11",
                    "origQty": "1",
                    "executedQty": "0.25",
                    "avgPrice": "60000",
                    "status": "PARTIALLY_FILLED",
                },
                [
                    {
                        "symbol": "BTCUSDT",
                        "orderId": 12,
                        "clientOrderId": "nexus-12",
                        "origQty": "2",
                        "executedQty": "0",
                        "avgPrice": "0",
                        "status": "NEW",
                    }
                ],
                [
                    {
                        "symbol": "BTCUSDT",
                        "positionSide": "BOTH",
                        "positionAmt": "-0.5",
                        "entryPrice": "61000",
                    },
                    {
                        "symbol": "ETHUSDT",
                        "positionSide": "BOTH",
                        "positionAmt": "0",
                        "entryPrice": "0",
                    },
                ],
                [
                    {
                        "asset": "USDT",
                        "balance": "1000",
                        "availableBalance": "800",
                    }
                ],
                [
                    {
                        "symbol": "BTCUSDT",
                        "id": 99,
                        "orderId": 11,
                        "side": "BUY",
                        "price": "60000",
                        "qty": "0.25",
                        "commission": "0.1",
                        "commissionAsset": "USDT",
                        "time": 1789387200000,
                    }
                ],
            ]
        )
        adapter = BinanceUsdMVenueAdapter(transport=transport, clock=lambda: NOW)
        order = await adapter.get_order(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=VenueOrderId("11"),
        )
        assert order.state is VenueOrderState.PARTIALLY_FILLED
        assert order.filled_quantity == Decimal("0.25")
        open_orders = await adapter.get_open_orders(account_id=ACCOUNT, instrument_id=INSTRUMENT)
        assert open_orders[0].state is VenueOrderState.ACCEPTED
        positions = await adapter.get_positions(account_id=ACCOUNT)
        assert len(positions) == 1
        assert positions[0].side is VenuePositionSide.SHORT
        assert positions[0].quantity == Decimal("0.5")
        account = await adapter.get_account_state(account_id=ACCOUNT)
        assert account.balances[0].available == Decimal("800")
        fills = await adapter.get_fills(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            since=NOW,
        )
        assert fills[0].fee == Decimal("0.1")
        assert fills[0].fee_currency == "USDT"
        assert [call[1] for call in transport.calls] == [
            "/fapi/v1/order",
            "/fapi/v1/openOrders",
            "/fapi/v2/positionRisk",
            "/fapi/v2/balance",
            "/fapi/v1/userTrades",
        ]

    asyncio.run(scenario())


def test_filled_order_can_derive_average_price_from_cum_quote() -> None:
    result = BinanceUsdMNormalizer().normalize_order(
        {
            "orderId": 1,
            "clientOrderId": "c1",
            "origQty": "2",
            "executedQty": "2",
            "avgPrice": "0",
            "cumQuote": "120000",
            "status": "FILLED",
        }
    )
    assert result.state is VenueOrderState.FILLED
    assert result.average_fill_price == Decimal("60000")


def test_fill_query_requires_instrument_fail_closed() -> None:
    async def scenario() -> None:
        adapter = BinanceUsdMVenueAdapter(transport=FakeTransport([]), clock=lambda: NOW)
        with pytest.raises(ValueError, match="requires instrument_id"):
            await adapter.get_fills(account_id=ACCOUNT)

    asyncio.run(scenario())


def test_testnet_writes_disabled_by_default() -> None:
    async def scenario() -> None:
        adapter = BinanceUsdMVenueAdapter(transport=FakeTransport([]))
        request = VenueOrderRequest(
            client_order_id=ClientOrderId("nexus-write"),
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.MARKET,
        )
        with pytest.raises(PermissionError, match="TESTNET writes are disabled"):
            await adapter.submit_order(request)

    asyncio.run(scenario())


def test_opt_in_testnet_write_maps_canonical_order_without_position_side() -> None:
    async def scenario() -> None:
        transport = FakeTransport(
            [
                {
                    "symbol": "BTCUSDT",
                    "orderId": 13,
                    "clientOrderId": "nexus-write",
                    "origQty": "1",
                    "executedQty": "0",
                    "avgPrice": "0",
                    "status": "NEW",
                }
            ]
        )
        adapter = BinanceUsdMVenueAdapter(
            transport=transport,
            config=BinanceUsdMTestnetConfig(allow_testnet_writes=True),
        )
        request = VenueOrderRequest(
            client_order_id=ClientOrderId("nexus-write"),
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.LIMIT,
            limit_price=Decimal("59000"),
            reduce_only=True,
        )
        result = await adapter.submit_order(request)
        assert result.venue_order_id == VenueOrderId("13")
        params = transport.calls[0][2]
        assert params["newClientOrderId"] == "nexus-write"
        assert params["timeInForce"] == "GTC"
        assert params["reduceOnly"] == "true"
        assert "positionSide" not in params

    asyncio.run(scenario())


def test_binance_api_errors_are_normalized() -> None:
    async def scenario() -> None:
        adapter = BinanceUsdMVenueAdapter(
            transport=FakeTransport([{"code": -1021, "msg": "timestamp outside recvWindow"}])
        )
        with pytest.raises(BinanceUsdMApiError) as exc:
            await adapter.get_order(
                account_id=ACCOUNT,
                instrument_id=INSTRUMENT,
                venue_order_id=VenueOrderId("1"),
            )
        assert exc.value.code == -1021
        assert exc.value.retryable is True

    asyncio.run(scenario())
