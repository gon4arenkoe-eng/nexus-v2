"""Read-only BingX VST Phase-3 reconciliation server runtime."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from sqlalchemy import text

from adapters.bingx.http_transport import (
    BingXVstHttpConfig,
    BingXVstReadOnlyHttpTransport,
)
from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
)
from apps.core.application.reconciliation_runtime import ReconciliationRuntime
from infra.persistence.application.ledger import ExecutionLedgerPersistenceService
from infra.persistence.application.reconciliation_evidence import (
    LedgerReconciliationEvidenceAdapter,
)
from infra.persistence.application.reconciliation_snapshot import (
    SqlAlchemyLocalReconciliationSnapshotProvider,
)
from infra.persistence.session import (
    create_persistence_engine,
    create_session_factory,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
)

DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8080
DEFAULT_INTERVAL_SECONDS: Final = 30.0
EXPECTED_ALEMBIC_HEAD: Final = "e9b1c7d3a246"


@dataclass(frozen=True, slots=True)
class Phase3Snapshot:
    observed_at: str
    source_state: str
    reconciliation_gate_passed: bool
    ready: bool
    error: str | None
    strategy_execution_allowed: bool = False
    production_authority: bool = False
    writes_attempted: bool = False


class RuntimeState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: Phase3Snapshot | None = None

    def set(self, snapshot: Phase3Snapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get(self) -> Phase3Snapshot | None:
        with self._lock:
            return self._snapshot


STATE = RuntimeState()


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(
            f"required environment variable is missing: {name}"
        )
    return value.strip()


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be positive")
    return value


def _symbol() -> str:
    value = os.environ.get(
        "BINGX_VST_SYMBOL",
        "BTCUSDT",
    ).strip().upper()
    if not value:
        raise RuntimeError("BINGX_VST_SYMBOL must not be empty")
    return value


def _interval_seconds() -> float:
    raw = os.environ.get(
        "NEXUS_RECONCILIATION_INTERVAL_SECONDS",
        str(DEFAULT_INTERVAL_SECONDS),
    )
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(
            "NEXUS_RECONCILIATION_INTERVAL_SECONDS must be numeric"
        ) from exc
    if value < 1.0:
        raise RuntimeError(
            "NEXUS_RECONCILIATION_INTERVAL_SECONDS must be >= 1"
        )
    return value


def _scope() -> ReconciliationAcquisitionScope:
    account_id = AccountId(
        venue_id=BINGX_VENUE_ID,
        value=_positive_int_env("NEXUS_ACCOUNT_VALUE", 1),
    )
    instrument_id = InstrumentId(
        venue_id=BINGX_VENUE_ID,
        native_symbol=_symbol(),
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )
    return ReconciliationAcquisitionScope(
        user_id=_positive_int_env("NEXUS_USER_ID", 1),
        account_id=account_id,
        instrument_id=instrument_id,
    )


def _build_runtime():
    database_url = _required_env("NEXUS_V2_DATABASE_URL")
    api_key = _required_env("BINGX_VST_API_KEY")
    secret_key = _required_env("BINGX_VST_SECRET_KEY")

    engine = create_persistence_engine(database_url)
    factory = create_session_factory(engine)

    local = SqlAlchemyLocalReconciliationSnapshotProvider(factory)

    transport = BingXVstReadOnlyHttpTransport(
        config=BingXVstHttpConfig(
            api_key=api_key,
            secret_key=secret_key,
        )
    )
    venue = BingXVenueAdapter(transport=transport)

    def evidence_factory(session):
        service = ExecutionLedgerPersistenceService(session)
        return LedgerReconciliationEvidenceAdapter(service)

    runtime = ReconciliationRuntime(
        session_factory=factory,
        local=local,
        evidence_factory=evidence_factory,
        venue=venue,
    )
    return engine, factory, runtime


async def _verify_v2_database(factory) -> None:
    """Fail closed unless the configured DB is already at V2 head.

    This runtime never creates, stamps, upgrades, or mutates schema.
    """
    async with factory() as session:
        result = await session.execute(
            text("SELECT version_num FROM alembic_version")
        )
        versions = tuple(result.scalars().all())

    if versions != (EXPECTED_ALEMBIC_HEAD,):
        raise RuntimeError(
            "NEXUS_V2_DATABASE_URL is not at required V2 Alembic head "
            f"{EXPECTED_ALEMBIC_HEAD}; observed={versions!r}"
        )


async def _run_once(runtime, scope) -> Phase3Snapshot:
    observed_at = datetime.now(UTC).isoformat()

    try:
        result = await runtime.run_once(scope)
    except Exception as exc:
        return Phase3Snapshot(
            observed_at=observed_at,
            source_state="UNAVAILABLE",
            reconciliation_gate_passed=False,
            ready=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    passed = result.reconciliation_gate_passed

    return Phase3Snapshot(
        observed_at=observed_at,
        source_state="CURRENT",
        reconciliation_gate_passed=passed,
        ready=passed,
        error=None if passed else "reconciliation_not_matched",
        strategy_execution_allowed=False,
        production_authority=False,
        writes_attempted=False,
    )


def reconciliation_loop(stop: threading.Event, runtime, scope) -> None:
    interval = _interval_seconds()

    while not stop.is_set():
        snapshot = asyncio.run(_run_once(runtime, scope))
        STATE.set(snapshot)
        stop.wait(interval)


def _payload(snapshot: Phase3Snapshot | None) -> dict[str, object]:
    base: dict[str, object] = {
        "service": "nexus-v2-core",
        "runtime_mode": "PHASE3_BINGX_VST_RECONCILIATION_OBSERVE_ONLY",
        "environment": "BINGX_VST",
        "symbol": _symbol(),
        "strategy_execution_allowed": False,
        "production_authority": False,
        "writes_attempted": False,
    }

    if snapshot is None:
        return {
            **base,
            "status": "STARTING",
            "ready": False,
            "reconciliation_gate_passed": False,
            "source_state": "UNKNOWN",
        }

    return {
        **base,
        **asdict(snapshot),
        "status": "RUNNING" if snapshot.ready else "DEGRADED",
    }


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-PHASE3-RECONCILIATION"

    def do_GET(self) -> None:
        payload = _payload(STATE.get())

        if self.path == "/health":
            code = 200
        elif self.path == "/ready":
            code = 200 if payload["ready"] else 503
        elif self.path == "/status":
            code = 200
        else:
            self.send_error(404)
            return

        encoded = json.dumps(
            payload,
            sort_keys=True,
        ).encode("utf-8")

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    # Validate all safety-critical configuration before binding HTTP.
    _required_env("NEXUS_V2_DATABASE_URL")
    _required_env("BINGX_VST_API_KEY")
    _required_env("BINGX_VST_SECRET_KEY")
    _symbol()
    _interval_seconds()
    scope = _scope()

    engine, factory, runtime = _build_runtime()

    # Database compatibility is checked before readiness/server startup.
    asyncio.run(_verify_v2_database(factory))

    stop = threading.Event()
    worker = threading.Thread(
        target=reconciliation_loop,
        args=(stop, runtime, scope),
        daemon=True,
    )
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
        asyncio.run(engine.dispose())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
