"""Tests for Phase 3 reconciliation Ledger persistence."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.ledger import ExecutionLedgerEventType
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancy,
    ReconciliationDiscrepancyKind,
    ReconciliationSubject,
)
from infra.persistence.application.ledger import (
    ExecutionLedgerPersistenceService,
    LedgerEventConflictError,
    LedgerPersistDisposition,
)
from infra.persistence.application.reconciliation_evidence import (
    persist_reconciliation_discrepancy,
    reconciliation_discrepancy_event_id,
    reconciliation_discrepancy_to_ledger_model,
)
from infra.persistence.models import ExecutionLedgerEventModel
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


def _discrepancy() -> ReconciliationDiscrepancy:
    return ReconciliationDiscrepancy(
        kind=(
            ReconciliationDiscrepancyKind
            .VENUE_ORDER_UNKNOWN_LOCALLY
        ),
        subject=ReconciliationSubject.ORDER,
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=NOW,
        venue_reference="venue-order-777",
    )


class FakeLedgerRepository:
    def __init__(self) -> None:
        self.events: dict[
            tuple[int, str],
            ExecutionLedgerEventModel,
        ] = {}

    async def add(
        self,
        event: ExecutionLedgerEventModel,
    ) -> ExecutionLedgerEventModel:
        self.events[
            (event.user_id, event.event_id)
        ] = event

        return event

    async def get_by_event_id(
        self,
        *,
        user_id: int,
        event_id: str,
    ) -> ExecutionLedgerEventModel | None:
        return self.events.get(
            (user_id, event_id)
        )


def _service(
    repository: FakeLedgerRepository,
) -> ExecutionLedgerPersistenceService:
    return ExecutionLedgerPersistenceService(
        cast(AsyncSession, object()),
        repository=repository,
    )


def test_event_id_is_deterministic() -> None:
    discrepancy = _discrepancy()

    assert (
        reconciliation_discrepancy_event_id(discrepancy)
        == reconciliation_discrepancy_event_id(discrepancy)
    )

    assert reconciliation_discrepancy_event_id(
        discrepancy
    ).startswith(
        "reconciliation-discrepancy:"
    )


def test_discrepancy_maps_to_planless_canonical_ledger_event() -> None:
    event = reconciliation_discrepancy_to_ledger_model(
        _discrepancy()
    )

    assert (
        event.event_type
        == ExecutionLedgerEventType
        .RECONCILIATION_DISCREPANCY
        .value
    )

    assert event.user_id == 11
    assert event.plan_id is None
    assert event.group_id is None
    assert event.leg_id is None
    assert event.order_id is None
    assert event.fill_id is None

    assert event.venue_id == "BINANCE"
    assert event.account_value == 7

    assert event.instrument_venue_id == "BINANCE"
    assert event.native_symbol == "BTCUSDT"
    assert event.instrument_type == "PERPETUAL"
    assert event.asset_class == "CRYPTO"

    assert event.occurred_at == NOW
    assert event.recorded_at == NOW

    assert event.payload == {
        "kind": "VENUE_ORDER_UNKNOWN_LOCALLY",
        "subject": "ORDER",
        "local_reference": None,
        "venue_reference": "venue-order-777",
        "local_value": None,
        "venue_value": None,
    }


def test_retry_is_idempotent_duplicate() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)
        discrepancy = _discrepancy()

        first = await persist_reconciliation_discrepancy(
            service,
            discrepancy,
        )

        second = await persist_reconciliation_discrepancy(
            service,
            discrepancy,
        )

        return repository, first, second

    repository, first, second = asyncio.run(
        scenario()
    )

    assert (
        first.disposition
        is LedgerPersistDisposition.APPENDED
    )

    assert (
        second.disposition
        is LedgerPersistDisposition.DUPLICATE
    )

    assert len(repository.events) == 1


def test_conflicting_existing_event_fails_closed() -> None:
    async def scenario() -> None:
        repository = FakeLedgerRepository()
        discrepancy = _discrepancy()

        existing = (
            reconciliation_discrepancy_to_ledger_model(
                discrepancy
            )
        )

        existing.payload = {
            "kind": "TAMPERED",
        }

        repository.events[
            (existing.user_id, existing.event_id)
        ] = existing

        service = _service(repository)

        await persist_reconciliation_discrepancy(
            service,
            discrepancy,
        )

    with pytest.raises(
        LedgerEventConflictError,
        match="conflicting immutable Ledger content",
    ):
        asyncio.run(scenario())


def test_source_discrepancy_does_not_invent_instrument() -> None:
    discrepancy = ReconciliationDiscrepancy(
        kind=ReconciliationDiscrepancyKind.SOURCE_STALE,
        subject=ReconciliationSubject.SOURCE,
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=None,
        observed_at=NOW,
    )

    event = reconciliation_discrepancy_to_ledger_model(
        discrepancy
    )

    assert event.plan_id is None
    assert event.venue_id == "BINANCE"
    assert event.account_value == 7
    assert event.instrument_venue_id is None
    assert event.native_symbol is None
    assert event.instrument_type is None
    assert event.asset_class is None
