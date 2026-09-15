from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from adapters.bybit.venue import (
    BYBIT_VENUE_ID,
    BybitApiError,
    BybitDemoConfig,
    BybitNormalizer,
    BybitVenueAdapter,
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

NOW = datetime(2026, 9, 15, 18, 0, tzinfo=UTC)
ACCOUNT = AccountId(BYBIT_VENUE_ID, 7)
INSTRUMENT = InstrumentId(
    venue_id=BYBIT_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _ok_list(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"retCode": 0, "retMsg": "OK", "result": {"list": rows}, "time": 1}


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
    profile = BybitNormalizer().profile
    assert profile.venue_id == BYBIT_VENUE_ID
    assert profile.supported == frozenset(NormalizationEntity)


def test_config_is_demo_only_oneway_and_usdt_only() -> None:
    assert BybitDemoConfig().environment == "DEMO"
    with pytest.raises(ValueError, match="DEMO only"):
        BybitDemoConfig(environment="LIVE")
    with pytest.raises(ValueError, match="ONEWAY"):
        BybitDemoConfig(position_mode="HEDGE")
    with pytest.raises(ValueError, match="USDT"):
        BybitDemoConfig(settle_coin="USDC")


def test_capabilities_are_explicit_and_do_not_claim_hedge_mode() -> None:
    adapter = BybitVenueAdapter(transport=FakeTransport([]))
    for capability in (
        VenueCapability.ORDER_QUERY,
        VenueCapability.OPEN_ORDER_QUERY,
        VenueCapability.POSITION_QUERY,
        VenueCapability.ACCOUNT_QUERY,
        VenueCapability.FILL_QUERY,
    ):
        assert adapter.capabilities.supports(capability)
    assert not adapter.capabilities.supports(VenueCapability.HEDGE_MODE)


def test_reads_normalize_bybit_v5_envelopes() -> None:
    async def scenario() -> None:
        transport = FakeTransport(
            [
                _ok_list([
                    {
                        "symbol": "BTCUSDT",
                        "orderId": "11",
                        "orderLinkId": "nexus-11",
                        "qty": "1",
                        "cumExecQty": "0.25",
                        "avgPrice": "60000",
                        "orderStatus": "PartiallyFilled",
                    }
                ]),
                _ok_list([
                    {
                        "symbol": "BTCUSDT",
                        "orderId": "12",
                        "orderLinkId": "nexus-12",
                        "qty": "2",
                        "cumExecQty": "0",
                        "avgPrice": "",
                        "orderStatus": "New",
                    }
                ]),
                _ok_list([
                    {
                        "symbol": "BTCUSDT",
                        "positionIdx": 0,
                        "side": "Sell",
                        "size": "0.5",
                        "avgPrice": "61000",
                    },
                    {
                        "symbol": "ETHUSDT",
                        "positionIdx": 0,
                        "side": "",
                        "size": "0",
                        "avgPrice": "",
                    },
                ]),
                _ok_list([
                    {
                        "accountType": "UNIFIED",
                        "totalWalletBalance": "1000",
                        "totalAvailableBalance": "800",
                        "coin": [],
                    }
                ]),
                _ok_list([
                    {
                        "symbol": "BTCUSDT",
                        "execId": "99",
                        "orderId": "11",
                        "orderLinkId": "nexus-11",
                        "side": "Buy",
                        "execPrice": "60000",
                        "execQty": "0.25",
                        "execFee": "0.1",
                        "feeCurrency": "USDT",
                        "execTime": 1789495200000,
                    }
                ]),
            ]
        )
        adapter = BybitVenueAdapter(transport=transport, clock=lambda: NOW)
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
        assert account.balances[0].currency == "USD"
        assert account.balances[0].available == Decimal("800")
        fills = await adapter.get_fills(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            since=NOW,
        )
        assert fills[0].fee == Decimal("0.1")
        assert fills[0].fee_currency == "USDT"
        assert [call[1] for call in transport.calls] == [
            "/v5/order/realtime",
            "/v5/order/realtime",
            "/v5/position/list",
            "/v5/account/wallet-balance",
            "/v5/execution/list",
        ]

    asyncio.run(scenario())


def test_position_idx_hedge_mode_fails_closed() -> None:
    context = __import__("adapters.common.normalization", fromlist=["PositionNormalizationContext"]).PositionNormalizationContext(
        account_id=ACCOUNT, observed_at=NOW
    )
    with pytest.raises(ValueError, match="positionIdx=0"):
        BybitNormalizer().normalize_position(
            {
                "symbol": "BTCUSDT",
                "positionIdx": 1,
                "side": "Buy",
                "size": "1",
                "avgPrice": "60000",
            },
            context=context,
        )


def test_filled_order_can_derive_average_price_from_cum_exec_value() -> None:
    result = BybitNormalizer().normalize_order(
        {
            "orderId": "1",
            "orderLinkId": "c1",
            "qty": "2",
            "cumExecQty": "2",
            "avgPrice": "",
            "cumExecValue": "120000",
            "orderStatus": "Filled",
        }
    )
    assert result.state is VenueOrderState.FILLED
    assert result.average_fill_price == Decimal("60000")


def test_fill_query_requires_instrument_fail_closed() -> None:
    async def scenario() -> None:
        adapter = BybitVenueAdapter(transport=FakeTransport([]), clock=lambda: NOW)
        with pytest.raises(ValueError, match="requires instrument_id"):
            await adapter.get_fills(account_id=ACCOUNT)

    asyncio.run(scenario())


def test_demo_writes_disabled_by_default() -> None:
    async def scenario() -> None:
        adapter = BybitVenueAdapter(transport=FakeTransport([]))
        request = VenueOrderRequest(
            client_order_id=ClientOrderId("nexus-write"),
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.MARKET,
        )
        with pytest.raises(PermissionError, match="DEMO writes are disabled"):
            await adapter.submit_order(request)

    asyncio.run(scenario())


def test_opt_in_demo_submit_confirms_state_with_readback() -> None:
    async def scenario() -> None:
        transport = FakeTransport(
            [
                {"retCode": 0, "retMsg": "OK", "result": {"orderId": "13", "orderLinkId": "nexus-write"}},
                _ok_list([
                    {
                        "symbol": "BTCUSDT",
                        "orderId": "13",
                        "orderLinkId": "nexus-write",
                        "qty": "1",
                        "cumExecQty": "0",
                        "avgPrice": "",
                        "orderStatus": "New",
                    }
                ]),
            ]
        )
        adapter = BybitVenueAdapter(
            transport=transport,
            config=BybitDemoConfig(allow_demo_writes=True),
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
        assert result.state is VenueOrderState.ACCEPTED
        assert [call[1] for call in transport.calls] == [
            "/v5/order/create",
            "/v5/order/realtime",
        ]
        create_params = transport.calls[0][2]
        assert create_params["orderLinkId"] == "nexus-write"
        assert create_params["timeInForce"] == "GTC"
        assert create_params["reduceOnly"] == "true"
        assert create_params["positionIdx"] == "0"

    asyncio.run(scenario())


def test_bybit_api_errors_are_normalized() -> None:
    async def scenario() -> None:
        adapter = BybitVenueAdapter(
            transport=FakeTransport([
                {"retCode": 10002, "retMsg": "request time exceeds window", "result": {}}
            ])
        )
        with pytest.raises(BybitApiError) as exc:
            await adapter.get_order(
                account_id=ACCOUNT,
                instrument_id=INSTRUMENT,
                venue_order_id=VenueOrderId("1"),
            )
        assert exc.value.code == 10002
        assert exc.value.retryable is True

    asyncio.run(scenario())
