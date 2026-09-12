"""Persist canonical reconciliation evidence in the Execution Ledger."""

from __future__ import annotations

from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.ledger import ExecutionLedgerEventType
from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancy,
    ReconciliationResult,
    reconciliation_discrepancy_key,
)
from infra.persistence.application.ledger import (
    ExecutionLedgerPersistenceService,
    LedgerPersistResult,
)
from infra.persistence.models import ExecutionLedgerEventModel


_EVENT_ID_PREFIX = "reconciliation-discrepancy"


def reconciliation_discrepancy_event_id(
    discrepancy: ReconciliationDiscrepancy,
) -> str:
    """Return stable identity for one immutable discrepancy observation."""

    material = "\x1f".join(
        reconciliation_discrepancy_key(discrepancy)
    )

    digest = sha256(
        material.encode("utf-8")
    ).hexdigest()

    return f"{_EVENT_ID_PREFIX}:{digest}"


def reconciliation_discrepancy_to_ledger_model(
    discrepancy: ReconciliationDiscrepancy,
) -> ExecutionLedgerEventModel:
    """Map canonical discrepancy evidence into the canonical Ledger."""

    instrument = discrepancy.instrument_id

    return ExecutionLedgerEventModel(
        event_id=reconciliation_discrepancy_event_id(
            discrepancy
        ),
        event_type=(
            ExecutionLedgerEventType
            .RECONCILIATION_DISCREPANCY
            .value
        ),
        event_version=1,
        user_id=discrepancy.user_id,
        plan_id=None,
        group_id=None,
        leg_id=None,
        order_id=None,
        fill_id=None,
        venue_id=str(
            discrepancy.account_id.venue_id
        ),
        account_value=discrepancy.account_id.value,
        instrument_venue_id=(
            str(instrument.venue_id)
            if instrument is not None
            else None
        ),
        native_symbol=(
            instrument.native_symbol
            if instrument is not None
            else None
        ),
        instrument_type=(
            instrument.instrument_type.value
            if instrument is not None
            else None
        ),
        asset_class=(
            instrument.asset_class.value
            if instrument is not None
            else None
        ),
        source="reconciliation",
        correlation_id=None,
        causation_id=None,
        occurred_at=discrepancy.observed_at,
        recorded_at=discrepancy.observed_at,
        sequence_no=None,
        evidence_source="reconciliation_detector",
        evidence_quality=None,
        schema_version=1,
        payload={
            "kind": discrepancy.kind.value,
            "subject": discrepancy.subject.value,
            "local_reference": discrepancy.local_reference,
            "venue_reference": discrepancy.venue_reference,
            "local_value": discrepancy.local_value,
            "venue_value": discrepancy.venue_value,
        },
    )


async def _no_projection_mutation(
    _session: AsyncSession,
) -> None:
    """Reconciliation evidence has no destructive projection mutation."""

    return None


async def persist_reconciliation_discrepancy(
    service: ExecutionLedgerPersistenceService,
    discrepancy: ReconciliationDiscrepancy,
) -> LedgerPersistResult:
    """Persist discrepancy through existing idempotent Ledger boundary."""

    event = reconciliation_discrepancy_to_ledger_model(
        discrepancy
    )

    return await service.persist(
        event=event,
        mutate_projection=_no_projection_mutation,
    )


async def persist_reconciliation_result(
    service: ExecutionLedgerPersistenceService,
    result: ReconciliationResult,
) -> tuple[LedgerPersistResult, ...]:
    """Persist all discrepancies from one deterministic pass."""

    persisted: list[LedgerPersistResult] = []

    for discrepancy in result.discrepancies:
        persisted.append(
            await persist_reconciliation_discrepancy(
                service,
                discrepancy,
            )
        )

    return tuple(persisted)


class LedgerReconciliationEvidenceAdapter:
    """Connect Core reconciliation orchestration to canonical Ledger."""

    def __init__(
        self,
        service: ExecutionLedgerPersistenceService,
    ) -> None:
        self._service = service

    async def persist_result(
        self,
        result: ReconciliationResult,
    ) -> None:
        """Persist all immutable evidence before pass completion."""

        await persist_reconciliation_result(
            self._service,
            result,
        )
