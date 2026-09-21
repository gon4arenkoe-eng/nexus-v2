from __future__ import annotations

import asyncio
from dataclasses import replace

from scripts.bingx_vst_observer_runtime import ObserverSnapshot
from scripts.phase14_bingx_shadow_runtime import (
    _payload,
    run_shadow_cycle,
)


def _observer_snapshot() -> ObserverSnapshot:
    return ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-21T14:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=0,
        position_count=0,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
    )


async def _observer_current() -> ObserverSnapshot:
    return _observer_snapshot()


async def _candidate_ok() -> dict[str, object]:
    return {
        "service": "nexus-v2-core",
        "mode": "SIMULATION_ONLY",
        "startup_reconciliation": "MATCHED",
        "strategy_execution_allowed": True,
        "portfolio_risk": "APPROVED",
        "execution_state": "COMPLETED",
        "order_status": "ACCEPTED",
        "post_execution_reconciliation": "MATCHED",
        "venue_writes": 1,
        "real_exchange_writes": 0,
        "production_authority": False,
        "status": "RUNNING",
    }


def test_shadow_cycle_combines_real_readonly_and_simulated_candidate() -> None:
    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
        )
    )

    assert snapshot.ready is True
    assert snapshot.environment == "BINGX_VST"
    assert snapshot.source_state == "CURRENT"

    assert snapshot.simulated_venue_writes == 1
    assert snapshot.real_exchange_writes == 0

    assert snapshot.production_authority is False
    assert snapshot.strategy_execution_allowed is False
    assert snapshot.writes_attempted is False

    # Foundation readiness must never claim full shadow parity closure.
    assert snapshot.shadow_gate_open is False
    assert snapshot.error is None


def test_shadow_cycle_fails_closed_when_real_observation_is_unavailable() -> None:
    async def unavailable() -> ObserverSnapshot:
        return replace(
            _observer_snapshot(),
            source_state="UNAVAILABLE",
        )

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=unavailable,
            candidate_runner=_candidate_ok,
        )
    )

    assert snapshot.ready is False
    assert snapshot.shadow_gate_open is False
    assert (
        snapshot.error
        == "bingx_observation_not_current_or_not_read_only"
    )


def test_shadow_cycle_fails_closed_if_candidate_reports_real_exchange_write() -> None:
    async def unsafe_candidate() -> dict[str, object]:
        candidate = await _candidate_ok()
        candidate["real_exchange_writes"] = 1
        return candidate

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=unsafe_candidate,
        )
    )

    assert snapshot.ready is False
    assert snapshot.real_exchange_writes == 1
    assert snapshot.shadow_gate_open is False
    assert (
        snapshot.error
        == "candidate_real_exchange_write_detected"
    )


def test_runtime_payload_never_exposes_live_authority() -> None:
    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
        )
    )

    payload = _payload(snapshot)

    assert payload["runtime_mode"] == (
        "PHASE14_BINGX_VST_SHADOW_READ_ONLY"
    )
    assert payload["ready"] is True
    assert payload["production_authority"] is False
    assert payload["strategy_execution_allowed"] is False
    assert payload["writes_attempted"] is False
    assert payload["shadow_gate_open"] is False
