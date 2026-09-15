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
import re
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
    """Sanitized Binance transport failure with safe runtime evidence."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        binance_code: int | str | None = None,
        binance_message: str | None = None,
        retry_after_seconds: int | None = None,
        rate_limit_headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.binance_code = binance_code
        self.binance_message = binance_message
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit_headers = rate_limit_headers


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
            evidence = _http_error_evidence(exc)
            parts = [f"Binance USD-M sandbox HTTP error status={exc.code}"]
            if evidence["binance_code"] is not None:
                parts.append(f"code={evidence['binance_code']}")
            if evidence["retry_after_seconds"] is not None:
                parts.append(f"retry_after={evidence['retry_after_seconds']}s")
            if evidence["binance_message"]:
                parts.append(f"msg={evidence['binance_message']}")
            raise BinanceUsdMTransportError(
                " ".join(parts),
                status_code=exc.code,
                binance_code=evidence["binance_code"],
                binance_message=evidence["binance_message"],
                retry_after_seconds=evidence["retry_after_seconds"],
                rate_limit_headers=evidence["rate_limit_headers"],
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


_SENSITIVE_TOKEN_PATTERNS: Final = (
    re.compile(r"(?i)(signature\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(secret(?:[_-]?key)?\s*[=:]\s*)[^&\s,;]+"),
)


def _redact_sensitive_text(value: object, *, limit: int = 512) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    for pattern in _SENSITIVE_TOKEN_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}<redacted>", text)
    return text[:limit]


def _http_error_evidence(exc: HTTPError) -> dict[str, object]:
    """Extract only non-secret diagnostic evidence from one HTTPError."""

    retry_after_seconds: int | None = None
    rate_limit_headers: list[tuple[str, str]] = []
    headers = exc.headers
    if headers is not None:
        raw_retry_after = headers.get("Retry-After")
        if raw_retry_after is not None:
            try:
                retry_after_seconds = max(0, int(str(raw_retry_after).strip()))
            except ValueError:
                retry_after_seconds = None
        for name, value in headers.items():
            lowered = str(name).lower()
            if lowered.startswith("x-mbx-used-weight-") or lowered.startswith(
                "x-mbx-order-count-"
            ):
                rate_limit_headers.append((str(name), _redact_sensitive_text(value, limit=128)))

    binance_code: int | str | None = None
    binance_message: str | None = None
    try:
        body = exc.read(4096)
    except Exception:  # pragma: no cover - defensive against exotic HTTPError bodies.
        body = b""
    if body:
        try:
            parsed = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            raw_code = parsed.get("code")
            if isinstance(raw_code, (int, str)):
                binance_code = raw_code
            raw_message = parsed.get("msg")
            if raw_message is not None:
                binance_message = _redact_sensitive_text(raw_message)

    return {
        "binance_code": binance_code,
        "binance_message": binance_message,
        "retry_after_seconds": retry_after_seconds,
        "rate_limit_headers": tuple(sorted(rate_limit_headers)),
    }
