from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
    StartupReconciliationInput,
)
from apps.core.application.startup_reconciliation_service import (
    StartupReconciliationService,
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


def _identity():
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
    return account_id, instrument_id


class _Acquisition:
    def __init__(self) -> None:
        self.calls = []

    async def acquire(self, scope):
        self.calls.append(scope)

        return StartupReconciliationInput(
            user_id=scope.user_id,
            account_id=scope.account_id,
            instrument_id=scope.instrument_id,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=datetime.now(timezone.utc),
        )


@dataclass
class _Runner:
    state: ReconciliationResultState

    async def run(
        self,
        *,
        user_id,
        account_id,
        instrument_id,
        source_state,
        observed_at,
        local_orders,
        venue_orders,
        local_fills,
        venue_fills,
        order_comparison_local_orders=None,
        local_positions,
        venue_positions,
        venue_account=None,
    ):
        effective_source_state = source_state

        if self.state is ReconciliationResultState.UNKNOWN:
            effective_source_state = ReconciliationSourceState.UNKNOWN

        return ReconciliationResult(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            source_state=effective_source_state,
            state=self.state,
            observed_at=observed_at,
            discrepancies=(),
        )


@pytest.mark.asyncio
async def test_service_allows_only_matched_startup_reconciliation():
    account_id, instrument_id = _identity()

    acquisition = _Acquisition()

    service = StartupReconciliationService(
        acquisition=acquisition,
        gate=StartupReconciliationActivationGate(
            _Runner(ReconciliationResultState.MATCHED)
        ),
    )

    decision = await service.evaluate(
        (
            ReconciliationAcquisitionScope(
                user_id=1,
                account_id=account_id,
                instrument_id=instrument_id,
            ),
        )
    )

    assert decision.strategy_execution_allowed is True
    assert len(decision.receipts) == 1
    assert len(acquisition.calls) == 1


@pytest.mark.asyncio
async def test_service_fails_closed_for_non_matched_result():
    account_id, instrument_id = _identity()

    service = StartupReconciliationService(
        acquisition=_Acquisition(),
        gate=StartupReconciliationActivationGate(
            _Runner(ReconciliationResultState.UNKNOWN)
        ),
    )

    decision = await service.evaluate(
        (
            ReconciliationAcquisitionScope(
                user_id=1,
                account_id=account_id,
                instrument_id=instrument_id,
            ),
        )
    )

    assert decision.strategy_execution_allowed is False


@pytest.mark.asyncio
async def test_service_does_not_run_gate_when_acquisition_fails():
    account_id, instrument_id = _identity()

    class FailingAcquisition:
        async def acquire(self, scope):
            raise RuntimeError("venue unavailable")

    class ForbiddenRunner:
        async def run(self, **kwargs):
            raise AssertionError(
                "reconciliation gate ran after acquisition failure"
            )

    service = StartupReconciliationService(
        acquisition=FailingAcquisition(),
        gate=StartupReconciliationActivationGate(
            ForbiddenRunner()
        ),
    )

    with pytest.raises(RuntimeError, match="venue unavailable"):
        await service.evaluate(
            (
                ReconciliationAcquisitionScope(
                    user_id=1,
                    account_id=account_id,
                    instrument_id=instrument_id,
                ),
            )
        )
