"""BingX VST read-only transport certification tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from urllib.error import URLError

import pytest

from adapters.bingx import http_transport
from adapters.bingx.http_transport import (
    FALLBACK_VST_BASE_URL,
    PRIMARY_VST_BASE_URL,
    BingXVstHttpConfig,
    BingXVstReadOnlyHttpTransport,
    _canonical_signing_string,
    _signature,
)


NOW = datetime(2026, 9, 13, 7, 0, tzinfo=UTC)


def _transport() -> BingXVstReadOnlyHttpTransport:
    return BingXVstReadOnlyHttpTransport(
        config=BingXVstHttpConfig(
            api_key="test-key",
            secret_key="test-secret",
        ),
        clock=lambda: NOW,
    )


def test_signing_string_is_ascii_key_sorted_and_unencoded() -> None:
    value = _canonical_signing_string(
        {
            "timestamp": "2",
            "symbol": "BTC-USDT",
            "recvWindow": "5000",
        }
    )
    assert value == "recvWindow=5000&symbol=BTC-USDT&timestamp=2"


def test_signature_is_deterministic_sha256_hmac() -> None:
    value = _signature(
        secret_key="secret",
        signing_string="a=1&b=2",
    )
    assert value == (
        "604fe97c66c6393ff22e3cae366eee1131e351ebc736bf12"
        "f5d62e1755b7a233"
    )
    assert len(value) == 64


def test_transport_rejects_write_methods_before_network() -> None:
    async def scenario() -> None:
        with pytest.raises(PermissionError, match="read-only"):
            await _transport().request("POST", "/openApi/example", {})

    asyncio.run(scenario())


def test_transport_uses_vst_only() -> None:
    assert "vst" in PRIMARY_VST_BASE_URL
    assert "vst" in FALLBACK_VST_BASE_URL
    assert PRIMARY_VST_BASE_URL.startswith("https://")
    assert FALLBACK_VST_BASE_URL.startswith("https://")


def test_transport_falls_back_only_after_network_failure(monkeypatch) -> None:
    transport = _transport()
    calls: list[str] = []

    def fake_request_once(*, method: str, url: str):
        calls.append(url)
        if len(calls) == 1:
            raise URLError("network down")
        return {"code": 0, "data": {}}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        response = await transport.request("GET", "/openApi/example", {})
        assert response["code"] == 0

    asyncio.run(scenario())
    assert calls[0].startswith(PRIMARY_VST_BASE_URL)
    assert calls[1].startswith(FALLBACK_VST_BASE_URL)


def test_transport_source_contains_no_live_base_url_without_vst() -> None:
    source = http_transport.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert "https://open-api.bingx.com" not in text
    assert "https://open-api.bingx.pro" not in text
