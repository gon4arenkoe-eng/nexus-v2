from __future__ import annotations

import asyncio
import inspect
from typing import Mapping

import pytest

from adapters.bybit.venue import BybitVenueAdapter
from packages.contracts.identities import (
    AccountId,
    ClientOrderId,
    VenueId,
    VenueOrderId,
)

BYBIT = VenueId("BYBIT")
ACCOUNT = AccountId(
    venue_id=BYBIT,
    value=7,
)


class ScriptedTransport:
    def __init__(
        self,
        responses: list[Mapping[str, object]],
    ) -> None:
        self.responses = list(responses)
        self.calls: list[
            tuple[str, str, dict[str, str]]
        ] = []

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> object:
        self.calls.append(
            (method, path, dict(params))
        )

        if not self.responses:
            raise AssertionError(
                "unexpected transport request"
            )

        return self.responses.pop(0)


def envelope(
    rows: list[Mapping[str, object]],
    *,
    cursor: str = "",
) -> Mapping[str, object]:
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "list": rows,
            "nextPageCursor": cursor,
        },
    }


def order_row(
    *,
    order_id: str = "1001",
    client_id: str = "client-1",
    status: str = "Filled",
) -> Mapping[str, object]:
    return {
        "orderId": order_id,
        "orderLinkId": client_id,
        "symbol": "BTCUSDT",
        "side": "Buy",
        "orderStatus": status,
        "qty": "1",
        "cumExecQty": "1",
        "avgPrice": "50000",
    }


def make_adapter(
    transport: ScriptedTransport,
) -> BybitVenueAdapter:
    return BybitVenueAdapter(
        transport=transport,
    )


def test_lookup_by_venue_order_id() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [order_row(order_id="1001")]
                )
            ]
        )

        result = await make_adapter(
            transport
        ).get_historical_order(
            account_id=ACCOUNT,
            venue_order_id=VenueOrderId("1001"),
        )

        assert (
            result.venue_order_id
            == VenueOrderId("1001")
        )

        assert transport.calls == [
            (
                "GET",
                "/v5/order/history",
                {
                    "category": "linear",
                    "settleCoin": "USDT",
                    "limit": "50",
                    "orderId": "1001",
                },
            )
        ]

    asyncio.run(scenario())


def test_lookup_by_client_order_id() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [order_row(client_id="client-7")]
                )
            ]
        )

        result = await make_adapter(
            transport
        ).get_historical_order(
            account_id=ACCOUNT,
            client_order_id=ClientOrderId(
                "client-7"
            ),
        )

        assert (
            result.client_order_id
            == ClientOrderId("client-7")
        )

        assert (
            transport.calls[0][2]["orderLinkId"]
            == "client-7"
        )

    asyncio.run(scenario())


def test_lookup_follows_cursor() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope([], cursor="page-2"),
                envelope(
                    [order_row(order_id="2001")]
                ),
            ]
        )

        result = await make_adapter(
            transport
        ).get_historical_order(
            account_id=ACCOUNT,
            venue_order_id=VenueOrderId("2001"),
        )

        assert (
            result.venue_order_id
            == VenueOrderId("2001")
        )
        assert len(transport.calls) == 2
        assert (
            transport.calls[1][2]["cursor"]
            == "page-2"
        )

    asyncio.run(scenario())


def test_missing_identity_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport([])

        with pytest.raises(
            ValueError,
            match="requires venue_order_id",
        ):
            await make_adapter(
                transport
            ).get_historical_order(
                account_id=ACCOUNT,
            )

        assert transport.calls == []

    asyncio.run(scenario())


def test_missing_order_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [envelope([])]
        )

        with pytest.raises(
            LookupError,
            match="not found",
        ):
            await make_adapter(
                transport
            ).get_historical_order(
                account_id=ACCOUNT,
                venue_order_id=VenueOrderId(
                    "missing"
                ),
            )

    asyncio.run(scenario())


def test_invalid_cursor_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                {
                    "retCode": 0,
                    "retMsg": "OK",
                    "result": {
                        "list": [order_row()],
                        "nextPageCursor": 123,
                    },
                }
            ]
        )

        with pytest.raises(
            ValueError,
            match="nextPageCursor must be a string",
        ):
            await make_adapter(
                transport
            ).get_historical_order(
                account_id=ACCOUNT,
                venue_order_id=VenueOrderId(
                    "1001"
                ),
            )

    asyncio.run(scenario())


def test_repeated_cursor_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope([], cursor="same"),
                envelope([], cursor="same"),
            ]
        )

        with pytest.raises(
            ValueError,
            match="cursor repeated",
        ):
            await make_adapter(
                transport
            ).get_historical_order(
                account_id=ACCOUNT,
                venue_order_id=VenueOrderId(
                    "1001"
                ),
            )

    asyncio.run(scenario())


def test_conflicting_identity_matches_fail_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [
                        order_row(
                            order_id="1001",
                            status="Filled",
                        ),
                        order_row(
                            order_id="1001",
                            status="Cancelled",
                        ),
                    ]
                )
            ]
        )

        with pytest.raises(
            ValueError,
            match="conflicting identity",
        ):
            await make_adapter(
                transport
            ).get_historical_order(
                account_id=ACCOUNT,
                venue_order_id=VenueOrderId(
                    "1001"
                ),
            )

    asyncio.run(scenario())


def test_historical_method_is_get_only() -> None:
    source = inspect.getsource(
        BybitVenueAdapter.get_historical_order
    )

    assert '"GET"' in source
    assert '"POST"' not in source
    assert "/v5/order/history" in source


def test_historical_method_stays_inside_adapter_boundary() -> None:
    source = inspect.getsource(
        BybitVenueAdapter.get_historical_order
    )

    assert "VenueOrderResult" in source
    assert "sqlalchemy" not in source.lower()
    assert "requests." not in source.lower()