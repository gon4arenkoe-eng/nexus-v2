"""Tests for canonical Phase 3 reconciliation pass orchestration."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import inspect

import pytest

from apps.core.application.reconciliation_orchestrator import (
    ReconciliationPassOrchestrator,
)
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from infra.persistence.application.reconciliation_evidence import (
    LedgerReconciliationEvidenceAdapter,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


NOW = datetime(
    2026,
    9,
    12,
    12,
    0,
    tzinfo=UTC,
)

VENUE = VenueId("BINANCE")

ACCOUNT = AccountId(
    venue_id=VENUE,
    value=7,
)

INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


class RecordingEvidencePort:
    def __init__(
        self,
        *,
        fail: bool = False,
    ) -> None:
        self.fail = fail
        self.results: list[ReconciliationResult] = []

    async def persist_result(
        self,
        result: ReconciliationResult,
    ) -> None:
        self.results.append(result)

        if self.fail:
            raise RuntimeError(
                "evidence persistence unavailable"
            )


def _run(
    evidence: RecordingEvidencePort,
    *,
    source_state: ReconciliationSourceState,
) -> ReconciliationResult:
    async def scenario() -> ReconciliationResult:
        orchestrator = ReconciliationPassOrchestrator(
            evidence
        )

        return await orchestrator.run(
            user_id=11,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            source_state=source_state,
            observed_at=NOW,
            local_orders=(),
            venue_orders=(),
            local_fills=(),
            venue_fills=(),
            local_positions=(),
            venue_positions=(),
        )

    return asyncio.run(scenario())


def test_non_current_pass_persists_evidence_before_return() -> None:
    evidence = RecordingEvidencePort()

    result = _run(
        evidence,
        source_state=ReconciliationSourceState.STALE,
    )

    assert result.state is ReconciliationResultState.STALE
    assert len(result.discrepancies) == 1

    assert evidence.results == [
        result,
    ]


def test_matched_pass_crosses_evidence_boundary_before_return() -> None:
    evidence = RecordingEvidencePort()

    result = _run(
        evidence,
        source_state=ReconciliationSourceState.CURRENT,
    )

    assert result.state is ReconciliationResultState.MATCHED
    assert result.discrepancies == ()

    assert evidence.results == [
        result,
    ]


def test_evidence_failure_fails_closed() -> None:
    evidence = RecordingEvidencePort(
        fail=True,
    )

    with pytest.raises(
        RuntimeError,
        match="evidence persistence unavailable",
    ):
        _run(
            evidence,
            source_state=ReconciliationSourceState.STALE,
        )

    assert len(evidence.results) == 1


def test_ledger_adapter_delegates_complete_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = RecordingEvidencePort()

    result = _run(
        evidence,
        source_state=ReconciliationSourceState.STALE,
    )

    calls = []

    async def fake_persist(
        service,
        received: ReconciliationResult,
    ):
        calls.append(
            (service, received)
        )
        return ()

    import infra.persistence.application.reconciliation_evidence as module

    monkeypatch.setattr(
        module,
        "persist_reconciliation_result",
        fake_persist,
    )

    service = object()

    adapter = LedgerReconciliationEvidenceAdapter(
        service  # type: ignore[arg-type]
    )

    asyncio.run(
        adapter.persist_result(result)
    )

    assert calls == [
        (service, result),
    ]


def test_orchestrator_has_no_infrastructure_or_execution_authority() -> None:
    import apps.core.application.reconciliation_orchestrator as module

    source = inspect.getsource(module)

    forbidden = (
        "sqlalchemy",
        "AsyncSession",
        "ExecutionLedgerPersistenceService",
        "infra.persistence",
        "submit_order(",
        "cancel_order(",
        "ExecutionCoordinator",
        ".commit(",
        ".rollback(",
    )

    assert not any(
        item in source
        for item in forbidden
    )
