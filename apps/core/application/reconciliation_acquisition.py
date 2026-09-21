"""Acquire canonical local and venue truth for one reconciliation scope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from apps.core.application.startup_reconciliation import (
    StartupReconciliationInput,
)
from apps.core.domain.reconciliation import ReconciliationSourceState
from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshotProvider,
)
from apps.core.ports.venue import VenueAdapter
from packages.contracts.identities import AccountId, InstrumentId


@dataclass(frozen=True, slots=True)
class ReconciliationAcquisitionScope:
    """One owned user/account/instrument reconciliation scope."""

    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId


class StartupReconciliationAcquisition:
    """Acquire canonical local + venue observations without mutation."""

    def __init__(
        self,
        *,
        local: LocalReconciliationSnapshotProvider,
        venue: VenueAdapter,
    ) -> None:
        self._local = local
        self._venue = venue

    async def acquire(
        self,
        scope: ReconciliationAcquisitionScope,
    ) -> StartupReconciliationInput:
        """Return one startup input or fail closed on acquisition error."""

        if not isinstance(scope, ReconciliationAcquisitionScope):
            raise ValueError(
                "scope must be ReconciliationAcquisitionScope"
            )

        if scope.user_id <= 0:
            raise ValueError("user_id must be positive")

        if scope.account_id.venue_id != scope.instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

        local = await self._local.load(
            user_id=scope.user_id,
            account_id=scope.account_id,
            instrument_id=scope.instrument_id,
        )

        # Venue reads are intentionally sequential. A single observed_at is
        # captured only after all required canonical observations succeeded.
        # Any exception escapes: callers must remain fail-closed.
        venue_account = await self._venue.get_account_state(
            account_id=scope.account_id,
        )
        venue_orders = await self._venue.get_open_orders(
            account_id=scope.account_id,
            instrument_id=scope.instrument_id,
        )
        venue_positions_all = await self._venue.get_positions(
            account_id=scope.account_id,
        )
        venue_fills = await self._venue.get_fills(
            account_id=scope.account_id,
            instrument_id=scope.instrument_id,
        )

        venue_positions = tuple(
            position
            for position in venue_positions_all
            if position.account_id == scope.account_id
            and position.instrument_id == scope.instrument_id
        )

        observed_at = datetime.now(timezone.utc)

        return StartupReconciliationInput(
            user_id=scope.user_id,
            account_id=scope.account_id,
            instrument_id=scope.instrument_id,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=observed_at,
            local_orders=local.orders,
            venue_orders=venue_orders,
            local_fills=local.fills,
            venue_fills=venue_fills,
            local_positions=local.positions,
            venue_positions=venue_positions,
            venue_account=venue_account,
        )
