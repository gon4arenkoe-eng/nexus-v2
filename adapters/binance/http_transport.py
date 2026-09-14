"""Credential-safe Binance USD-M sandbox HTTP transport.

Only Binance sandbox/demo USD-M hosts are accepted. Production hosts are rejected.
Signed requests use X-MBX-APIKEY plus HMAC-SHA256 over the exact encoded query
string containing timestamp and recvWindow. Writes require an explicit transport
opt-in in addition to the VenueAdapter write gate.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEMO_FAPI_BASE_URL: Final = "https://demo-fapi.binance.com"
LEGACY_TESTNET_BASE_URL: Final = "https://testnet.binancefuture.com"
_ALLOWED_SANDBOX_BASE_URLS: Final = frozenset(
    {DEMO_FAPI_BASE_URL, LEGACY_TESTNET_BASE_URL}
)


class BinanceUsdMTransportError(RuntimeError):
    """Sanitized network/HTTP/JSON transport failure."""


@dataclass(frozen=True, slots=True)
class BinanceUsdMHttpConfig:
    """Strict Binance USD-M sandbox transport configuration."""

    api_key: str
    secret_key: str
    base_url: str = DEMO_FAPI_BASE_URL
    recv_window_ms: int = 5000
    timeout_seconds: float = 10.0
    allow_sandbox_writes: bool = False

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("api_key must be non-empty")
        if not self.secret_key.strip():
            raise ValueError("secret_key must be non-empty")
        base_url = self.base_url.rstrip("/")
        if base_url not in _ALLOWED_SANDBOX_BASE_URLS:
            raise ValueError("Binance USD-M transport accepts sandbox hosts only")
        object.__setattr__(self, "base_url", base_url)
        if self.recv_window_ms <= 0 or self.recv_window_ms > 60000:
            raise ValueError("recv_window_ms must be within 1..60000")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.allow_sandbox_writes, bool):
            raise ValueError("allow_sandbox_writes must be boolean")


class BinanceUsdMSandboxHttpTransport:
    """Signed Binance USD-M sandbox REST transport with fail-closed writes."""

    _ALLOWED_METHODS = frozenset({"GET", "POST", "DELETE"})

    def __init__(
        self,
        *,
        config: BinanceUsdMHttpConfig,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._clock = clock if clock is not None else _utc_now

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> object:
        method_normalized = method.strip().upper()
        if method_normalized not in self._ALLOWED_METHODS:
            raise PermissionError("Binance USD-M transport rejects HTTP method")
        if not path.startswith("/fapi/"):
            raise ValueError("Binance USD-M path must start with /fapi/")
        if method_normalized != "GET" and not self._config.allow_sandbox_writes:
            raise PermissionError("Binance USD-M sandbox transport writes are disabled")

        signed_params = dict(params)
        if "timestamp" in signed_params or "recvWindow" in signed_params or "signature" in signed_params:
            raise ValueError("transport owns timestamp, recvWindow and signature")
        signed_params["recvWindow"] = str(self._config.recv_window_ms)
        signed_params["timestamp"] = str(_milliseconds(self._now()))

        query = _canonical_encoded_query(signed_params)
        signature = _signature(secret_key=self._config.secret_key, query_string=query)
        url = f"{self._config.base_url}{path}?{query}&signature={signature}"
        return self._request_once(method=method_normalized, url=url)

    def _request_once(self, *, method: str, url: str) -> object:
        request = Request(
            url=url,
            method=method,
            headers={
                "Accept": "application/json",
                "X-MBX-APIKEY": self._config.api_key,
            },
        )
        try:
            with urlopen(  # noqa: S310 - base_url is strict sandbox allowlist.
                request,
                timeout=self._config.timeout_seconds,
            ) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            raise BinanceUsdMTransportError(
                f"Binance USD-M sandbox HTTP error status={exc.code}"
            ) from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise BinanceUsdMTransportError(
                "Binance USD-M sandbox network request failed"
            ) from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BinanceUsdMTransportError(
                "Binance USD-M sandbox returned invalid JSON"
            ) from exc
        if not isinstance(parsed, (dict, list)):
            raise BinanceUsdMTransportError(
                "Binance USD-M sandbox response must be JSON object or array"
            )
        return parsed

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("transport clock must return timezone-aware datetime")
        return value.astimezone(UTC)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _milliseconds(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _canonical_encoded_query(params: Mapping[str, str]) -> str:
    return urlencode(sorted(params.items()))


def _signature(*, secret_key: str, query_string: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
