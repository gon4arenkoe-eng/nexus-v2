"""BingX DEMO adapter normalization and safety tests."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from adapters.bingx.venue import (
    BINGX_VENUE_ID,
    BingXApiError,
    BingXDemoConfig,
    BingXVenueAdapter,
)
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
    VenueId,
    VenueOrderId,
)


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(venue_id=BINGX_VENUE_ID, value=7)
INSTRUMENT = InstrumentId(
    venue_id=BINGX_VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


class ScriptedTransport:
    def __init__(self, *responses: Mapping[str, object]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, Mapping[str, str]]] = []

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        self.calls.append((method, path, dict(params)))
        if not self.responses:
            raise AssertionError("transport response sequence exhausted")
        return self.responses.pop(0)


def _adapter(
    transport: ScriptedTransport,
    *,
    writes: bool = False,
) -> BingXVenueAdapter:
    return BingXVenueAdapter(
        transport=transport,
        config=BingXDemoConfig(allow_demo_writes=writes),
        clock=lambda: NOW,
    )


def _market_request(*, reduce_only: bool = False) -> VenueOrderRequest:
    return VenueOrderRequest(
        client_order_id=ClientOrderId("nexus-1"),
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=OrderSide.SELL if reduce_only else OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
        reduce_only=reduce_only,
    )


def test_capabilities_cover_shared_reconciliation_reads() -> None:
    adapter = _adapter(ScriptedTransport())
    for capability in (
        VenueCapability.ORDER_QUERY,
        VenueCapability.OPEN_ORDER_QUERY,
        VenueCapability.POSITION_QUERY,
        VenueCapability.ACCOUNT_QUERY,
        VenueCapability.FILL_QUERY,
        VenueCapability.HEDGE_MODE,
    ):
        assert adapter.capabilities.supports(capability)


def test_real_environment_is_rejected() -> None:
    with pytest.raises(ValueError, match="DEMO environment only"):
        BingXDemoConfig(environment="REAL")


def test_demo_writes_fail_closed_until_explicitly_enabled() -> None:
    async def scenario() -> None:
        adapter = _adapter(ScriptedTransport())
        with pytest.raises(PermissionError, match="explicit enablement"):
            await adapter.submit_order(_market_request())

    asyncio.run(scenario())


def test_submit_maps_canonical_market_order_to_bingx_hedge_order() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {"code": 0, "data": {"orderId": 123, "clientOrderId": "nexus-1"}}
        )
        result = await _adapter(transport, writes=True).submit_order(
            _market_request()
        )
        assert result.state is VenueOrderState.ACCEPTED
        assert result.venue_order_id == VenueOrderId("123")
        method, path, params = transport.calls[0]
        assert method == "POST"
        assert path == "/openApi/swap/v2/trade/order"
        assert params == {
            "symbol": "BTC-USDT",
            "side": "BUY",
            "positionSide": "LONG",
            "type": "MARKET",
            "quantity": "0.01",
            "clientOrderId": "nexus-1",
        }

    asyncio.run(scenario())


def test_reduce_only_sell_targets_long_position() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport({"code": 0, "data": {"orderId": 124}})
        await _adapter(transport, writes=True).submit_order(
            _market_request(reduce_only=True)
        )
        params = transport.calls[0][2]
        assert params["side"] == "SELL"
        assert params["positionSide"] == "LONG"
        assert params["reduceOnly"] == "true"

    asyncio.run(scenario())


def test_get_order_normalizes_filled_order() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {
                "code": 0,
                "data": {
                    "orderId": 123,
                    "clientOrderId": "nexus-1",
                    "origQty": "0.01",
                    "executedQty": "0.01",
                    "avgPrice": "60000",
                    "status": "FILLED",
                },
            }
        )
        result = await _adapter(transport).get_order(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=VenueOrderId("123"),
        )
        assert result.state is VenueOrderState.FILLED
        assert result.filled_quantity == Decimal("0.01")
        assert result.average_fill_price == Decimal("60000")

    asyncio.run(scenario())


def test_unknown_order_status_remains_explicit_unknown() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {
                "code": 0,
                "data": {
                    "orderId": 123,
                    "origQty": "1",
                    "executedQty": "0",
                    "status": "VENUE_NEW_STATE",
                },
            }
        )
        result = await _adapter(transport).get_order(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=VenueOrderId("123"),
        )
        assert result.state is VenueOrderState.UNKNOWN
        assert result.client_order_id == ClientOrderId("venue:123")

    asyncio.run(scenario())


def test_positions_preserve_hedge_side_identity() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {
                "code": 0,
                "data": [
                    {
                        "symbol": "BTC-USDT",
                        "positionSide": "LONG",
                        "positionAmt": "0.4",
                        "avgPrice": "60000",
                    },
                    {
                        "symbol": "BTC-USDT",
                        "positionSide": "SHORT",
                        "positionAmt": "-0.2",
                        "avgPrice": "61000",
                    },
                ],
            }
        )
        positions = await _adapter(transport).get_positions(account_id=ACCOUNT)
        assert tuple(item.side for item in positions) == (
            VenuePositionSide.LONG,
            VenuePositionSide.SHORT,
        )
        assert tuple(item.quantity for item in positions) == (
            Decimal("0.4"),
            Decimal("0.2"),
        )

    asyncio.run(scenario())


def test_demo_vst_balance_remains_vst_canonical_asset() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {
                "code": 0,
                "data": {
                    "balance": {
                        "asset": "VST",
                        "balance": "100000",
                        "availableMargin": "90000",
                    }
                },
            }
        )
        state = await _adapter(transport).get_account_state(account_id=ACCOUNT)
        assert state.balances[0].currency == "VST"
        assert state.balances[0].total == Decimal("100000")
        assert state.balances[0].available == Decimal("90000")
        assert state.observed_at == NOW

    asyncio.run(scenario())


def test_fill_history_normalizes_fill_identity_and_fee() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {
                "code": 0,
                "data": {
                    "fill_orders": [
                        {
                            "tradeId": 55,
                            "orderId": 123,
                            "clientOrderId": "nexus-1",
                            "symbol": "BTC-USDT",
                            "side": "BUY",
                            "qty": "0.01",
                            "price": "60000",
                            "commission": "0.2",
                            "commissionAsset": "USDT",
                            "time": 1789214400000,
                        }
                    ]
                },
            }
        )
        fills = await _adapter(transport).get_fills(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            since=datetime(2026, 9, 12, 11, 0, tzinfo=UTC),
        )
        assert len(fills) == 1
        fill = fills[0]
        assert fill.venue_fill_id is not None
        assert fill.venue_fill_id.value == "55"
        assert fill.venue_order_id == VenueOrderId("123")
        assert fill.quantity == Decimal("0.01")
        assert fill.fee == Decimal("0.2")
        assert fill.fee_currency == "USDT"

    asyncio.run(scenario())


def test_fill_query_requires_instrument_fail_closed() -> None:
    async def scenario() -> None:
        with pytest.raises(ValueError, match="requires instrument_id"):
            await _adapter(ScriptedTransport()).get_fills(account_id=ACCOUNT)

    asyncio.run(scenario())


def test_rate_limit_error_is_classified_retryable() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            {"code": 100410, "msg": "rate limit exceeded", "data": {}}
        )
        with pytest.raises(BingXApiError) as error:
            await _adapter(transport).get_positions(account_id=ACCOUNT)
        assert error.value.code == 100410
        assert error.value.retryable is True

    asyncio.run(scenario())


def test_wrong_venue_identity_fails_closed_before_transport() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport()
        other = AccountId(venue_id=VenueId("OTHER"), value=1)
        with pytest.raises(ValueError, match="belong to BINGX"):
            await _adapter(transport).get_positions(account_id=other)
        assert transport.calls == []

    asyncio.run(scenario())
