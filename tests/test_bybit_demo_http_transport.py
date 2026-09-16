from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from adapters.bybit import http_transport
from adapters.bybit.http_transport import (
    BYBIT_DEMO_BASE_URL,
    BybitDemoHttpConfig,
    BybitDemoHttpTransport,
    BybitDemoTransportError,
    _canonical_encoded_query,
    _canonical_json_body,
    _signature,
)

NOW = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)


def _transport(*, allow_writes: bool = False) -> BybitDemoHttpTransport:
    return BybitDemoHttpTransport(
        config=BybitDemoHttpConfig(
            api_key="demo-key",
            secret_key="demo-secret",
            allow_demo_writes=allow_writes,
        ),
        clock=lambda: NOW,
    )


def test_config_defaults_to_demo_host_and_rejects_non_demo_hosts() -> None:
    config = BybitDemoHttpConfig(api_key="k", secret_key="s")
    assert config.base_url == BYBIT_DEMO_BASE_URL

    production = "https://api" + ".bybit.com"
    testnet = "https://api-testnet" + ".bybit.com"
    with pytest.raises(ValueError, match="Demo Trading host only"):
        BybitDemoHttpConfig(api_key="k", secret_key="s", base_url=production)
    with pytest.raises(ValueError, match="Demo Trading host only"):
        BybitDemoHttpConfig(api_key="k", secret_key="s", base_url=testnet)


def test_recv_window_and_timeout_are_fail_closed() -> None:
    with pytest.raises(ValueError, match="1..60000"):
        BybitDemoHttpConfig(api_key="k", secret_key="s", recv_window_ms=60001)
    with pytest.raises(ValueError, match="positive"):
        BybitDemoHttpConfig(api_key="k", secret_key="s", timeout_seconds=0)


def test_query_json_and_hmac_are_deterministic() -> None:
    query = _canonical_encoded_query({"symbol": "BTCUSDT", "category": "linear"})
    assert query == "category=linear&symbol=BTCUSDT"

    body = _canonical_json_body({"symbol": "BTCUSDT", "qty": "1", "category": "linear"})
    assert body == '{"category":"linear","qty":"1","symbol":"BTCUSDT"}'

    get_payload = "1789408800000demo-key5000" + query
    assert _signature(secret_key="demo-secret", payload=get_payload) == (
        "baa3b941de43c6999c12ef1914be8e7e64274eb05f8a42ebd8caa0dd6b6b7b66"
    )
    post_payload = "1789408800000demo-key5000" + body
    assert _signature(secret_key="demo-secret", payload=post_payload) == (
        "e7633cb02b0afb755cfb226892e82eba2cabe5fb3cf31ead4319440d46cf6047"
    )


def test_get_transport_adds_required_headers_and_signs_exact_query(monkeypatch) -> None:
    transport = _transport()
    captured: dict[str, object] = {}

    def fake_request_once(*, method, url, headers, body):
        captured.update(method=method, url=url, headers=dict(headers), body=body)
        return {"retCode": 0, "retMsg": "OK", "result": {"list": []}}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        result = await transport.request(
            "GET",
            "/v5/order/realtime",
            {"symbol": "BTCUSDT", "category": "linear"},
        )
        assert result["retCode"] == 0

    asyncio.run(scenario())
    assert captured["method"] == "GET"
    assert captured["url"] == (
        BYBIT_DEMO_BASE_URL + "/v5/order/realtime?category=linear&symbol=BTCUSDT"
    )
    assert captured["body"] is None
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["X-BAPI-API-KEY"] == "demo-key"
    assert headers["X-BAPI-TIMESTAMP"] == "1789408800000"
    assert headers["X-BAPI-RECV-WINDOW"] == "5000"
    assert headers["X-BAPI-SIGN"] == (
        "baa3b941de43c6999c12ef1914be8e7e64274eb05f8a42ebd8caa0dd6b6b7b66"
    )


def test_transport_rejects_write_before_network_by_default(monkeypatch) -> None:
    transport = _transport()
    called = False

    def fake_request_once(*, method, url, headers, body):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        with pytest.raises(PermissionError, match="writes are disabled"):
            await transport.request(
                "POST",
                "/v5/order/create",
                {"category": "linear", "symbol": "BTCUSDT", "qty": "1"},
            )

    asyncio.run(scenario())
    assert called is False


def test_post_write_opt_in_signs_exact_json_body(monkeypatch) -> None:
    transport = _transport(allow_writes=True)
    captured: dict[str, object] = {}

    def fake_request_once(*, method, url, headers, body):
        captured.update(method=method, url=url, headers=dict(headers), body=body)
        return {"retCode": 0, "retMsg": "OK", "result": {"orderId": "1"}}

    monkeypatch.setattr(transport, "_request_once", fake_request_once)

    async def scenario() -> None:
        await transport.request(
            "POST",
            "/v5/order/create",
            {"symbol": "BTCUSDT", "qty": "1", "category": "linear"},
        )

    asyncio.run(scenario())
    assert captured["method"] == "POST"
    assert captured["url"] == BYBIT_DEMO_BASE_URL + "/v5/order/create"
    assert captured["body"] == b'{"category":"linear","qty":"1","symbol":"BTCUSDT"}'
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Content-Type"] == "application/json"
    assert headers["X-BAPI-SIGN"] == (
        "e7633cb02b0afb755cfb226892e82eba2cabe5fb3cf31ead4319440d46cf6047"
    )


def test_transport_rejects_non_v5_path_and_unknown_http_method() -> None:
    async def scenario() -> None:
        transport = _transport()
        with pytest.raises(ValueError, match="/v5/"):
            await transport.request("GET", "/api/v3/account", {})
        with pytest.raises(PermissionError, match="rejects HTTP method"):
            await transport.request("DELETE", "/v5/order/cancel", {})

    asyncio.run(scenario())


def test_http_error_preserves_safe_bybit_and_rate_limit_evidence(monkeypatch) -> None:
    transport = _transport()
    body = (
        b'{"retCode":10006,"retMsg":"Too many visits; '
        b'apiKey=top-secret-key X-BAPI-SIGN=top-secret-signature"}'
    )

    def limited(request, timeout):
        raise HTTPError(
            request.full_url,
            429,
            "Too Many Requests",
            {
                "Retry-After": "2",
                "X-Bapi-Limit": "10",
                "X-Bapi-Limit-Status": "0",
                "X-Bapi-Limit-Reset-Timestamp": "1789408802000",
                "X-BAPI-API-KEY": "must-never-be-captured",
            },
            BytesIO(body),
        )

    monkeypatch.setattr(http_transport, "urlopen", limited)

    async def scenario() -> None:
        with pytest.raises(BybitDemoTransportError) as caught:
            await transport.request("GET", "/v5/order/realtime", {"category": "linear"})
        error = caught.value
        assert error.status_code == 429
        assert error.bybit_code == 10006
        assert error.retry_after_seconds == 2
        assert error.rate_limit_headers == (
            ("X-Bapi-Limit", "10"),
            ("X-Bapi-Limit-Reset-Timestamp", "1789408802000"),
            ("X-Bapi-Limit-Status", "0"),
        )
        assert error.bybit_message is not None
        assert "apiKey=<redacted>" in error.bybit_message
        assert "X-BAPI-SIGN=<redacted>" in error.bybit_message
        rendered = str(error)
        assert "status=429" in rendered
        assert "code=10006" in rendered
        assert "retry_after=2s" in rendered
        assert "top-secret-key" not in rendered
        assert "top-secret-signature" not in rendered
        assert "must-never-be-captured" not in repr(error.rate_limit_headers)

    asyncio.run(scenario())


def test_network_and_invalid_json_errors_have_no_secret_material(monkeypatch) -> None:
    transport = _transport()

    def network_fail(request, timeout):
        raise URLError("network down")

    monkeypatch.setattr(http_transport, "urlopen", network_fail)

    async def network_case() -> None:
        with pytest.raises(BybitDemoTransportError, match="network request failed") as caught:
            await transport.request("GET", "/v5/order/realtime", {"category": "linear"})
        assert caught.value.status_code is None
        assert caught.value.bybit_code is None

    asyncio.run(network_case())

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr(http_transport, "urlopen", lambda request, timeout: FakeResponse())

    async def json_case() -> None:
        with pytest.raises(BybitDemoTransportError, match="invalid JSON"):
            await transport.request("GET", "/v5/order/realtime", {"category": "linear"})

    asyncio.run(json_case())


def test_source_contains_only_demo_host_literal() -> None:
    source = http_transport.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    production = "https://api" + ".bybit.com"
    testnet = "https://api-testnet" + ".bybit.com"
    assert production not in text
    assert testnet not in text
    assert BYBIT_DEMO_BASE_URL in text
