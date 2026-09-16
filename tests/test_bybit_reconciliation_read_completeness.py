"""Bybit reconciliation read-completeness edge cases."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Mapping

import pytest

from adapters.bybit.venue import (
    BybitVenueAdapter,
)


NOW = datetime(
    2026,
    9,
    16,
    12,
    0,
    tzinfo=UTC,
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
    ) -> Mapping[str, object]:
        self.calls.append(
            (
                method,
                path,
                dict(params),
            )
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


def adapter(
    transport: ScriptedTransport,
) -> BybitVenueAdapter:
    return BybitVenueAdapter(
        transport=transport,
        clock=lambda: NOW,
    )


def result_rows(
    response: Mapping[str, object],
) -> list[Mapping[str, object]]:
    result = response["result"]

    assert isinstance(result, Mapping)

    rows = result["list"]

    assert isinstance(rows, list)

    return rows


def test_open_order_cursor_traversal_uses_bybit_max_page_size() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [{"orderId": "1"}],
                    cursor="cursor-2",
                ),
                envelope(
                    [{"orderId": "2"}],
                ),
            ]
        )

        response = await adapter(
            transport
        )._request_complete_read(
            "GET",
            "/v5/order/realtime",
            {
                "category": "linear",
                "symbol": "BTCUSDT",
            },
        )

        assert result_rows(response) == [
            {"orderId": "1"},
            {"orderId": "2"},
        ]

        assert transport.calls == [
            (
                "GET",
                "/v5/order/realtime",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "limit": "50",
                },
            ),
            (
                "GET",
                "/v5/order/realtime",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "limit": "50",
                    "cursor": "cursor-2",
                },
            ),
        ]

    asyncio.run(scenario())


def test_position_cursor_traversal_uses_bybit_max_page_size() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [{"symbol": "BTCUSDT"}],
                    cursor="positions-2",
                ),
                envelope(
                    [{"symbol": "ETHUSDT"}],
                ),
            ]
        )

        response = await adapter(
            transport
        )._request_complete_read(
            "GET",
            "/v5/position/list",
            {
                "category": "linear",
                "settleCoin": "USDT",
            },
        )

        assert len(result_rows(response)) == 2

        assert transport.calls[0][2]["limit"] == "200"
        assert (
            transport.calls[1][2]["cursor"]
            == "positions-2"
        )

    asyncio.run(scenario())


def test_execution_cursor_traversal_uses_bybit_max_page_size() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope(
                    [{"execId": "e2"}],
                    cursor="fills-2",
                ),
                envelope(
                    [{"execId": "e1"}],
                ),
            ]
        )

        response = await adapter(
            transport
        )._request_complete_read(
            "GET",
            "/v5/execution/list",
            {
                "category": "linear",
                "symbol": "BTCUSDT",
            },
        )

        assert result_rows(response) == [
            {"execId": "e2"},
            {"execId": "e1"},
        ]

        assert transport.calls[0][2]["limit"] == "100"
        assert transport.calls[1][2]["cursor"] == "fills-2"

    asyncio.run(scenario())


def test_execution_history_is_split_into_non_overlapping_seven_day_windows() -> None:
    async def scenario() -> None:
        since_ms = int(
            datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=UTC,
            ).timestamp()
            * 1000
        )

        transport = ScriptedTransport(
            [
                envelope([{"execId": "new"}]),
                envelope([{"execId": "middle"}]),
                envelope([{"execId": "old"}]),
            ]
        )

        response = await adapter(
            transport
        )._request_complete_read(
            "GET",
            "/v5/execution/list",
            {
                "category": "linear",
                "symbol": "BTCUSDT",
                "startTime": str(since_ms),
            },
        )

        assert [
            row["execId"]
            for row in result_rows(response)
        ] == [
            "new",
            "middle",
            "old",
        ]

        assert len(transport.calls) == 3

        seven_days_ms = (
            7 * 24 * 60 * 60 * 1000
        )

        windows: list[tuple[int, int]] = []

        for method, path, params in transport.calls:
            assert method == "GET"
            assert path == "/v5/execution/list"
            assert params["limit"] == "100"

            start = int(params["startTime"])
            end = int(params["endTime"])

            assert end >= start
            assert end - start <= seven_days_ms

            windows.append((start, end))

        # Newest -> oldest, with no inclusive-ms overlap.
        for newer, older in zip(
            windows,
            windows[1:],
        ):
            newer_start, _ = newer
            _, older_end = older

            assert older_end == newer_start - 1

        assert windows[-1][0] == since_ms

    asyncio.run(scenario())


def test_duplicate_execution_at_window_boundary_is_deduplicated() -> None:
    async def scenario() -> None:
        since_ms = int(
            datetime(
                2026,
                9,
                8,
                0,
                0,
                tzinfo=UTC,
            ).timestamp()
            * 1000
        )

        duplicate = {
            "execId": "same-exec",
            "orderId": "order-1",
        }

        transport = ScriptedTransport(
            [
                envelope([duplicate]),
                envelope([duplicate]),
            ]
        )

        response = await adapter(
            transport
        )._request_complete_read(
            "GET",
            "/v5/execution/list",
            {
                "category": "linear",
                "symbol": "BTCUSDT",
                "startTime": str(since_ms),
            },
        )

        assert result_rows(response) == [duplicate]

    asyncio.run(scenario())


def test_conflicting_duplicate_execution_fails_closed() -> None:
    async def scenario() -> None:
        since_ms = int(
            datetime(
                2026,
                9,
                8,
                0,
                0,
                tzinfo=UTC,
            ).timestamp()
            * 1000
        )

        transport = ScriptedTransport(
            [
                envelope(
                    [
                        {
                            "execId": "same-exec",
                            "orderId": "order-1",
                        }
                    ]
                ),
                envelope(
                    [
                        {
                            "execId": "same-exec",
                            "orderId": "DIFFERENT",
                        }
                    ]
                ),
            ]
        )

        with pytest.raises(
            ValueError,
            match="conflicting duplicate execId",
        ):
            await adapter(
                transport
            )._request_complete_read(
                "GET",
                "/v5/execution/list",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "startTime": str(since_ms),
                },
            )

    asyncio.run(scenario())


def test_repeated_cursor_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                envelope([], cursor="repeat"),
                envelope([], cursor="repeat"),
            ]
        )

        with pytest.raises(
            ValueError,
            match="pagination cursor repeated",
        ):
            await adapter(
                transport
            )._request_complete_read(
                "GET",
                "/v5/order/realtime",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                },
            )

    asyncio.run(scenario())


def test_non_string_cursor_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport(
            [
                {
                    "retCode": 0,
                    "retMsg": "OK",
                    "result": {
                        "list": [],
                        "nextPageCursor": 123,
                    },
                }
            ]
        )

        with pytest.raises(
            ValueError,
            match="nextPageCursor must be a string",
        ):
            await adapter(
                transport
            )._request_complete_read(
                "GET",
                "/v5/order/realtime",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                },
            )

    asyncio.run(scenario())


def test_future_execution_start_time_fails_closed() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport([])

        future_ms = int(
            datetime(
                2026,
                9,
                17,
                12,
                0,
                tzinfo=UTC,
            ).timestamp()
            * 1000
        )

        with pytest.raises(
            ValueError,
            match="cannot be in the future",
        ):
            await adapter(
                transport
            )._request_complete_read(
                "GET",
                "/v5/execution/list",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "startTime": str(future_ms),
                },
            )

        assert transport.calls == []

    asyncio.run(scenario())


def test_complete_read_is_get_only() -> None:
    async def scenario() -> None:
        transport = ScriptedTransport([])

        with pytest.raises(
            PermissionError,
            match="GET-only",
        ):
            await adapter(
                transport
            )._request_complete_read(
                "POST",
                "/v5/order/realtime",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                },
            )

        assert transport.calls == []

    asyncio.run(scenario())


def test_public_reconciliation_reads_route_through_completeness_layer() -> None:
    import inspect

    for method in (
        BybitVenueAdapter.get_open_orders,
        BybitVenueAdapter.get_positions,
        BybitVenueAdapter.get_fills,
    ):
        source = inspect.getsource(method)

        assert "self._request_complete_read(" in source
        assert "self._transport.request(" not in source
