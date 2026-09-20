"""Long-running read-only BingX VST observer runtime for Phase 13.

This runtime replaces the simulation-only venue view with repeated canonical
BingX VST observations. It deliberately has no order-write path and grants no
strategy execution authority.
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from adapters.bingx.http_transport import BingXVstHttpConfig, BingXVstReadOnlyHttpTransport
from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from packages.contracts.identities import AccountId, AssetClass, InstrumentId, InstrumentType

DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8080
DEFAULT_INTERVAL_SECONDS: Final = 30.0


@dataclass(frozen=True, slots=True)
class ObserverSnapshot:
    environment: str
    symbol: str
    observed_at: str
    source_state: str
    account_query: str
    open_orders_query: str
    positions_query: str
    fills_query: str
    balance_assets: tuple[str, ...]
    open_order_count: int
    position_count: int
    fill_count: int
    writes_attempted: bool
    production_authority: bool
    strategy_execution_allowed: bool
    error: str | None = None


class RuntimeState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: ObserverSnapshot | None = None

    def set(self, snapshot: ObserverSnapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get(self) -> ObserverSnapshot | None:
        with self._lock:
            return self._snapshot


STATE = RuntimeState()


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def _symbol() -> str:
    value = os.environ.get("BINGX_VST_SYMBOL", "BTCUSDT").strip().upper()
    if not value:
        raise RuntimeError("BINGX_VST_SYMBOL must not be empty")
    return value


def _interval_seconds() -> float:
    value = float(os.environ.get("NEXUS_OBSERVER_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS)))
    if value < 1.0:
        raise RuntimeError("NEXUS_OBSERVER_INTERVAL_SECONDS must be >= 1")
    return value


async def observe_once() -> ObserverSnapshot:
    api_key = _required_env("BINGX_VST_API_KEY")
    secret_key = _required_env("BINGX_VST_SECRET_KEY")
    symbol = _symbol()
    transport = BingXVstReadOnlyHttpTransport(
        config=BingXVstHttpConfig(api_key=api_key, secret_key=secret_key)
    )
    adapter = BingXVenueAdapter(transport=transport)
    account_id = AccountId(venue_id=BINGX_VENUE_ID, value=1)
    instrument_id = InstrumentId(
        venue_id=BINGX_VENUE_ID,
        native_symbol=symbol,
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    account = await adapter.get_account_state(account_id=account_id)
    open_orders = await adapter.get_open_orders(account_id=account_id, instrument_id=instrument_id)
    positions = await adapter.get_positions(account_id=account_id)
    fills = await adapter.get_fills(
        account_id=account_id,
        instrument_id=instrument_id,
        since=datetime.now(UTC) - timedelta(hours=24),
    )
    return ObserverSnapshot(
        environment="BINGX_VST",
        symbol=symbol,
        observed_at=datetime.now(UTC).isoformat(),
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=tuple(item.currency for item in account.balances),
        open_order_count=len(open_orders),
        position_count=len(positions),
        fill_count=len(fills),
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
    )


def _failed_snapshot(exc: Exception) -> ObserverSnapshot:
    return ObserverSnapshot(
        environment="BINGX_VST",
        symbol=_symbol(),
        observed_at=datetime.now(UTC).isoformat(),
        source_state="UNAVAILABLE",
        account_query="FAIL",
        open_orders_query="FAIL",
        positions_query="FAIL",
        fills_query="FAIL",
        balance_assets=(),
        open_order_count=0,
        position_count=0,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
        error=f"{type(exc).__name__}: {exc}",
    )


def observer_loop(stop: threading.Event) -> None:
    interval = _interval_seconds()
    while not stop.is_set():
        try:
            STATE.set(asyncio.run(observe_once()))
        except Exception as exc:  # fail closed and expose source failure
            STATE.set(_failed_snapshot(exc))
        stop.wait(interval)


def _payload(snapshot: ObserverSnapshot | None) -> dict[str, object]:
    if snapshot is None:
        return {
            "service": "nexus-v2-core",
            "runtime_mode": "BINGX_VST_OBSERVE_ONLY",
            "status": "STARTING",
            "ready": False,
            "production_authority": False,
            "strategy_execution_allowed": False,
        }
    data = asdict(snapshot)
    data.update(
        {
            "service": "nexus-v2-core",
            "runtime_mode": "BINGX_VST_OBSERVE_ONLY",
            "status": "RUNNING" if snapshot.source_state == "CURRENT" else "DEGRADED",
            "ready": snapshot.source_state == "CURRENT",
        }
    )
    return data


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-BINGX-VST-OBSERVER"

    def do_GET(self) -> None:
        payload = _payload(STATE.get())
        if self.path == "/health":
            self._respond(HTTPStatus.OK, payload)
            return
        if self.path == "/ready":
            ready = bool(payload["ready"])
            self._respond(HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE, payload)
            return
        if self.path == "/status":
            self._respond(HTTPStatus.OK, payload)
            return
        self._respond(HTTPStatus.NOT_FOUND, {"code": "NOT_FOUND", "message": "not found"})

    def _respond(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    # Fail before binding a server if secrets/config are absent.
    _required_env("BINGX_VST_API_KEY")
    _required_env("BINGX_VST_SECRET_KEY")
    _symbol()
    _interval_seconds()

    stop = threading.Event()
    worker = threading.Thread(target=observer_loop, args=(stop,), daemon=True)
    worker.start()

    host = os.environ.get("NEXUS_RUNTIME_HOST", DEFAULT_HOST)
    port = int(os.environ.get("NEXUS_RUNTIME_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), RuntimeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        worker.join(timeout=5)
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
