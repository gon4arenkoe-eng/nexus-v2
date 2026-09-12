"""Deterministic repeated Phase 3 reconciliation cycles."""

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
from apps.core.ports.venue_account import VenueAccountState

from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)


class ContinuousReconciliationError(RuntimeError):
    """A deterministic continuous reconciliation cycle is invalid."""


class ReconciliationPassRunnerPort(Protocol):
    """Persisted reconciliation-pass boundary used by each cycle."""

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
        venue_account: VenueAccountState | None = None,
    ) -> ReconciliationResult:
        """Return only after immutable reconciliation evidence persists."""

        ...


@dataclass(frozen=True, slots=True)
class ContinuousReconciliationInput:
    """One account/instrument snapshot inside a runtime cycle."""

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
    venue_account: VenueAccountState | None = None


@dataclass(frozen=True, slots=True)
class ContinuousReconciliationReceipt:
    """One persisted reconciliation result inside a cycle."""

    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    result: ReconciliationResult


@dataclass(frozen=True, slots=True)
class ContinuousReconciliationCycle:
    """Completed deterministic runtime reconciliation cycle."""

    receipts: tuple[ContinuousReconciliationReceipt, ...]

    @property
    def all_matched(self) -> bool:
        return bool(self.receipts) and all(
            receipt.result.state
            is ReconciliationResultState.MATCHED
            for receipt in self.receipts
        )


def _scope_key(
    item: ContinuousReconciliationInput,
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


class ContinuousReconciliationRunner:
    """Run deterministic persisted reconciliation cycles while live."""

    def __init__(
        self,
        runner: ReconciliationPassRunnerPort,
    ) -> None:
        self._runner = runner

    async def run_cycle(
        self,
        passes: tuple[ContinuousReconciliationInput, ...],
    ) -> ContinuousReconciliationCycle:
        """Run one complete reconciliation cycle without auto-correction."""

        if not isinstance(passes, tuple):
            raise ValueError(
                "continuous reconciliation passes must be a tuple"
            )

        if not passes:
            raise ContinuousReconciliationError(
                "continuous reconciliation requires at least one scope"
            )

        for item in passes:
            if not isinstance(
                item,
                ContinuousReconciliationInput,
            ):
                raise ValueError(
                    "passes must contain "
                    "ContinuousReconciliationInput values"
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
            raise ContinuousReconciliationError(
                "duplicate continuous reconciliation scope"
            )

        receipts: list[
            ContinuousReconciliationReceipt
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
                venue_account=item.venue_account,
            )

            if result.user_id != item.user_id:
                raise ContinuousReconciliationError(
                    "reconciliation result user ownership mismatch"
                )

            if result.account_id != item.account_id:
                raise ContinuousReconciliationError(
                    "reconciliation result account ownership mismatch"
                )

            receipts.append(
                ContinuousReconciliationReceipt(
                    user_id=item.user_id,
                    account_id=item.account_id,
                    instrument_id=item.instrument_id,
                    result=result,
                )
            )

        return ContinuousReconciliationCycle(
            receipts=tuple(receipts),
        )
