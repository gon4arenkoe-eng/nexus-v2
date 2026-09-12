"""Tests for fail-closed Phase 3 startup reconciliation readiness."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
import inspect

import pytest

from apps.core.application.reconciliation_orchestrator import (
    ReconciliationPassOrchestrator,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
    StartupReconciliationGateError,
    StartupReconciliationInput,
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
                "startup evidence persistence unavailable"
            )


def _input(
    instrument: InstrumentId = BTC,
    *,
    source_state: ReconciliationSourceState = (
        ReconciliationSourceState.CURRENT
    ),
    venue_orders: tuple[VenueOrderResult, ...] = (),
) -> StartupReconciliationInput:
    return StartupReconciliationInput(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=instrument,
        source_state=source_state,
        observed_at=NOW,
        venue_orders=venue_orders,
    )


def _external_order() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId(
            "external-client"
        ),
        venue_order_id=VenueOrderId(
            "external-venue-order"
        ),
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        rejection_reason=None,
    )


def _evaluate(
    evidence: RecordingEvidencePort,
    passes: tuple[StartupReconciliationInput, ...],
):
    async def scenario():
        runner = ReconciliationPassOrchestrator(
            evidence
        )

        gate = StartupReconciliationActivationGate(
            runner
        )

        return await gate.evaluate(passes)

    return asyncio.run(scenario())


def test_all_required_matched_passes_allow_strategy_execution() -> None:
    evidence = RecordingEvidencePort()

    decision = _evaluate(
        evidence,
        (
            _input(ETH),
            _input(BTC),
        ),
    )

    assert decision.strategy_execution_allowed is True

    assert tuple(
        receipt.instrument_id.native_symbol
        for receipt in decision.receipts
    ) == (
        "BTCUSDT",
        "ETHUSDT",
    )

    assert all(
        receipt.result.state
        is ReconciliationResultState.MATCHED
        for receipt in decision.receipts
    )

    assert len(evidence.results) == 2


def test_stale_startup_pass_blocks_strategy_execution() -> None:
    evidence = RecordingEvidencePort()

    decision = _evaluate(
        evidence,
        (
            _input(
                source_state=(
                    ReconciliationSourceState.STALE
                )
            ),
        ),
    )

    assert decision.strategy_execution_allowed is False

    assert (
        decision.receipts[0].result.state
        is ReconciliationResultState.STALE
    )

    assert len(evidence.results) == 1


def test_discrepancy_blocks_strategy_execution() -> None:
    evidence = RecordingEvidencePort()

    decision = _evaluate(
        evidence,
        (
            _input(
                venue_orders=(
                    _external_order(),
                ),
            ),
        ),
    )

    assert decision.strategy_execution_allowed is False

    assert (
        decision.receipts[0].result.state
        is ReconciliationResultState.DISCREPANCY
    )

    assert len(evidence.results) == 1


def test_evidence_failure_never_returns_activation_decision() -> None:
    evidence = RecordingEvidencePort(
        fail=True,
    )

    with pytest.raises(
        RuntimeError,
        match="startup evidence persistence unavailable",
    ):
        _evaluate(
            evidence,
            (_input(),),
        )

    assert len(evidence.results) == 1


def test_duplicate_required_scope_fails_closed() -> None:
    evidence = RecordingEvidencePort()

    with pytest.raises(
        StartupReconciliationGateError,
        match="duplicate startup reconciliation scope",
    ):
        _evaluate(
            evidence,
            (
                _input(),
                _input(),
            ),
        )

    assert evidence.results == []


def test_empty_startup_scope_set_fails_closed() -> None:
    evidence = RecordingEvidencePort()

    with pytest.raises(
        StartupReconciliationGateError,
        match="requires at least one scope",
    ):
        _evaluate(
            evidence,
            (),
        )

    assert evidence.results == []


def test_gate_has_no_infrastructure_or_execution_authority() -> None:
    import apps.core.application.startup_reconciliation as module

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
    )

    assert not any(
        item in source
        for item in forbidden
    )
