"""Phase 14 BingX VST read-only shadow runtime.

Real BingX VST is observation-only.
Candidate execution runs only through the existing simulated Core runtime.
This runtime grants no real venue submit/cancel authority and does not close
NEXUS_V2_SHADOW_PARITY_OK by itself.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Awaitable, Callable, Final

from scripts.bingx_vst_observer_runtime import (
    ObserverSnapshot,
    observe_once,
)
from scripts.phase14_postgres_candidate import (
    run as run_postgres_candidate,
)


DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8080
DEFAULT_INTERVAL_SECONDS: Final = 30.0


ObserverRunner = Callable[[], Awaitable[ObserverSnapshot]]
CandidateRunner = Callable[[], Awaitable[dict[str, object]]]


@dataclass(frozen=True, slots=True)
class Phase14ShadowSnapshot:
    observed_at: str
    environment: str
    symbol: str
    source_state: str
    ready: bool

    real_open_order_count: int
    real_position_count: int
    real_fill_count: int

    candidate_status: str
    candidate_startup_reconciliation: str
    candidate_portfolio_risk: str
    candidate_execution_state: str
    candidate_order_status: str
    candidate_post_execution_reconciliation: str

    simulated_venue_writes: int
    real_exchange_writes: int

    shadow_gate_open: bool
    production_authority: bool
    strategy_execution_allowed: bool
    writes_attempted: bool

    error: str | None = None


class RuntimeState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: Phase14ShadowSnapshot | None = None

    def set(self, snapshot: Phase14ShadowSnapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get(self) -> Phase14ShadowSnapshot | None:
        with self._lock:
            return self._snapshot


STATE = RuntimeState()


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"required environment variable is missing: {name}"
        )
    return value


def _interval_seconds() -> float:
    raw = os.environ.get(
        "NEXUS_PHASE14_SHADOW_INTERVAL_SECONDS",
        str(DEFAULT_INTERVAL_SECONDS),
    )

    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(
            "NEXUS_PHASE14_SHADOW_INTERVAL_SECONDS must be numeric"
        ) from exc

    if value < 1.0:
        raise RuntimeError(
            "NEXUS_PHASE14_SHADOW_INTERVAL_SECONDS must be >= 1"
        )

    return value


def _candidate_text(
    candidate: dict[str, object],
    key: str,
) -> str:
    value = candidate.get(key)
    return "" if value is None else str(value)


def _candidate_int(
    candidate: dict[str, object],
    key: str,
) -> int:
    value = candidate.get(key)

    if isinstance(value, bool):
        raise RuntimeError(f"{key} must be integer")

    if not isinstance(value, int):
        raise RuntimeError(f"{key} must be integer")

    return value


async def run_shadow_cycle(
    *,
    observer: ObserverRunner = observe_once,
    candidate_runner: CandidateRunner = run_postgres_candidate,
) -> Phase14ShadowSnapshot:
    real = await observer()
    candidate = await candidate_runner()

    real_exchange_writes = _candidate_int(
        candidate,
        "real_exchange_writes",
    )
    simulated_venue_writes = _candidate_int(
        candidate,
        "venue_writes",
    )

    candidate_production_authority = candidate.get(
        "production_authority"
    )

    candidate_ok = all(
        (
            _candidate_text(candidate, "status") == "RUNNING",
            _candidate_text(
                candidate,
                "startup_reconciliation",
            )
            == "MATCHED",
            _candidate_text(candidate, "portfolio_risk")
            == "APPROVED",
            _candidate_text(
                candidate,
                "post_execution_reconciliation",
            )
            == "MATCHED",
            real_exchange_writes == 0,
            candidate_production_authority is False,
        )
    )

    real_ok = (
        real.source_state == "CURRENT"
        and real.writes_attempted is False
        and real.production_authority is False
        and real.strategy_execution_allowed is False
    )

    ready = real_ok and candidate_ok

    error: str | None = None

    if real_exchange_writes != 0:
        error = "candidate_real_exchange_write_detected"
    elif not real_ok:
        error = "bingx_observation_not_current_or_not_read_only"
    elif not candidate_ok:
        error = "simulated_candidate_not_ready"

    return Phase14ShadowSnapshot(
        observed_at=datetime.now(UTC).isoformat(),
        environment="BINGX_VST",
        symbol=real.symbol,
        source_state=real.source_state,
        ready=ready,
        real_open_order_count=real.open_order_count,
        real_position_count=real.position_count,
        real_fill_count=real.fill_count,
        candidate_status=_candidate_text(
            candidate,
            "status",
        ),
        candidate_startup_reconciliation=_candidate_text(
            candidate,
            "startup_reconciliation",
        ),
        candidate_portfolio_risk=_candidate_text(
            candidate,
            "portfolio_risk",
        ),
        candidate_execution_state=_candidate_text(
            candidate,
            "execution_state",
        ),
        candidate_order_status=_candidate_text(
            candidate,
            "order_status",
        ),
        candidate_post_execution_reconciliation=_candidate_text(
            candidate,
            "post_execution_reconciliation",
        ),
        simulated_venue_writes=simulated_venue_writes,
        real_exchange_writes=real_exchange_writes,
        # Runtime readiness is not the Phase 14 parity gate.
        shadow_gate_open=False,
        production_authority=False,
        strategy_execution_allowed=False,
        writes_attempted=False,
        error=error,
    )


def _failed_snapshot(
    exc: Exception,
) -> Phase14ShadowSnapshot:
    return Phase14ShadowSnapshot(
        observed_at=datetime.now(UTC).isoformat(),
        environment="BINGX_VST",
        symbol=os.environ.get(
            "BINGX_VST_SYMBOL",
            "BTCUSDT",
        ).strip().upper(),
        source_state="UNAVAILABLE",
        ready=False,
        real_open_order_count=0,
        real_position_count=0,
        real_fill_count=0,
        candidate_status="UNKNOWN",
        candidate_startup_reconciliation="UNKNOWN",
        candidate_portfolio_risk="UNKNOWN",
        candidate_execution_state="UNKNOWN",
        candidate_order_status="UNKNOWN",
        candidate_post_execution_reconciliation="UNKNOWN",
        simulated_venue_writes=0,
        real_exchange_writes=0,
        shadow_gate_open=False,
        production_authority=False,
        strategy_execution_allowed=False,
        writes_attempted=False,
        error=f"{type(exc).__name__}: {exc}",
    )


def shadow_loop(stop: threading.Event) -> None:
    interval = _interval_seconds()

    while not stop.is_set():
        try:
            STATE.set(
                asyncio.run(
                    run_shadow_cycle()
                )
            )
        except Exception as exc:
            STATE.set(_failed_snapshot(exc))

        stop.wait(interval)


def _payload(
    snapshot: Phase14ShadowSnapshot | None,
) -> dict[str, object]:
    base: dict[str, object] = {
        "service": "nexus-v2-core",
        "runtime_mode": "PHASE14_BINGX_VST_SHADOW_READ_ONLY",
        "environment": "BINGX_VST",
        "production_authority": False,
        "strategy_execution_allowed": False,
        "writes_attempted": False,
        "shadow_gate_open": False,
    }

    if snapshot is None:
        return {
            **base,
            "status": "STARTING",
            "ready": False,
            "source_state": "UNKNOWN",
        }

    return {
        **base,
        **asdict(snapshot),
        "status": (
            "RUNNING"
            if snapshot.ready
            else "DEGRADED"
        ),
    }


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-PHASE14-BINGX-SHADOW"

    def do_GET(self) -> None:
        payload = _payload(STATE.get())

        if self.path == "/health":
            code = HTTPStatus.OK
        elif self.path == "/ready":
            code = (
                HTTPStatus.OK
                if payload["ready"]
                else HTTPStatus.SERVICE_UNAVAILABLE
            )
        elif self.path == "/status":
            code = HTTPStatus.OK
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        encoded = json.dumps(
            payload,
            sort_keys=True,
        ).encode("utf-8")

        self.send_response(code)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(encoded)),
        )
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        return


def main() -> int:
    # Fail before binding HTTP if real VST observation cannot be configured.
    _required_env("BINGX_VST_API_KEY")
    _required_env("BINGX_VST_SECRET_KEY")
    _interval_seconds()

    stop = threading.Event()
    worker = threading.Thread(
        target=shadow_loop,
        args=(stop,),
        daemon=True,
    )
    worker.start()

    host = os.environ.get(
        "NEXUS_RUNTIME_HOST",
        DEFAULT_HOST,
    )
    port = int(
        os.environ.get(
            "NEXUS_RUNTIME_PORT",
            str(DEFAULT_PORT),
        )
    )

    server = ThreadingHTTPServer(
        (host, port),
        RuntimeHandler,
    )

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
