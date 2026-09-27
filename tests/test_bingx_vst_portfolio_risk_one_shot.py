from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from scripts import bingx_vst_portfolio_risk_one_shot as runner
from scripts.bingx_vst_observer_runtime import ObserverSnapshot


def _snapshot() -> ObserverSnapshot:
    return ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-27T18:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=2,
        position_count=1,
        fill_count=3,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
        portfolio_risk_recording="PASS",
        portfolio_risk_snapshot_id="a" * 64,
    )


def _overview() -> dict[str, object]:
    return {
        "workspace_id": "workspace-test",
        "user_id": 7,
        "portfolio_state": "CURRENT",
        "risk_state": "HALTED",
        "portfolio": {
            "equity": "100000",
            "gross_exposure": "31000",
            "net_exposure": "31000",
            "margin_used": "3100",
        },
        "risk": {"headline_utilization": "0.31"},
    }


def test_one_shot_requires_explicit_recording_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEXUS_VST_PORTFOLIO_RISK_RECORDING", raising=False)
    with pytest.raises(RuntimeError, match="must be ENABLED"):
        runner._required_opt_in()


def test_one_shot_rejects_any_execution_authority() -> None:
    unsafe = replace(_snapshot(), production_authority=True)
    with pytest.raises(RuntimeError, match="production_authority is true"):
        runner._require_safe_observation(unsafe)


def test_one_shot_rejects_missing_control_plane_readback() -> None:
    overview = _overview()
    overview["portfolio"] = None
    with pytest.raises(RuntimeError, match="portfolio readback is unavailable"):
        runner._require_control_plane_readback(overview)


def test_one_shot_runs_once_and_reports_zero_exchange_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEXUS_VST_PORTFOLIO_RISK_RECORDING", "ENABLED")

    calls = {"observe": 0, "readback": 0}

    async def fake_observe_once() -> ObserverSnapshot:
        calls["observe"] += 1
        return _snapshot()

    async def fake_load_overview() -> dict[str, object]:
        calls["readback"] += 1
        return _overview()

    monkeypatch.setattr(runner, "observe_once", fake_observe_once)
    monkeypatch.setattr(runner, "_load_overview", fake_load_overview)

    result = asyncio.run(runner.run_once())

    assert calls == {"observe": 1, "readback": 1}
    assert result["status"] == "PASS"
    assert result["portfolio_risk_recording"] == "PASS"
    assert result["portfolio_risk_snapshot_id"] == "a" * 64
    assert result["portfolio_state"] == "CURRENT"
    assert result["risk_state"] == "HALTED"
    assert result["real_exchange_writes"] == 0
    assert result["writes_attempted"] is False
    assert result["production_authority"] is False
    assert result["strategy_execution_allowed"] is False
