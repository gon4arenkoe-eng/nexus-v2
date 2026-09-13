"""BingX VST controlled-write transport safety tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from urllib.error import URLError

import pytest

from adapters.bingx.http_transport import (
    FALLBACK_VST_BASE_URL,
    PRIMARY_VST_BASE_URL,
    BingXVstControlledWriteHttpTransport,
    BingXVstHttpConfig,
)


NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
ORDER_PATH = "/openApi/swap/v2/trade/order"


def _transport() -> BingXVstControlledWriteHttpTransport:
    return BingXVstControlledWriteHttpTransport(
        config=BingXVstHttpConfig(
            api_key="test-key",
            secret_key="test-secret",
        ),
        clock=lambda: NOW,
    )


def test_controlled_transport_uses_vst_only() -> None:
    assert "vst" in PRIMARY_VST_BASE_URL
    assert "vst" in FALLBACK_VST_BASE_URL
    assert PRIMARY_VST_BASE_URL.startswith("https://")
    assert FALLBACK_VST_BASE_URL.startswith("https://")


def test_controlled_transport_rejects_unknown_method_before_network() -> None:
    async def scenario() -> None:
        with pytest.raises(PermissionError, match="rejects method"):
            await _transport().request("PATCH", ORDER_PATH, {})

    asyncio.run(scenario())


def test_controlled_transport_rejects_non_openapi_path_before_network() -> None:
    async def scenario() -> None:
        with pytest.raises(ValueError, match="must start"):
            await _transport().request("POST", "/unsafe/order", {})

    asyncio.run(scenario())


def test_controlled_transport_rejects_other_write_endpoint_before_network() -> None:
    async def scenario() -> None:
        with pytest.raises(PermissionError, match="write endpoint"):
            await _transport().request(
                "POST",
                "/openApi/swap/v2/trade/closeAllPositions",
                {},
            )

    asyncio.run(scenario())


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_controlled_transport_allows_only_order_write_path(
    monkeypatch,
    method: str,
) -> None:
    transport = _transport()
    calls: list[tuple[str, str]] = []

    def fake_request_once(*, method: str, url: str):
        calls.append((method, url))
        return {"code": 0, "data": {}}

    monkeypatch.setattr(
        transport._delegate,
        "_request_once",
        fake_request_once,
    )

    async def scenario() -> None:
        response = await transport.request(
            method,
            ORDER_PATH,
            {"symbol": "BTC-USDT"},
        )
        assert response["code"] == 0

    asyncio.run(scenario())

    assert len(calls) == 1
    called_method, url = calls[0]
    assert called_method == method
    assert url.startswith(PRIMARY_VST_BASE_URL + ORDER_PATH + "?")
    assert "recvWindow=5000" in url
    assert "symbol=BTC-USDT" in url
    assert "timestamp=" in url
    assert "signature=" in url


def test_controlled_write_falls_back_only_after_network_failure(
    monkeypatch,
) -> None:
    transport = _transport()
    calls: list[str] = []

    def fake_request_once(*, method: str, url: str):
        assert method == "POST"
        calls.append(url)
        if len(calls) == 1:
            raise URLError("network down")
        return {"code": 0, "data": {}}

    monkeypatch.setattr(
        transport._delegate,
        "_request_once",
        fake_request_once,
    )

    async def scenario() -> None:
        response = await transport.request(
            "POST",
            ORDER_PATH,
            {"symbol": "BTC-USDT"},
        )
        assert response["code"] == 0

    asyncio.run(scenario())

    assert calls[0].startswith(PRIMARY_VST_BASE_URL)
    assert calls[1].startswith(FALLBACK_VST_BASE_URL)


def test_get_remains_available_through_readonly_delegate(
    monkeypatch,
) -> None:
    transport = _transport()
    calls: list[tuple[str, str]] = []

    def fake_request_once(*, method: str, url: str):
        calls.append((method, url))
        return {"code": 0, "data": {}}

    monkeypatch.setattr(
        transport._delegate,
        "_request_once",
        fake_request_once,
    )

    async def scenario() -> None:
        response = await transport.request(
            "GET",
            "/openApi/swap/v2/trade/openOrders",
            {"symbol": "BTC-USDT"},
        )
        assert response["code"] == 0

    asyncio.run(scenario())

    assert calls[0][0] == "GET"
    assert calls[0][1].startswith(PRIMARY_VST_BASE_URL)


def test_transport_source_contains_no_real_base_url() -> None:
    import adapters.bingx.http_transport as module

    source = module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert "https://open-api.bingx.com" not in text
    assert "https://open-api.bingx.pro" not in text
