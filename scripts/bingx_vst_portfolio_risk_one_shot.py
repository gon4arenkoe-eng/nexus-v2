"""One-shot BingX VST Portfolio/Risk producer validation.

This runner performs exactly one read-only BingX VST observation, requires the
Portfolio/Risk recorder opt-in to be enabled, verifies the canonical snapshot
was persisted, verifies the Control Plane can read it back, and exits.

It deliberately has no order-write transport or execution authority.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from scripts.bingx_vst_observer_runtime import ObserverSnapshot, observe_once
from scripts.control_plane_readonly_runtime import _load_overview


def _required_opt_in() -> None:
    value = os.environ.get(
        "NEXUS_VST_PORTFOLIO_RISK_RECORDING",
        "DISABLED",
    ).strip().upper()
    if value != "ENABLED":
        raise RuntimeError(
            "NEXUS_VST_PORTFOLIO_RISK_RECORDING must be ENABLED for one-shot validation"
        )


def _require_safe_observation(snapshot: ObserverSnapshot) -> None:
    failures: list[str] = []
    if snapshot.environment != "BINGX_VST":
        failures.append("environment is not BINGX_VST")
    if snapshot.source_state != "CURRENT":
        failures.append("source_state is not CURRENT")
    for field_name in (
        "account_query",
        "open_orders_query",
        "positions_query",
        "fills_query",
    ):
        if getattr(snapshot, field_name) != "PASS":
            failures.append(f"{field_name} is not PASS")
    if snapshot.writes_attempted:
        failures.append("writes_attempted is true")
    if snapshot.production_authority:
        failures.append("production_authority is true")
    if snapshot.strategy_execution_allowed:
        failures.append("strategy_execution_allowed is true")
    if snapshot.portfolio_risk_recording != "PASS":
        failures.append("portfolio_risk_recording is not PASS")
    if not snapshot.portfolio_risk_snapshot_id:
        failures.append("portfolio_risk_snapshot_id is missing")
    if snapshot.portfolio_risk_recording_error:
        failures.append("portfolio_risk_recording_error is present")
    if failures:
        raise RuntimeError("; ".join(failures))


def _require_control_plane_readback(overview: dict[str, Any]) -> None:
    portfolio = overview.get("portfolio")
    risk = overview.get("risk")
    if not isinstance(portfolio, dict):
        raise RuntimeError("Control Plane portfolio readback is unavailable")
    if not isinstance(risk, dict):
        raise RuntimeError("Control Plane risk readback is unavailable")
    if str(overview.get("portfolio_state", "UNAVAILABLE")).upper() == "UNAVAILABLE":
        raise RuntimeError("Control Plane portfolio_state is UNAVAILABLE")
    if str(overview.get("risk_state", "UNAVAILABLE")).upper() == "UNAVAILABLE":
        raise RuntimeError("Control Plane risk_state is UNAVAILABLE")


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


async def run_once() -> dict[str, Any]:
    _required_opt_in()
    snapshot = await observe_once()
    _require_safe_observation(snapshot)

    overview = await _load_overview()
    _require_control_plane_readback(overview)

    portfolio = overview["portfolio"]
    risk = overview["risk"]
    assert isinstance(portfolio, dict)
    assert isinstance(risk, dict)

    return {
        "service": "nexus-v2-portfolio-risk-one-shot",
        "status": "PASS",
        "environment": snapshot.environment,
        "symbol": snapshot.symbol,
        "observed_at": snapshot.observed_at,
        "source_state": snapshot.source_state,
        "account_query": snapshot.account_query,
        "open_orders_query": snapshot.open_orders_query,
        "positions_query": snapshot.positions_query,
        "fills_query": snapshot.fills_query,
        "open_order_count": snapshot.open_order_count,
        "position_count": snapshot.position_count,
        "fill_count": snapshot.fill_count,
        "portfolio_risk_recording": snapshot.portfolio_risk_recording,
        "portfolio_risk_snapshot_id": snapshot.portfolio_risk_snapshot_id,
        "portfolio_state": overview["portfolio_state"],
        "risk_state": overview["risk_state"],
        "equity": portfolio["equity"],
        "gross_exposure": portfolio["gross_exposure"],
        "net_exposure": portfolio["net_exposure"],
        "margin_used": portfolio["margin_used"],
        "headline_risk_utilization": risk["headline_utilization"],
        "real_exchange_writes": 0,
        "writes_attempted": False,
        "production_authority": False,
        "strategy_execution_allowed": False,
    }


def main() -> int:
    try:
        result = asyncio.run(run_once())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "service": "nexus-v2-portfolio-risk-one-shot",
                    "status": "FAIL",
                    "error": f"{type(exc).__name__}: {exc}",
                    "real_exchange_writes": 0,
                    "production_authority": False,
                    "strategy_execution_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, default=_json_default, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
