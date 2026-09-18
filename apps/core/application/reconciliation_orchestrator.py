"""Canonical Phase 3 reconciliation pass orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.core.application.reconciliation_detector import (
    detect_reconciliation,
)
from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
)
from apps.core.domain.positions import PositionLeg
from apps.core.domain.reconciliation import (
    ReconciliationResult,
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


class ReconciliationEvidencePort(Protocol):
    """Persistence boundary required by reconciliation orchestration."""

    async def persist_result(
        self,
        result: ReconciliationResult,
    ) -> None:
        """Persist immutable reconciliation evidence or fail."""

        ...


class ReconciliationPassOrchestrator:
    """Run one deterministic account/instrument reconciliation pass."""

    def __init__(
        self,
        evidence: ReconciliationEvidencePort,
    ) -> None:
        self._evidence = evidence

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
        order_comparison_local_orders: tuple[ExecutionOrder, ...] | None = None,
        venue_fills: tuple[VenueFill, ...],
        local_positions: tuple[PositionLeg, ...],
        venue_positions: tuple[VenuePosition, ...],
        venue_account: VenueAccountState | None = None,
    ) -> ReconciliationResult:
        """Detect, persist evidence, then expose completed pass result."""

        result = detect_reconciliation(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            source_state=source_state,
            observed_at=observed_at,
            local_orders=local_orders,
            venue_orders=venue_orders,
            local_fills=local_fills,
            venue_fills=venue_fills,
            order_comparison_local_orders=order_comparison_local_orders,
            local_positions=local_positions,
            venue_positions=venue_positions,
            venue_account=venue_account,
        )

        await self._evidence.persist_result(result)

        return result
