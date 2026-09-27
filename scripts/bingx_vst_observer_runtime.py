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
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from adapters.bingx.http_transport import BingXVstHttpConfig, BingXVstReadOnlyHttpTransport
from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from apps.core.application.portfolio_risk_recording import (
    build_portfolio_risk_snapshot,
)
from apps.core.domain.portfolio_risk import (
    PortfolioRiskLimits,
    PortfolioRiskState,
)
from infra.persistence.repositories.portfolio_risk_snapshot import (
    PortfolioRiskSnapshotRepository,
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
    portfolio_risk_recording: str = "DISABLED"
    portfolio_risk_snapshot_id: str | None = None
    portfolio_risk_recording_error: str | None = None
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


def _risk_recording_enabled() -> bool:
    return (
        os.environ.get(
            "NEXUS_VST_PORTFOLIO_RISK_RECORDING",
            "DISABLED",
        ).strip().upper()
        == "ENABLED"
    )


def _required_decimal_mapping(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception as exc:
        raise RuntimeError(
            f"invalid Portfolio Risk limit: {field_name}"
        ) from exc
    if not parsed.is_finite():
        raise RuntimeError(
            f"invalid Portfolio Risk limit: {field_name}"
        )
    return parsed


def _portfolio_risk_limits() -> PortfolioRiskLimits:
    raw = _required_env("NEXUS_PORTFOLIO_RISK_LIMITS_JSON")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "NEXUS_PORTFOLIO_RISK_LIMITS_JSON must be valid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            "NEXUS_PORTFOLIO_RISK_LIMITS_JSON must be an object"
        )

    required = (
        "max_open_position_groups",
        "max_gross_exposure",
        "max_net_exposure",
        "max_account_exposure",
        "max_venue_exposure",
        "max_strategy_exposure",
        "max_instrument_exposure",
        "max_currency_concentration",
        "max_correlation_cluster_exposure",
        "max_leverage",
        "max_margin_utilization",
        "max_daily_drawdown",
        "max_rolling_drawdown",
        "max_order_liquidity_ratio",
        "max_expected_slippage_bps",
    )
    missing = tuple(name for name in required if name not in payload)
    if missing:
        raise RuntimeError(
            "missing Portfolio Risk limits: " + ",".join(missing)
        )

    try:
        max_groups = int(payload["max_open_position_groups"])
    except Exception as exc:
        raise RuntimeError(
            "max_open_position_groups must be an integer"
        ) from exc

    decimal_fields = {
        name: _required_decimal_mapping(
            payload[name],
            field_name=name,
        )
        for name in required
        if name != "max_open_position_groups"
    }
    hedge_tolerance = _required_decimal_mapping(
        payload.get("hedge_tolerance", "0.05"),
        field_name="hedge_tolerance",
    )
    return PortfolioRiskLimits(
        max_open_position_groups=max_groups,
        hedge_tolerance=hedge_tolerance,
        **decimal_fields,
    )


def _risk_user_id() -> int:
    value = int(_required_env("NEXUS_CONTROL_PLANE_USER_ID"))
    if value <= 0:
        raise RuntimeError("NEXUS_CONTROL_PLANE_USER_ID must be positive")
    return value


def _risk_stale_after() -> timedelta:
    seconds = float(
        os.environ.get(
            "NEXUS_PORTFOLIO_RISK_STALE_SECONDS",
            "90",
        )
    )
    if seconds <= 0:
        raise RuntimeError(
            "NEXUS_PORTFOLIO_RISK_STALE_SECONDS must be positive"
        )
    return timedelta(seconds=seconds)


async def _record_portfolio_risk_snapshot(
    *,
    account,
    positions,
) -> str:
    database_url = _required_env("NEXUS_V2_DATABASE_URL")
    user_id = _risk_user_id()
    limits = _portfolio_risk_limits()
    equity_asset = os.environ.get(
        "NEXUS_VST_EQUITY_ASSET",
        "VST",
    ).strip().upper()
    if not equity_asset:
        raise RuntimeError("NEXUS_VST_EQUITY_ASSET must be non-empty")

    engine = create_persistence_engine(database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            repository = PortfolioRiskSnapshotRepository(session)
            previous = await repository.latest_for_user(user_id=user_id)
            snapshot = build_portfolio_risk_snapshot(
                user_id=user_id,
                account_state=account,
                positions=positions,
                equity_asset=equity_asset,
                trading_state=PortfolioRiskState.HALTED,
                now=datetime.now(UTC),
                stale_after=_risk_stale_after(),
                previous_snapshot=(
                    previous.snapshot if previous is not None else None
                ),
            )
            snapshot_id = await repository.append(
                snapshot=snapshot,
                limits=limits,
                source="BINGX_VST_OBSERVER_REAL",
                recorded_at=datetime.now(UTC),
            )
            await session.commit()
            return snapshot_id
    finally:
        await engine.dispose()


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

    portfolio_risk_recording = "DISABLED"
    portfolio_risk_snapshot_id = None
    portfolio_risk_recording_error = None
    if _risk_recording_enabled():
        try:
            portfolio_risk_snapshot_id = (
                await _record_portfolio_risk_snapshot(
                    account=account,
                    positions=positions,
                )
            )
            portfolio_risk_recording = "PASS"
        except Exception as exc:
            portfolio_risk_recording = "FAIL"
            portfolio_risk_recording_error = (
                f"{type(exc).__name__}: {exc}"
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
        portfolio_risk_recording=portfolio_risk_recording,
        portfolio_risk_snapshot_id=portfolio_risk_snapshot_id,
        portfolio_risk_recording_error=portfolio_risk_recording_error,
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
    ready = (
        snapshot.source_state == "CURRENT"
        and snapshot.portfolio_risk_recording != "FAIL"
    )
    data.update(
        {
            "service": "nexus-v2-core",
            "runtime_mode": "BINGX_VST_OBSERVE_ONLY",
            "status": "RUNNING" if ready else "DEGRADED",
            "ready": ready,
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
