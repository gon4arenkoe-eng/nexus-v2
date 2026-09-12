"""Tests for immutable reconciliation lifecycle/resolution evidence."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.ledger import ExecutionLedgerEventType
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancy,
    ReconciliationDiscrepancyKind,
    ReconciliationSourceState,
    ReconciliationSubject,
    build_reconciliation_result,
    reconciliation_discrepancy_id,
    reconciliation_run_id,
)
from infra.persistence.application.ledger import (
    ExecutionLedgerPersistenceService,
    LedgerPersistDisposition,
)
from infra.persistence.application.reconciliation_evidence import (
    persist_reconciliation_result,
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

INSTRUMENT = InstrumentId(
    venue_id=VENUE,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
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

    async def list_for_account(
        self,
        *,
        user_id: int,
        venue_id: str,
        account_value: int,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        events = [
            event
            for (owned_user, _), event
            in self.events.items()
            if (
                owned_user == user_id
                and event.venue_id == venue_id
                and event.account_value == account_value
            )
        ]

        return tuple(
            sorted(
                events,
                key=lambda event: (
                    event.occurred_at,
                    event.event_id,
                ),
            )
        )


def _service(
    repository: FakeLedgerRepository,
) -> ExecutionLedgerPersistenceService:
    return ExecutionLedgerPersistenceService(
        cast(AsyncSession, object()),
        repository=repository,
    )


def _discrepancy(
    observed_at: datetime,
) -> ReconciliationDiscrepancy:
    return ReconciliationDiscrepancy(
        kind=(
            ReconciliationDiscrepancyKind
            .VENUE_ORDER_UNKNOWN_LOCALLY
        ),
        subject=ReconciliationSubject.ORDER,
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=observed_at,
        venue_reference="venue-order-777",
    )


def _result(
    observed_at: datetime,
    *,
    discrepancies: tuple[
        ReconciliationDiscrepancy,
        ...,
    ] = (),
    source_state: ReconciliationSourceState = (
        ReconciliationSourceState.CURRENT
    ),
):
    return build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT,
        source_state=source_state,
        observed_at=observed_at,
        discrepancies=discrepancies,
        instrument_id=INSTRUMENT,
    )


def test_run_id_is_deterministic_per_scope_and_snapshot() -> None:
    first = reconciliation_run_id(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=NOW,
    )

    second = reconciliation_run_id(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=NOW,
    )

    later = reconciliation_run_id(
        user_id=11,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        observed_at=LATER,
    )

    assert first == second
    assert first != later


def test_discrepancy_id_survives_repeated_observation() -> None:
    first = _discrepancy(NOW)
    later = _discrepancy(LATER)

    assert (
        reconciliation_discrepancy_id(
            first,
            scope_instrument_id=INSTRUMENT,
        )
        == reconciliation_discrepancy_id(
            later,
            scope_instrument_id=INSTRUMENT,
        )
    )


def test_discrepancy_run_emits_started_found_completed() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)

        result = _result(
            NOW,
            discrepancies=(
                _discrepancy(NOW),
            ),
        )

        persisted = await persist_reconciliation_result(
            service,
            result,
        )

        return repository, persisted

    repository, persisted = asyncio.run(
        scenario()
    )

    assert tuple(
        item.event.event_type
        for item in persisted
    ) == (
        ExecutionLedgerEventType.RECONCILIATION_STARTED.value,
        (
            ExecutionLedgerEventType
            .RECONCILIATION_DISCREPANCY
            .value
        ),
        (
            ExecutionLedgerEventType
            .RECONCILIATION_COMPLETED
            .value
        ),
    )

    assert len(repository.events) == 3


def test_later_matched_run_emits_resolution() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)

        first = _result(
            NOW,
            discrepancies=(
                _discrepancy(NOW),
            ),
        )

        await persist_reconciliation_result(
            service,
            first,
        )

        matched = _result(
            LATER,
        )

        second = await persist_reconciliation_result(
            service,
            matched,
        )

        return repository, second

    repository, second = asyncio.run(
        scenario()
    )

    assert tuple(
        item.event.event_type
        for item in second
    ) == (
        ExecutionLedgerEventType.RECONCILIATION_STARTED.value,
        (
            ExecutionLedgerEventType
            .RECONCILIATION_RESOLVED
            .value
        ),
        (
            ExecutionLedgerEventType
            .RECONCILIATION_COMPLETED
            .value
        ),
    )

    resolved = second[1].event

    expected = str(
        reconciliation_discrepancy_id(
            _discrepancy(NOW),
            scope_instrument_id=INSTRUMENT,
        )
    )

    assert (
        resolved.payload["discrepancy_id"]
        == expected
    )

    assert len(repository.events) == 6


def test_non_current_run_emits_degraded_terminal() -> None:
    stale = ReconciliationDiscrepancy(
        kind=ReconciliationDiscrepancyKind.SOURCE_STALE,
        subject=ReconciliationSubject.SOURCE,
        user_id=11,
        account_id=ACCOUNT,
        observed_at=NOW,
    )

    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)

        result = _result(
            NOW,
            discrepancies=(stale,),
            source_state=ReconciliationSourceState.STALE,
        )

        return await persist_reconciliation_result(
            service,
            result,
        )

    persisted = asyncio.run(scenario())

    assert tuple(
        item.event.event_type
        for item in persisted
    ) == (
        ExecutionLedgerEventType.RECONCILIATION_STARTED.value,
        (
            ExecutionLedgerEventType
            .RECONCILIATION_DISCREPANCY
            .value
        ),
        (
            ExecutionLedgerEventType
            .RECONCILIATION_DEGRADED
            .value
        ),
    )


def test_retry_same_matched_run_is_idempotent() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)
        result = _result(NOW)

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


def test_resolution_retry_does_not_duplicate_evidence() -> None:
    async def scenario():
        repository = FakeLedgerRepository()
        service = _service(repository)

        await persist_reconciliation_result(
            service,
            _result(
                NOW,
                discrepancies=(
                    _discrepancy(NOW),
                ),
            ),
        )

        matched = _result(LATER)

        await persist_reconciliation_result(
            service,
            matched,
        )

        count_after_resolution = len(
            repository.events
        )

        retry = await persist_reconciliation_result(
            service,
            matched,
        )

        return (
            repository,
            count_after_resolution,
            retry,
        )

    repository, count_after_resolution, retry = (
        asyncio.run(scenario())
    )

    assert len(repository.events) == count_after_resolution

    assert all(
        item.disposition
        is LedgerPersistDisposition.DUPLICATE
        for item in retry
    )
