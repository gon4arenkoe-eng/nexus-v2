"""Tests for deterministic Phase 3 continuous reconciliation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
import inspect

import pytest

from apps.core.application.continuous_reconciliation import (
    ContinuousReconciliationError,
    ContinuousReconciliationInput,
    ContinuousReconciliationRunner,
)
from apps.core.application.reconciliation_orchestrator import (
    ReconciliationPassOrchestrator,
)
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.venue import (
    VenueOrderResult,
    VenueOrderState,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueId,
    VenueOrderId,
)


NOW = datetime(
    2026,
    9,
    12,
    12,
    0,
    tzinfo=UTC,
)

LATER = datetime(
    2026,
    9,
    12,
    12,
    1,
    tzinfo=UTC,
)

VENUE = VenueId("BINANCE")

ACCOUNT = AccountId(
    venue_id=VENUE,
    value=7,
)

BTC = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)

ETH = InstrumentId(
    venue_id=VENUE,
    native_symbol="ETHUSDT",
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
                "continuous evidence persistence unavailable"
            )


def _input(
    instrument: InstrumentId = BTC,
    *,
    source_state: ReconciliationSourceState = (
        ReconciliationSourceState.CURRENT
    ),
    observed_at: datetime = NOW,
    venue_orders: tuple[VenueOrderResult, ...] = (),
) -> ContinuousReconciliationInput:
    return ContinuousReconciliationInput(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=instrument,
        source_state=source_state,
        observed_at=observed_at,
        venue_orders=venue_orders,
    )


def _external_order() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId(
            "external-client"
        ),
        venue_order_id=VenueOrderId(
            "external-order"
        ),
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        rejection_reason=None,
    )


def _run_cycle(
    evidence: RecordingEvidencePort,
    passes: tuple[ContinuousReconciliationInput, ...],
):
    async def scenario():
        pass_runner = ReconciliationPassOrchestrator(
            evidence
        )

        continuous = ContinuousReconciliationRunner(
            pass_runner
        )

        return await continuous.run_cycle(passes)

    return asyncio.run(scenario())


def test_cycle_is_deterministically_scope_ordered() -> None:
    evidence = RecordingEvidencePort()

    cycle = _run_cycle(
        evidence,
        (
            _input(ETH),
            _input(BTC),
        ),
    )

    assert tuple(
        receipt.instrument_id.native_symbol
        for receipt in cycle.receipts
    ) == (
        "BTCUSDT",
        "ETHUSDT",
    )

    assert cycle.all_matched is True
    assert len(evidence.results) == 2


def test_non_current_state_remains_explicit() -> None:
    evidence = RecordingEvidencePort()

    cycle = _run_cycle(
        evidence,
        (
            _input(
                source_state=(
                    ReconciliationSourceState.STALE
                )
            ),
        ),
    )

    assert cycle.all_matched is False

    assert (
        cycle.receipts[0].result.state
        is ReconciliationResultState.STALE
    )

    assert len(evidence.results) == 1


def test_runtime_discrepancy_is_detected_and_persisted() -> None:
    evidence = RecordingEvidencePort()

    cycle = _run_cycle(
        evidence,
        (
            _input(
                venue_orders=(
                    _external_order(),
                ),
            ),
        ),
    )

    assert cycle.all_matched is False

    assert (
        cycle.receipts[0].result.state
        is ReconciliationResultState.DISCREPANCY
    )

    assert len(
        cycle.receipts[0].result.discrepancies
    ) == 1

    assert len(evidence.results) == 1


def test_repeated_equal_cycle_is_deterministic() -> None:
    first_evidence = RecordingEvidencePort()
    second_evidence = RecordingEvidencePort()

    passes = (
        _input(ETH),
        _input(BTC),
    )

    first = _run_cycle(
        first_evidence,
        passes,
    )

    second = _run_cycle(
        second_evidence,
        tuple(reversed(passes)),
    )

    assert first == second


def test_later_cycle_can_observe_new_drift() -> None:
    evidence = RecordingEvidencePort()

    first = _run_cycle(
        evidence,
        (
            _input(
                observed_at=NOW,
            ),
        ),
    )

    second = _run_cycle(
        evidence,
        (
            _input(
                observed_at=LATER,
                venue_orders=(
                    _external_order(),
                ),
            ),
        ),
    )

    assert first.all_matched is True
    assert second.all_matched is False

    assert (
        second.receipts[0].result.state
        is ReconciliationResultState.DISCREPANCY
    )

    assert len(evidence.results) == 2


def test_evidence_failure_fails_cycle_closed() -> None:
    evidence = RecordingEvidencePort(
        fail=True,
    )

    with pytest.raises(
        RuntimeError,
        match="continuous evidence persistence unavailable",
    ):
        _run_cycle(
            evidence,
            (_input(),),
        )

    assert len(evidence.results) == 1


def test_duplicate_scope_fails_closed() -> None:
    evidence = RecordingEvidencePort()

    with pytest.raises(
        ContinuousReconciliationError,
        match="duplicate continuous reconciliation scope",
    ):
        _run_cycle(
            evidence,
            (
                _input(),
                _input(),
            ),
        )

    assert evidence.results == []


def test_empty_cycle_fails_closed() -> None:
    evidence = RecordingEvidencePort()

    with pytest.raises(
        ContinuousReconciliationError,
        match="requires at least one scope",
    ):
        _run_cycle(
            evidence,
            (),
        )

    assert evidence.results == []


def test_continuous_runner_has_no_execution_or_infra_authority() -> None:
    import apps.core.application.continuous_reconciliation as module

    source = inspect.getsource(module)

    forbidden = (
        "sqlalchemy",
        "AsyncSession",
        "infra.persistence",
        "ExecutionLedgerPersistenceService",
        "submit_order(",
        "cancel_order(",
        "ExecutionCoordinator",
        ".commit(",
        ".rollback(",
        "asyncio.sleep",
        "while True",
    )

    assert not any(
        item in source
        for item in forbidden
    )
