from __future__ import annotations

import asyncio
import threading

import pytest

from apps.core.application.reconciliation_runtime import (
    ReconciliationRuntimeResult,
)
from scripts import phase3_bingx_vst_reconciliation_runtime as target


class _Runtime:
    def __init__(self, *, passed=True, error=None):
        self.passed = passed
        self.error = error
        self.calls = 0

    async def run_once(self, scope):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return ReconciliationRuntimeResult(
            reconciliation_gate_passed=self.passed,
            strategy_execution_allowed=False,
            production_authority=False,
            writes_attempted=False,
        )


@pytest.mark.asyncio
async def test_run_once_ready_only_when_reconciliation_gate_passes():
    snapshot = await target._run_once(
        _Runtime(passed=True),
        object(),
    )

    assert snapshot.ready is True
    assert snapshot.reconciliation_gate_passed is True
    assert snapshot.source_state == "CURRENT"
    assert snapshot.strategy_execution_allowed is False
    assert snapshot.production_authority is False
    assert snapshot.writes_attempted is False


@pytest.mark.asyncio
async def test_run_once_nonmatched_is_fail_closed():
    snapshot = await target._run_once(
        _Runtime(passed=False),
        object(),
    )

    assert snapshot.ready is False
    assert snapshot.reconciliation_gate_passed is False
    assert snapshot.error == "reconciliation_not_matched"
    assert snapshot.strategy_execution_allowed is False


@pytest.mark.asyncio
async def test_run_once_exception_is_unavailable_and_fail_closed():
    snapshot = await target._run_once(
        _Runtime(error=RuntimeError("venue unavailable")),
        object(),
    )

    assert snapshot.ready is False
    assert snapshot.source_state == "UNAVAILABLE"
    assert snapshot.reconciliation_gate_passed is False
    assert "venue unavailable" in snapshot.error
    assert snapshot.production_authority is False
    assert snapshot.writes_attempted is False


def test_payload_starting_is_not_ready(monkeypatch):
    monkeypatch.setenv("BINGX_VST_SYMBOL", "BTCUSDT")

    payload = target._payload(None)

    assert payload["status"] == "STARTING"
    assert payload["ready"] is False
    assert payload["reconciliation_gate_passed"] is False
    assert payload["strategy_execution_allowed"] is False
    assert payload["production_authority"] is False
    assert payload["writes_attempted"] is False


def test_payload_ready_comes_from_reconciliation(monkeypatch):
    monkeypatch.setenv("BINGX_VST_SYMBOL", "BTCUSDT")

    snapshot = target.Phase3Snapshot(
        observed_at="2026-09-21T00:00:00+00:00",
        source_state="CURRENT",
        reconciliation_gate_passed=True,
        ready=True,
        error=None,
    )

    payload = target._payload(snapshot)

    assert payload["ready"] is True
    assert payload["reconciliation_gate_passed"] is True
    assert payload["strategy_execution_allowed"] is False
    assert payload["production_authority"] is False
    assert payload["writes_attempted"] is False


@pytest.mark.asyncio
async def test_database_head_mismatch_fails_closed():
    class _Result:
        class _Scalars:
            def all(self):
                return ["legacy-revision"]

        def scalars(self):
            return self._Scalars()

    class _Session:
        async def execute(self, statement):
            return _Result()

    class _Context:
        async def __aenter__(self):
            return _Session()

        async def __aexit__(self, exc_type, exc, traceback):
            return None

    with pytest.raises(
        RuntimeError,
        match="not at required V2 Alembic head",
    ):
        await target._verify_v2_database(lambda: _Context())


def test_runtime_source_has_no_schema_migration_or_venue_write_calls():
    source = open(target.__file__, encoding="utf-8-sig").read()

    forbidden = (
        "alembic upgrade",
        "alembic stamp",
        ".submit_order(",
        ".cancel_order(",
        "BingXVstControlledWriteHttpTransport",
    )

    for value in forbidden:
        assert value not in source


def test_loop_repeats_reconciliation(monkeypatch):
    runtime = _Runtime(passed=True)
    stop = threading.Event()

    monkeypatch.setattr(target, "_interval_seconds", lambda: 1.0)

    original_set = target.STATE.set

    def set_and_stop(snapshot):
        original_set(snapshot)
        if runtime.calls >= 2:
            stop.set()

    monkeypatch.setattr(target.STATE, "set", set_and_stop)

    original_wait = stop.wait

    def immediate_wait(timeout):
        if runtime.calls < 2:
            return False
        return original_wait(0)

    monkeypatch.setattr(stop, "wait", immediate_wait)

    class FakeEngine:
        async def dispose(self) -> None:
            return None

    async def fake_verify(factory) -> None:
        return None

    monkeypatch.setattr(target, "_verify_v2_database", fake_verify)

    thread = threading.Thread(
        target=target.reconciliation_loop,
        args=(stop, object(), runtime, object(), FakeEngine()),
    )
    thread.start()
    thread.join(timeout=3)

    assert not thread.is_alive()
    assert runtime.calls >= 2


def test_reconciliation_loop_uses_one_event_loop_for_verify_runs_and_dispose(
    monkeypatch,
) -> None:
    stop = threading.Event()
    loop_ids: list[int] = []
    calls: list[str] = []

    class FakeEngine:
        async def dispose(self) -> None:
            loop_ids.append(id(asyncio.get_running_loop()))
            calls.append("dispose")

    async def fake_verify(factory) -> None:
        loop_ids.append(id(asyncio.get_running_loop()))
        calls.append("verify")

    async def fake_run_once(runtime, scope):
        loop_ids.append(id(asyncio.get_running_loop()))
        calls.append("run")
        if calls.count("run") == 2:
            stop.set()
        return target.Phase3Snapshot(
            observed_at="2026-09-21T00:00:00+00:00",
            source_state="CURRENT",
            reconciliation_gate_passed=True,
            ready=True,
            error=None,
            strategy_execution_allowed=False,
            production_authority=False,
            writes_attempted=False,
        )

    monkeypatch.setattr(target, "_verify_v2_database", fake_verify)
    monkeypatch.setattr(target, "_run_once", fake_run_once)
    monkeypatch.setattr(target, "_interval_seconds", lambda: 0.0)

    target.reconciliation_loop(
        stop,
        object(),
        object(),
        object(),
        FakeEngine(),
    )

    assert calls == ["verify", "run", "run", "dispose"]
    assert len(set(loop_ids)) == 1
