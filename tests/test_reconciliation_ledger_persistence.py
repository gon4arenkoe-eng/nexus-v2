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
    ReconciliationSourceState,
    ReconciliationSubject,
    build_reconciliation_result,
)
from infra.persistence.application.ledger import (
    ExecutionLedgerPersistenceService,
    LedgerEventConflictError,
    LedgerPersistDisposition,
)
from infra.persistence.application.reconciliation_evidence import (
    persist_reconciliation_discrepancy,
    persist_reconciliation_result,
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


def _result_with_two_discrepancies():
    first = ReconciliationDiscrepancy(
        kind=(
            ReconciliationDiscrepancyKind
            .VENUE_ORDER_UNKNOWN_LOCALLY
        ),
        subject=ReconciliationSubject.ORDER,
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=NOW,
        venue_reference="venue-order-z",
    )

    second = ReconciliationDiscrepancy(
        kind=(
            ReconciliationDiscrepancyKind
            .LOCAL_ORDER_MISSING_ON_VENUE
        ),
        subject=ReconciliationSubject.ORDER,
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=NOW,
        local_reference="local-order-a",
    )

    return build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        discrepancies=(
            first,
            second,
        ),
    )


def test_result_batch_persists_in_canonical_order() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)
        result = _result_with_two_discrepancies()

        persisted = await persist_reconciliation_result(
            service,
            result,
        )

        return result, persisted, repository

    result, persisted, repository = asyncio.run(
        scenario()
    )

    expected_ids = tuple(
        reconciliation_discrepancy_event_id(item)
        for item in result.discrepancies
    )

    actual_ids = tuple(
        item.event.event_id
        for item in persisted
    )

    assert actual_ids == expected_ids

    assert all(
        item.disposition
        is LedgerPersistDisposition.APPENDED
        for item in persisted
    )

    assert len(repository.events) == 2


def test_repeated_result_batch_is_fully_idempotent() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)
        result = _result_with_two_discrepancies()

        first = await persist_reconciliation_result(
            service,
            result,
        )

        second = await persist_reconciliation_result(
            service,
            result,
        )

        return repository, first, second

    repository, first, second = asyncio.run(
        scenario()
    )

    assert all(
        item.disposition
        is LedgerPersistDisposition.APPENDED
        for item in first
    )

    assert all(
        item.disposition
        is LedgerPersistDisposition.DUPLICATE
        for item in second
    )

    assert len(repository.events) == 2


def test_matched_result_writes_no_discrepancy_events() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)

        result = build_reconciliation_result(
            user_id=11,
            account_id=ACCOUNT,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=NOW,
            discrepancies=(),
        )

        persisted = await persist_reconciliation_result(
            service,
            result,
        )

        return repository, persisted

    repository, persisted = asyncio.run(
        scenario()
    )

    assert persisted == ()
    assert repository.events == {}
