"""Credential-safe Bybit V5 Demo Trading HTTP transport.

Only the official Bybit Demo Trading REST host is accepted. Production and
Testnet hosts are intentionally rejected in this Phase-13 slice. Authenticated
V5 requests use X-BAPI-* headers and HMAC-SHA256 over the exact GET query string
or POST JSON body. Writes require an explicit transport opt-in in addition to
the VenueAdapter write gate.
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
from typing import Final, TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BYBIT_DEMO_BASE_URL: Final = "https://api-demo.bybit.com"
_ALLOWED_DEMO_BASE_URLS: Final = frozenset({BYBIT_DEMO_BASE_URL})


class _HttpErrorEvidence(TypedDict):
    bybit_code: int | str | None
    bybit_message: str | None
    retry_after_seconds: int | None
    rate_limit_headers: tuple[tuple[str, str], ...]


class BybitDemoTransportError(RuntimeError):
    """Sanitized Bybit transport failure with safe runtime evidence."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        bybit_code: int | str | None = None,
        bybit_message: str | None = None,
        retry_after_seconds: int | None = None,
        rate_limit_headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.bybit_code = bybit_code
        self.bybit_message = bybit_message
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit_headers = rate_limit_headers


@dataclass(frozen=True, slots=True)
class BybitDemoHttpConfig:
    """Strict Bybit V5 Demo Trading transport configuration."""

    api_key: str
    secret_key: str
    base_url: str = BYBIT_DEMO_BASE_URL
    recv_window_ms: int = 5000
    timeout_seconds: float = 10.0
    allow_demo_writes: bool = False

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("api_key must be non-empty")
        if not self.secret_key.strip():
            raise ValueError("secret_key must be non-empty")
        base_url = self.base_url.rstrip("/")
        if base_url not in _ALLOWED_DEMO_BASE_URLS:
            raise ValueError("Bybit transport accepts Demo Trading host only")
        object.__setattr__(self, "base_url", base_url)
        if self.recv_window_ms <= 0 or self.recv_window_ms > 60000:
            raise ValueError("recv_window_ms must be within 1..60000")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.allow_demo_writes, bool):
            raise ValueError("allow_demo_writes must be boolean")


class BybitDemoHttpTransport:
    """Signed Bybit V5 Demo REST transport with fail-closed writes."""

    _ALLOWED_METHODS = frozenset({"GET", "POST"})

    def __init__(
        self,
        *,
        config: BybitDemoHttpConfig,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._clock = clock if clock is not None else _utc_now

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        method_normalized = method.strip().upper()
        if method_normalized not in self._ALLOWED_METHODS:
            raise PermissionError("Bybit Demo transport rejects HTTP method")
        if not path.startswith("/v5/"):
            raise ValueError("Bybit path must start with /v5/")
        if method_normalized != "GET" and not self._config.allow_demo_writes:
            raise PermissionError("Bybit Demo transport writes are disabled")

        timestamp = str(_milliseconds(self._now()))
        recv_window = str(self._config.recv_window_ms)
        headers = {
            "Accept": "application/json",
            "X-BAPI-API-KEY": self._config.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
        }

        if method_normalized == "GET":
            query = _canonical_encoded_query(params)
            payload = f"{timestamp}{self._config.api_key}{recv_window}{query}"
            headers["X-BAPI-SIGN"] = _signature(
                secret_key=self._config.secret_key,
                payload=payload,
            )
            url = f"{self._config.base_url}{path}"
            if query:
                url = f"{url}?{query}"
            body = None
        else:
            body_text = _canonical_json_body(params)
            payload = f"{timestamp}{self._config.api_key}{recv_window}{body_text}"
            headers["X-BAPI-SIGN"] = _signature(
                secret_key=self._config.secret_key,
                payload=payload,
            )
            headers["Content-Type"] = "application/json"
            url = f"{self._config.base_url}{path}"
            body = body_text.encode("utf-8")

        return self._request_once(
            method=method_normalized,
            url=url,
            headers=headers,
            body=body,
        )

    def _request_once(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
    ) -> Mapping[str, object]:
        request = Request(
            url=url,
            method=method,
            headers=dict(headers),
            data=body,
        )
        try:
            with urlopen(  # noqa: S310 - base_url is strict Demo Trading allowlist.
                request,
                timeout=self._config.timeout_seconds,
            ) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            evidence = _http_error_evidence(exc)
            parts = [f"Bybit Demo HTTP error status={exc.code}"]
            if evidence["bybit_code"] is not None:
                parts.append(f"code={evidence['bybit_code']}")
            if evidence["retry_after_seconds"] is not None:
                parts.append(f"retry_after={evidence['retry_after_seconds']}s")
            if evidence["bybit_message"]:
                parts.append(f"msg={evidence['bybit_message']}")
            raise BybitDemoTransportError(
                " ".join(parts),
                status_code=exc.code,
                bybit_code=evidence["bybit_code"],
                bybit_message=evidence["bybit_message"],
                retry_after_seconds=evidence["retry_after_seconds"],
                rate_limit_headers=evidence["rate_limit_headers"],
            ) from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise BybitDemoTransportError("Bybit Demo network request failed") from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BybitDemoTransportError("Bybit Demo returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise BybitDemoTransportError("Bybit Demo response must be a JSON object")
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


def _canonical_json_body(params: Mapping[str, str]) -> str:
    return json.dumps(dict(params), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _signature(*, secret_key: str, payload: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


_SENSITIVE_TOKEN_PATTERNS: Final = (
    re.compile(r"(?i)(x-bapi-sign\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(x-bapi-api-key\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(secret(?:[_-]?key)?\s*[=:]\s*)[^&\s,;]+"),
    re.compile(r"(?i)(signature\s*[=:]\s*)[^&\s,;]+"),
)


def _redact_sensitive_text(value: object, *, limit: int = 512) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    for pattern in _SENSITIVE_TOKEN_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}<redacted>", text)
    return text[:limit]


def _http_error_evidence(exc: HTTPError) -> _HttpErrorEvidence:
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
            if lowered in {
                "x-bapi-limit",
                "x-bapi-limit-status",
                "x-bapi-limit-reset-timestamp",
            }:
                rate_limit_headers.append(
                    (str(name), _redact_sensitive_text(value, limit=128))
                )

    bybit_code: int | str | None = None
    bybit_message: str | None = None
    try:
        body = exc.read(4096)
    except Exception:  # pragma: no cover - defensive for unusual HTTPError bodies.
        body = b""
    if body:
        try:
            parsed = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            raw_code = parsed.get("retCode")
            if isinstance(raw_code, (int, str)):
                bybit_code = raw_code
            raw_message = parsed.get("retMsg")
            if raw_message is not None:
                bybit_message = _redact_sensitive_text(raw_message)

    return {
        "bybit_code": bybit_code,
        "bybit_message": bybit_message,
        "retry_after_seconds": retry_after_seconds,
        "rate_limit_headers": tuple(sorted(rate_limit_headers)),
    }
