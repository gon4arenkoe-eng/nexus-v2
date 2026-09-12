"""Phase 3 venue account observation and reconciliation tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.application.reconciliation_detector import (
    ReconciliationDetectionError,
    detect_reconciliation,
)
from apps.core.application.reconciliation_orchestrator import (
    ReconciliationPassOrchestrator,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
    StartupReconciliationInput,
)
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancyKind,
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
    VenueAccountState,
    VenueBalance,
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

OTHER_ACCOUNT = AccountId(
    venue_id=VENUE,
    value=8,
)

INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)


def _account_state(
    state: VenueAccountObservationState,
    *,
    account_id: AccountId = ACCOUNT,
) -> VenueAccountState:
    balances = ()

    if state is not VenueAccountObservationState.UNAVAILABLE:
        balances = (
            VenueBalance(
                asset="USDT",
                total=Decimal("1000"),
                available=Decimal("750"),
            ),
        )

    return VenueAccountState(
        account_id=account_id,
        state=state,
        observed_at=NOW,
        balances=balances,
    )


def _detect(
    venue_account: VenueAccountState | None,
):
    return detect_reconciliation(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        local_orders=(),
        venue_orders=(),
        local_fills=(),
        venue_fills=(),
        local_positions=(),
        venue_positions=(),
        venue_account=venue_account,
    )


def test_account_balances_are_deterministically_ordered() -> None:
    account = VenueAccountState(
        account_id=ACCOUNT,
        state=VenueAccountObservationState.CURRENT,
        observed_at=NOW,
        balances=(
            VenueBalance(
                asset="USDT",
                total=Decimal("1000"),
                available=Decimal("750"),
            ),
            VenueBalance(
                asset="BTC",
                total=Decimal("1"),
                available=Decimal("0.5"),
            ),
        ),
    )

    assert tuple(
        balance.asset
        for balance in account.balances
    ) == (
        "BTC",
        "USDT",
    )


def test_duplicate_balance_asset_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate asset",
    ):
        VenueAccountState(
            account_id=ACCOUNT,
            state=VenueAccountObservationState.CURRENT,
            observed_at=NOW,
            balances=(
                VenueBalance(
                    asset="USDT",
                    total=Decimal("1"),
                    available=Decimal("1"),
                ),
                VenueBalance(
                    asset="USDT",
                    total=Decimal("2"),
                    available=Decimal("2"),
                ),
            ),
        )


def test_unavailable_account_cannot_invent_balances() -> None:
    with pytest.raises(
        ValueError,
        match="cannot carry balances",
    ):
        VenueAccountState(
            account_id=ACCOUNT,
            state=VenueAccountObservationState.UNAVAILABLE,
            observed_at=NOW,
            balances=(
                VenueBalance(
                    asset="USDT",
                    total=Decimal("1"),
                    available=Decimal("1"),
                ),
            ),
        )


def test_current_account_observation_is_clean() -> None:
    result = _detect(
        _account_state(
            VenueAccountObservationState.CURRENT
        )
    )

    assert result.state is ReconciliationResultState.MATCHED
    assert result.discrepancies == ()


def test_stale_account_balance_is_explicit_discrepancy() -> None:
    result = _detect(
        _account_state(
            VenueAccountObservationState.STALE
        )
    )

    assert result.state is ReconciliationResultState.DISCREPANCY

    assert tuple(
        item.kind
        for item in result.discrepancies
    ) == (
        ReconciliationDiscrepancyKind.ACCOUNT_BALANCE_STALE,
    )

    assert result.discrepancies[0].instrument_id is None


def test_unavailable_account_balance_is_explicit_discrepancy() -> None:
    result = _detect(
        _account_state(
            VenueAccountObservationState.UNAVAILABLE
        )
    )

    assert result.state is ReconciliationResultState.DISCREPANCY

    assert tuple(
        item.kind
        for item in result.discrepancies
    ) == (
        (
            ReconciliationDiscrepancyKind
            .ACCOUNT_BALANCE_UNAVAILABLE
        ),
    )


def test_account_observation_ownership_mismatch_fails_closed() -> None:
    with pytest.raises(
        ReconciliationDetectionError,
        match="outside reconciliation scope",
    ):
        _detect(
            _account_state(
                VenueAccountObservationState.CURRENT,
                account_id=OTHER_ACCOUNT,
            )
        )


class RecordingEvidence:
    def __init__(self) -> None:
        self.results: list[ReconciliationResult] = []

    async def persist_result(
        self,
        result: ReconciliationResult,
    ) -> None:
        self.results.append(result)


def test_startup_gate_blocks_stale_account_balance() -> None:
    async def scenario():
        evidence = RecordingEvidence()

        runner = ReconciliationPassOrchestrator(
            evidence
        )

        gate = StartupReconciliationActivationGate(
            runner
        )

        decision = await gate.evaluate(
            (
                StartupReconciliationInput(
                    user_id=11,
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    source_state=(
                        ReconciliationSourceState.CURRENT
                    ),
                    observed_at=NOW,
                    venue_account=_account_state(
                        VenueAccountObservationState.STALE
                    ),
                ),
            )
        )

        return evidence, decision

    evidence, decision = asyncio.run(
        scenario()
    )

    assert decision.strategy_execution_allowed is False

    assert (
        decision.receipts[0].result.state
        is ReconciliationResultState.DISCREPANCY
    )

    assert len(evidence.results) == 1


def test_startup_gate_allows_current_account_balance() -> None:
    async def scenario():
        evidence = RecordingEvidence()

        runner = ReconciliationPassOrchestrator(
            evidence
        )

        gate = StartupReconciliationActivationGate(
            runner
        )

        decision = await gate.evaluate(
            (
                StartupReconciliationInput(
                    user_id=11,
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    source_state=(
                        ReconciliationSourceState.CURRENT
                    ),
                    observed_at=NOW,
                    venue_account=_account_state(
                        VenueAccountObservationState.CURRENT
                    ),
                ),
            )
        )

        return decision

    decision = asyncio.run(scenario())

    assert decision.strategy_execution_allowed is True
