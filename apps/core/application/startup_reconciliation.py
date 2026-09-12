"""Fail-closed startup reconciliation readiness for strategy execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
)
from apps.core.domain.positions import PositionLeg
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.venue import (
    VenueFill,
    VenueOrderResult,
    VenuePosition,
)
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)


class StartupReconciliationGateError(RuntimeError):
    """Startup reconciliation cannot produce a safe readiness decision."""


class ReconciliationPassRunnerPort(Protocol):
    """Completed reconciliation-pass boundary required by startup gate."""

    async def run(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
        source_state: ReconciliationSourceState,
        observed_at: datetime,
        local_orders: tuple[ExecutionOrder, ...],
        venue_orders: tuple[VenueOrderResult, ...],
        local_fills: tuple[ExecutionFill, ...],
        venue_fills: tuple[VenueFill, ...],
        local_positions: tuple[PositionLeg, ...],
        venue_positions: tuple[VenuePosition, ...],
    ) -> ReconciliationResult:
        """Return only after immutable reconciliation evidence persists."""

        ...


@dataclass(frozen=True, slots=True)
class StartupReconciliationInput:
    """One required account/instrument startup reconciliation scope."""

    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    source_state: ReconciliationSourceState
    observed_at: datetime
    local_orders: tuple[ExecutionOrder, ...] = ()
    venue_orders: tuple[VenueOrderResult, ...] = ()
    local_fills: tuple[ExecutionFill, ...] = ()
    venue_fills: tuple[VenueFill, ...] = ()
    local_positions: tuple[PositionLeg, ...] = ()
    venue_positions: tuple[VenuePosition, ...] = ()


@dataclass(frozen=True, slots=True)
class StartupReconciliationReceipt:
    """One startup pass which crossed the persisted-evidence boundary."""

    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    result: ReconciliationResult


@dataclass(frozen=True, slots=True)
class StartupReconciliationDecision:
    """Fail-closed readiness result for strategy execution."""

    strategy_execution_allowed: bool
    receipts: tuple[StartupReconciliationReceipt, ...]


def _scope_key(
    item: StartupReconciliationInput,
) -> tuple[int, str, int, str, str, str, str]:
    instrument = item.instrument_id

    return (
        item.user_id,
        str(item.account_id.venue_id),
        item.account_id.value,
        str(instrument.venue_id),
        instrument.native_symbol,
        instrument.instrument_type.value,
        instrument.asset_class.value,
    )


class StartupReconciliationActivationGate:
    """Require persisted MATCHED startup reconciliation before activation."""

    def __init__(
        self,
        runner: ReconciliationPassRunnerPort,
    ) -> None:
        self._runner = runner

    async def evaluate(
        self,
        passes: tuple[StartupReconciliationInput, ...],
    ) -> StartupReconciliationDecision:
        """Run all required startup scopes and return readiness."""

        if not isinstance(passes, tuple):
            raise ValueError(
                "startup reconciliation passes must be a tuple"
            )

        if not passes:
            raise StartupReconciliationGateError(
                "startup reconciliation requires at least one scope"
            )

        for item in passes:
            if not isinstance(
                item,
                StartupReconciliationInput,
            ):
                raise ValueError(
                    "passes must contain "
                    "StartupReconciliationInput values"
                )

        ordered = tuple(
            sorted(
                passes,
                key=_scope_key,
            )
        )

        scope_keys = tuple(
            _scope_key(item)
            for item in ordered
        )

        if len(scope_keys) != len(set(scope_keys)):
            raise StartupReconciliationGateError(
                "duplicate startup reconciliation scope"
            )

        receipts: list[
            StartupReconciliationReceipt
        ] = []

        for item in ordered:
            result = await self._runner.run(
                user_id=item.user_id,
                account_id=item.account_id,
                instrument_id=item.instrument_id,
                source_state=item.source_state,
                observed_at=item.observed_at,
                local_orders=item.local_orders,
                venue_orders=item.venue_orders,
                local_fills=item.local_fills,
                venue_fills=item.venue_fills,
                local_positions=item.local_positions,
                venue_positions=item.venue_positions,
            )

            if result.user_id != item.user_id:
                raise StartupReconciliationGateError(
                    "reconciliation result user ownership mismatch"
                )

            if result.account_id != item.account_id:
                raise StartupReconciliationGateError(
                    "reconciliation result account ownership mismatch"
                )

            receipts.append(
                StartupReconciliationReceipt(
                    user_id=item.user_id,
                    account_id=item.account_id,
                    instrument_id=item.instrument_id,
                    result=result,
                )
            )

        allowed = all(
            receipt.result.state
            is ReconciliationResultState.MATCHED
            for receipt in receipts
        )

        return StartupReconciliationDecision(
            strategy_execution_allowed=allowed,
            receipts=tuple(receipts),
        )
