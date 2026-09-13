"""Credential-safe BingX VST HTTP transport for read-only certification."""

from __future__ import annotations

import hashlib
import hmac
import json
import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


PRIMARY_VST_BASE_URL: Final = "https://open-api-vst.bingx.com"
FALLBACK_VST_BASE_URL: Final = "https://open-api-vst.bingx.pro"
SOURCE_HEADER: Final = "BX-AI-SKILL"


class BingXVstTransportError(RuntimeError):
    """Network/transport failure without secret-bearing response content."""


@dataclass(frozen=True, slots=True)
class BingXVstHttpConfig:
    """Strict read-only VST transport configuration."""

    api_key: str
    secret_key: str
    recv_window_ms: int = 5000
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("api_key must be non-empty")
        if not self.secret_key.strip():
            raise ValueError("secret_key must be non-empty")
        if self.recv_window_ms <= 0 or self.recv_window_ms > 5000:
            raise ValueError("recv_window_ms must be within 1..5000")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class BingXVstControlledWriteHttpTransport:
    """Signed VST transport for narrowly scoped Phase-13 order certification.

    REAL hosts are unavailable. Writes are limited to the single BingX
    perpetual order endpoint required for submit/cancel lifecycle evidence.
    """

    _WRITE_PATH = "/openApi/swap/v2/trade/order"
    _ALLOWED_METHODS = frozenset({"GET", "POST", "DELETE"})

    def __init__(
        self,
        *,
        config: BingXVstHttpConfig,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._delegate = BingXVstReadOnlyHttpTransport(
            config=config,
            clock=clock,
        )

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        method_normalized = method.strip().upper()

        if method_normalized not in self._ALLOWED_METHODS:
            raise PermissionError(
                "BingX VST controlled-write transport rejects method"
            )
        if not path.startswith("/openApi/"):
            raise ValueError("BingX path must start with /openApi/")

        if method_normalized == "GET":
            return await self._delegate.request(
                method_normalized,
                path,
                params,
            )

        if path != self._WRITE_PATH:
            raise PermissionError(
                "BingX VST controlled-write transport rejects write endpoint"
            )

        signed_params = dict(params)
        signed_params["recvWindow"] = str(
            self._delegate._config.recv_window_ms
        )
        signed_params["timestamp"] = str(
            _milliseconds(self._delegate._now())
        )

        signing_string = _canonical_signing_string(signed_params)
        signature = _signature(
            secret_key=self._delegate._config.secret_key,
            signing_string=signing_string,
        )
        query = _encoded_query(signed_params, signature=signature)

        last_error: Exception | None = None
        for base_url in (PRIMARY_VST_BASE_URL, FALLBACK_VST_BASE_URL):
            try:
                return self._delegate._request_once(
                    method=method_normalized,
                    url=f"{base_url}{path}?{query}",
                )
            except (URLError, TimeoutError, socket.timeout) as exc:
                last_error = exc
                continue

        raise BingXVstTransportError(
            "BingX VST request failed on primary and fallback endpoints"
        ) from last_error

class BingXVstReadOnlyHttpTransport:
    """Signed VST transport that rejects all non-GET methods."""

    def __init__(
        self,
        *,
        config: BingXVstHttpConfig,
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
        if method_normalized != "GET":
            raise PermissionError(
                "BingX VST network certification transport is read-only"
            )
        if not path.startswith("/openApi/"):
            raise ValueError("BingX path must start with /openApi/")

        signed_params = dict(params)
        signed_params["recvWindow"] = str(self._config.recv_window_ms)
        signed_params["timestamp"] = str(_milliseconds(self._now()))

        signing_string = _canonical_signing_string(signed_params)
        signature = _signature(
            secret_key=self._config.secret_key,
            signing_string=signing_string,
        )
        query = _encoded_query(signed_params, signature=signature)

        last_error: Exception | None = None
        for base_url in (PRIMARY_VST_BASE_URL, FALLBACK_VST_BASE_URL):
            try:
                return self._request_once(
                    method=method_normalized,
                    url=f"{base_url}{path}?{query}",
                )
            except (URLError, TimeoutError, socket.timeout) as exc:
                last_error = exc
                continue

        raise BingXVstTransportError(
            "BingX VST request failed on primary and fallback endpoints"
        ) from last_error

    def _request_once(
        self,
        *,
        method: str,
        url: str,
    ) -> Mapping[str, object]:
        request = Request(
            url=url,
            method=method,
            headers={
                "Accept": "application/json",
                "X-BX-APIKEY": self._config.api_key,
                "X-SOURCE-KEY": SOURCE_HEADER,
            },
        )
        try:
            with urlopen(  # noqa: S310 - HTTPS bases are hard-coded above.
                request,
                timeout=self._config.timeout_seconds,
            ) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            raise BingXVstTransportError(
                f"BingX VST HTTP error status={exc.code}"
            ) from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BingXVstTransportError(
                "BingX VST returned invalid JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise BingXVstTransportError(
                "BingX VST response must be a JSON object"
            )
        return cast(Mapping[str, object], parsed)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "transport clock must return timezone-aware datetime"
            )
        return value.astimezone(UTC)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _milliseconds(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _canonical_signing_string(params: Mapping[str, str]) -> str:
    return "&".join(f"{key}={params[key]}" for key in sorted(params))


def _signature(*, secret_key: str, signing_string: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        signing_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _encoded_query(params: Mapping[str, str], *, signature: str) -> str:
    encoded = [
        f"{key}={quote(params[key], safe='-_.~')}"
        for key in sorted(params)
    ]
    encoded.append(f"signature={signature}")
    return "&".join(encoded)
