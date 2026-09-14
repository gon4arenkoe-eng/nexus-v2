from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError

import pytest

from adapters.binance import http_transport
from adapters.binance.http_transport import (
    DEMO_FAPI_BASE_URL,
    LEGACY_TESTNET_BASE_URL,
    BinanceUsdMHttpConfig,
    BinanceUsdMSandboxHttpTransport,
    BinanceUsdMTransportError,
    _canonical_encoded_query,
    _signature,
)

NOW = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)


def _transport(*, allow_writes: bool = False) -> BinanceUsdMSandboxHttpTransport:
    return BinanceUsdMSandboxHttpTransport(
        config=BinanceUsdMHttpConfig(
            api_key="demo-key",
            secret_key="demo-secret",
            allow_sandbox_writes=allow_writes,
        ),
        clock=lambda: NOW,
    )


def test_config_defaults_to_demo_fapi_and_rejects_production_host() -> None:
    config = BinanceUsdMHttpConfig(api_key="k", secret_key="s")
    assert config.base_url == DEMO_FAPI_BASE_URL
    with pytest.raises(ValueError, match="sandbox hosts only"):
        BinanceUsdMHttpConfig(
            api_key="k",
            secret_key="s",
            base_url="https://fapi.binance.com",
        )


def test_legacy_testnet_host_is_explicitly_allowlisted_for_compatibility() -> None:
    config = BinanceUsdMHttpConfig(
        api_key="k",
        secret_key="s",
        base_url=LEGACY_TESTNET_BASE_URL,
    )
    assert config.base_url == LEGACY_TESTNET_BASE_URL


def test_recv_window_is_fail_closed_to_binance_documented_maximum() -> None:
    with pytest.raises(ValueError, match="1..60000"):
        BinanceUsdMHttpConfig(api_key="k", secret_key="s", recv_window_ms=60001)


def test_query_encoding_and_hmac_are_deterministic() -> None:
    query = _canonical_encoded_query(
        {"timestamp": "2", "symbol": "BTCUSDT", "recvWindow": "5000"}
    )
    assert query == "recvWindow=5000&symbol=BTCUSDT&timestamp=2"
    assert _signature(secret_key="secret", query_string="a=1&b=2") == (
        "604fe97c66c6393ff22e3cae366eee1131e351ebc736bf12"
        "f5d62e1755b7a233"
    )


def test_transport_adds_api_key_timestamp_recv_window_and_signature(monkeypatch) -> None:
    transport = _transport()
    captured: dict[str, str] = {}

    def fake_request_once(*, method: str, url: str):
        captured["method"] = method
        captured["url"] = url
        return {"ok": True}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        result = await transport.request("GET", "/fapi/v2/balance", {"asset": "USDT"})
        assert result == {"ok": True}

    asyncio.run(scenario())
    assert captured["method"] == "GET"
    assert captured["url"].startswith(DEMO_FAPI_BASE_URL + "/fapi/v2/balance?")
    assert "asset=USDT" in captured["url"]
    assert "recvWindow=5000" in captured["url"]
    assert "timestamp=1789408800000" in captured["url"]
    assert "signature=" in captured["url"]


def test_transport_rejects_write_before_network_by_default(monkeypatch) -> None:
    transport = _transport()
    called = False

    def fake_request_once(*, method: str, url: str):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        with pytest.raises(PermissionError, match="writes are disabled"):
            await transport.request("POST", "/fapi/v1/order", {"symbol": "BTCUSDT"})

    asyncio.run(scenario())
    assert called is False


def test_transport_write_requires_explicit_opt_in(monkeypatch) -> None:
    transport = _transport(allow_writes=True)
    captured: dict[str, str] = {}

    def fake_request_once(*, method: str, url: str):
        captured["method"] = method
        captured["url"] = url
        return {"orderId": 1}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        result = await transport.request("POST", "/fapi/v1/order", {"symbol": "BTCUSDT"})
        assert result == {"orderId": 1}

    asyncio.run(scenario())
    assert captured["method"] == "POST"


def test_transport_rejects_non_fapi_path_and_owned_security_params() -> None:
    async def scenario() -> None:
        transport = _transport()
        with pytest.raises(ValueError, match="/fapi/"):
            await transport.request("GET", "/api/v3/account", {})
        with pytest.raises(ValueError, match="transport owns"):
            await transport.request("GET", "/fapi/v2/balance", {"timestamp": "1"})

    asyncio.run(scenario())


def test_http_and_network_errors_are_sanitized(monkeypatch) -> None:
    transport = _transport()

    class FakeHttpError(HTTPError):
        pass

    def http_fail(request, timeout):
        raise FakeHttpError(request.full_url, 401, "secret body", {}, None)

    monkeypatch.setattr(http_transport, "urlopen", http_fail)
    async def first() -> None:
        with pytest.raises(BinanceUsdMTransportError, match="status=401") as exc:
            await transport.request("GET", "/fapi/v2/balance", {})
        assert "secret body" not in str(exc.value)

    asyncio.run(first())

    def network_fail(request, timeout):
        raise URLError("network down")

    monkeypatch.setattr(http_transport, "urlopen", network_fail)
    async def second() -> None:
        with pytest.raises(BinanceUsdMTransportError, match="network request failed"):
            await transport.request("GET", "/fapi/v2/balance", {})

    asyncio.run(second())


def test_source_contains_no_production_fapi_base_url() -> None:
    source = http_transport.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    forbidden = "https://" + "fapi.binance.com"
    assert forbidden not in text
