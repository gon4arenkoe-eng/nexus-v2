from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from scripts import bingx_vst_observer_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bingx_vst_observer_runtime.py"


def test_runtime_source_has_no_write_path() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for marker in ("submit_order(", "cancel_order(", "allow_demo_writes=True", "ExecutionCoordinator"):
        assert marker not in text
    assert "BingXVstReadOnlyHttpTransport" in text


def test_runtime_authority_is_fail_closed() -> None:
    payload = runtime._payload(None)
    assert payload["ready"] is False
    assert payload["production_authority"] is False
    assert payload["strategy_execution_allowed"] is False


def test_current_snapshot_is_ready_but_not_execution_authorized() -> None:
    snapshot = runtime.ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-20T00:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=2,
        position_count=15,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
    )
    payload = runtime._payload(snapshot)
    assert payload["ready"] is True
    assert payload["status"] == "RUNNING"
    assert payload["strategy_execution_allowed"] is False


def test_failure_is_explicit_and_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BINGX_VST_SYMBOL", "BTCUSDT")
    snapshot = runtime._failed_snapshot(RuntimeError("venue unavailable"))
    payload = runtime._payload(snapshot)
    assert snapshot.source_state == "UNAVAILABLE"
    assert payload["status"] == "DEGRADED"
    assert payload["ready"] is False
    assert "venue unavailable" in str(payload["error"])


def test_interval_rejects_subsecond_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_OBSERVER_INTERVAL_SECONDS", "0.5")
    with pytest.raises(RuntimeError, match=">= 1"):
        runtime._interval_seconds()


def test_secret_values_are_not_part_of_snapshot_contract() -> None:
    fields = runtime.ObserverSnapshot.__dataclass_fields__
    assert "api_key" not in fields
    assert "secret_key" not in fields
    assert "signature" not in fields


def test_observer_is_long_running_not_one_shot() -> None:
    source = inspect.getsource(runtime.observer_loop)
    assert "while not stop.is_set()" in source
    assert "stop.wait(interval)" in source
