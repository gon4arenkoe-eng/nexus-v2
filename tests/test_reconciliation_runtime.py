from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
)
from apps.core.application.reconciliation_runtime import (
    ReconciliationRuntime,
)
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _scope():
    venue_id = VenueId("BINGX")
    account_id = AccountId(
        venue_id=venue_id,
        value=1,
    )
    instrument_id = InstrumentId(
        venue_id=venue_id,
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )
    return ReconciliationAcquisitionScope(
        user_id=1,
        account_id=account_id,
        instrument_id=instrument_id,
    )


@dataclass
class _Snapshot:
    orders: tuple = ()
    fills: tuple = ()
    positions: tuple = ()


class _Local:
    def __init__(self, events):
        self.events = events

    async def load(self, *, user_id, account_id, instrument_id):
        self.events.append("snapshot_loaded")
        return _Snapshot()


class _Venue:
    def __init__(self, events):
        self.events = events

    async def get_account_state(self, *, account_id):
        self.events.append("venue_account")
        return None

    async def get_open_orders(self, *, account_id, instrument_id=None):
        self.events.append("venue_orders")
        return ()

    async def get_positions(self, *, account_id):
        self.events.append("venue_positions")
        return ()

    async def get_fills(
        self,
        *,
        account_id,
        instrument_id=None,
        since=None,
    ):
        self.events.append("venue_fills")
        return ()

    async def submit_order(self, request):
        raise AssertionError("venue write attempted")

    async def cancel_order(
        self,
        *,
        account_id,
        instrument_id,
        venue_order_id,
    ):
        raise AssertionError("venue write attempted")


class _Session:
    def __init__(self, events):
        self.events = events

    @asynccontextmanager
    async def begin(self):
        self.events.append("transaction_begin")
        try:
            yield self
        except Exception:
            self.events.append("transaction_rollback")
            raise
        else:
            self.events.append("transaction_commit")


class _SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return None


class _Evidence:
    def __init__(self, events):
        self.events = events

    async def persist_result(self, result):
        self.events.append("evidence_persisted")


async def _matched_run(self, **kwargs):
    result = ReconciliationResult(
        user_id=kwargs["user_id"],
        account_id=kwargs["account_id"],
        instrument_id=kwargs["instrument_id"],
        source_state=ReconciliationSourceState.CURRENT,
        state=ReconciliationResultState.MATCHED,
        observed_at=kwargs["observed_at"],
        discrepancies=(),
    )
    await self._evidence.persist_result(result)
    return result


@pytest.mark.asyncio
async def test_runtime_acquires_before_evidence_transaction(monkeypatch):
    events = []
    session = _Session(events)

    from apps.core.application import reconciliation_orchestrator

    monkeypatch.setattr(
        reconciliation_orchestrator.ReconciliationPassOrchestrator,
        "run",
        _matched_run,
    )

    runtime = ReconciliationRuntime(
        session_factory=lambda: _SessionContext(session),
        local=_Local(events),
        evidence_factory=lambda _session: _Evidence(events),
        venue=_Venue(events),
    )

    result = await runtime.run_once(_scope())

    assert events == [
        "snapshot_loaded",
        "venue_account",
        "venue_orders",
        "venue_positions",
        "venue_fills",
        "transaction_begin",
        "evidence_persisted",
        "transaction_commit",
    ]

    assert result.reconciliation_gate_passed is True
    assert result.strategy_execution_allowed is False
    assert result.production_authority is False
    assert result.writes_attempted is False


@pytest.mark.asyncio
async def test_runtime_does_not_open_evidence_transaction_if_acquisition_fails():
    events = []
    session = _Session(events)

    class FailingVenue(_Venue):
        async def get_open_orders(
            self,
            *,
            account_id,
            instrument_id=None,
        ):
            self.events.append("venue_orders")
            raise RuntimeError("venue unavailable")

    runtime = ReconciliationRuntime(
        session_factory=lambda: _SessionContext(session),
        local=_Local(events),
        evidence_factory=lambda _session: _Evidence(events),
        venue=FailingVenue(events),
    )

    with pytest.raises(RuntimeError, match="venue unavailable"):
        await runtime.run_once(_scope())

    assert events == [
        "snapshot_loaded",
        "venue_account",
        "venue_orders",
    ]
    assert "transaction_begin" not in events


@pytest.mark.asyncio
async def test_runtime_rolls_back_if_evidence_persistence_fails(monkeypatch):
    events = []
    session = _Session(events)

    from apps.core.application import reconciliation_orchestrator

    monkeypatch.setattr(
        reconciliation_orchestrator.ReconciliationPassOrchestrator,
        "run",
        _matched_run,
    )

    class FailingEvidence:
        async def persist_result(self, result):
            events.append("evidence_failed")
            raise RuntimeError("evidence persistence failed")

    runtime = ReconciliationRuntime(
        session_factory=lambda: _SessionContext(session),
        local=_Local(events),
        evidence_factory=lambda _session: FailingEvidence(),
        venue=_Venue(events),
    )

    with pytest.raises(
        RuntimeError,
        match="evidence persistence failed",
    ):
        await runtime.run_once(_scope())

    assert "transaction_begin" in events
    assert "evidence_failed" in events
    assert "transaction_rollback" in events
    assert "transaction_commit" not in events


@pytest.mark.asyncio
async def test_runtime_never_promotes_reconciliation_to_execution_authority(
    monkeypatch,
):
    events = []
    session = _Session(events)

    from apps.core.application import reconciliation_orchestrator

    monkeypatch.setattr(
        reconciliation_orchestrator.ReconciliationPassOrchestrator,
        "run",
        _matched_run,
    )

    runtime = ReconciliationRuntime(
        session_factory=lambda: _SessionContext(session),
        local=_Local(events),
        evidence_factory=lambda _session: _Evidence(events),
        venue=_Venue(events),
    )

    result = await runtime.run_once(_scope())

    assert result.reconciliation_gate_passed is True
    assert result.strategy_execution_allowed is False
    assert result.production_authority is False
    assert result.writes_attempted is False
