"""Persist canonical reconciliation evidence in the Execution Ledger."""

from __future__ import annotations

from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.ledger import ExecutionLedgerEventType
from apps.core.domain.reconciliation import (
    DiscrepancyId,
    ReconciliationDiscrepancy,
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationRunId,
    reconciliation_discrepancy_id,
    reconciliation_discrepancy_key,
    reconciliation_run_id,
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


_DEGRADED_RESULT_STATES = frozenset(
    {
        ReconciliationResultState.STALE,
        ReconciliationResultState.DEGRADED,
        ReconciliationResultState.UNAVAILABLE,
        ReconciliationResultState.UNKNOWN,
    }
)


def _stable_lifecycle_event_id(
    prefix: str,
    *parts: str,
) -> str:
    material = "\x1f".join(parts)

    digest = sha256(
        material.encode("utf-8")
    ).hexdigest()

    return f"{prefix}:{digest}"


def _reconciliation_scope_key(
    result: ReconciliationResult,
) -> str:
    instrument = result.instrument_id

    if instrument is None:
        raise ValueError(
            "lifecycle reconciliation requires instrument_id"
        )

    return "|".join(
        (
            str(result.user_id),
            str(result.account_id.venue_id),
            str(result.account_id.value),
            str(instrument.venue_id),
            instrument.native_symbol,
            instrument.instrument_type.value,
            instrument.asset_class.value,
        )
    )


def _run_id(
    result: ReconciliationResult,
) -> ReconciliationRunId:
    instrument = result.instrument_id

    if instrument is None:
        raise ValueError(
            "lifecycle reconciliation requires instrument_id"
        )

    return reconciliation_run_id(
        user_id=result.user_id,
        account_id=result.account_id,
        instrument_id=instrument,
        observed_at=result.observed_at,
    )


def _run_event_model(
    result: ReconciliationResult,
    *,
    run_id: ReconciliationRunId,
    event_type: ExecutionLedgerEventType,
    sequence_no: int,
) -> ExecutionLedgerEventModel:
    instrument = result.instrument_id

    if instrument is None:
        raise ValueError(
            "lifecycle reconciliation requires instrument_id"
        )

    scope = _reconciliation_scope_key(result)

    if (
        event_type
        is ExecutionLedgerEventType.RECONCILIATION_STARTED
    ):
        event_id = _stable_lifecycle_event_id(
            "reconciliation-run-started",
            str(run_id),
        )
    else:
        event_id = _stable_lifecycle_event_id(
            "reconciliation-run-terminal",
            str(run_id),
        )

    payload: dict[str, object] = {
        "run_id": str(run_id),
        "reconciliation_scope": scope,
        "source_state": result.source_state.value,
    }

    if (
        event_type
        is not ExecutionLedgerEventType.RECONCILIATION_STARTED
    ):
        payload["result_state"] = result.state.value
        payload["discrepancy_ids"] = sorted(
            str(
                reconciliation_discrepancy_id(
                    discrepancy,
                    scope_instrument_id=instrument,
                )
            )
            for discrepancy in result.discrepancies
        )

    return ExecutionLedgerEventModel(
        event_id=event_id,
        event_type=event_type.value,
        event_version=1,
        user_id=result.user_id,
        plan_id=None,
        group_id=None,
        leg_id=None,
        order_id=None,
        fill_id=None,
        venue_id=str(result.account_id.venue_id),
        account_value=result.account_id.value,
        instrument_venue_id=str(instrument.venue_id),
        native_symbol=instrument.native_symbol,
        instrument_type=instrument.instrument_type.value,
        asset_class=instrument.asset_class.value,
        source="reconciliation",
        correlation_id=str(run_id),
        causation_id=None,
        occurred_at=result.observed_at,
        recorded_at=result.observed_at,
        sequence_no=sequence_no,
        evidence_source="reconciliation_orchestrator",
        evidence_quality=result.source_state.value,
        schema_version=1,
        payload=payload,
    )


def _lifecycle_discrepancy_model(
    result: ReconciliationResult,
    discrepancy: ReconciliationDiscrepancy,
    *,
    run_id: ReconciliationRunId,
    discrepancy_id: DiscrepancyId,
) -> ExecutionLedgerEventModel:
    instrument = result.instrument_id

    if instrument is None:
        raise ValueError(
            "lifecycle reconciliation requires instrument_id"
        )

    event_id = _stable_lifecycle_event_id(
        "reconciliation-discrepancy-v2",
        str(run_id),
        str(discrepancy_id),
    )

    payload = {
        "run_id": str(run_id),
        "discrepancy_id": str(discrepancy_id),
        "reconciliation_scope": _reconciliation_scope_key(
            result
        ),
        "kind": discrepancy.kind.value,
        "subject": discrepancy.subject.value,
        "local_reference": discrepancy.local_reference,
        "venue_reference": discrepancy.venue_reference,
        "local_value": discrepancy.local_value,
        "venue_value": discrepancy.venue_value,
    }

    return ExecutionLedgerEventModel(
        event_id=event_id,
        event_type=(
            ExecutionLedgerEventType
            .RECONCILIATION_DISCREPANCY
            .value
        ),
        event_version=2,
        user_id=result.user_id,
        plan_id=None,
        group_id=None,
        leg_id=None,
        order_id=None,
        fill_id=None,
        venue_id=str(result.account_id.venue_id),
        account_value=result.account_id.value,
        instrument_venue_id=str(instrument.venue_id),
        native_symbol=instrument.native_symbol,
        instrument_type=instrument.instrument_type.value,
        asset_class=instrument.asset_class.value,
        source="reconciliation",
        correlation_id=str(run_id),
        causation_id=None,
        occurred_at=discrepancy.observed_at,
        recorded_at=result.observed_at,
        sequence_no=10,
        evidence_source="reconciliation_detector",
        evidence_quality=result.source_state.value,
        schema_version=2,
        payload=payload,
    )


def _resolved_model(
    result: ReconciliationResult,
    *,
    run_id: ReconciliationRunId,
    discrepancy_id: str,
) -> ExecutionLedgerEventModel:
    instrument = result.instrument_id

    if instrument is None:
        raise ValueError(
            "lifecycle reconciliation requires instrument_id"
        )

    event_id = _stable_lifecycle_event_id(
        "reconciliation-resolved-v2",
        str(run_id),
        discrepancy_id,
    )

    return ExecutionLedgerEventModel(
        event_id=event_id,
        event_type=(
            ExecutionLedgerEventType
            .RECONCILIATION_RESOLVED
            .value
        ),
        event_version=1,
        user_id=result.user_id,
        plan_id=None,
        group_id=None,
        leg_id=None,
        order_id=None,
        fill_id=None,
        venue_id=str(result.account_id.venue_id),
        account_value=result.account_id.value,
        instrument_venue_id=str(instrument.venue_id),
        native_symbol=instrument.native_symbol,
        instrument_type=instrument.instrument_type.value,
        asset_class=instrument.asset_class.value,
        source="reconciliation",
        correlation_id=str(run_id),
        causation_id=discrepancy_id,
        occurred_at=result.observed_at,
        recorded_at=result.observed_at,
        sequence_no=20,
        evidence_source="reconciliation_orchestrator",
        evidence_quality=result.source_state.value,
        schema_version=1,
        payload={
            "run_id": str(run_id),
            "discrepancy_id": discrepancy_id,
            "reconciliation_scope": _reconciliation_scope_key(
                result
            ),
            "resolved_by_state": result.state.value,
        },
    )


def _active_discrepancy_ids(
    events: tuple[ExecutionLedgerEventModel, ...],
    *,
    scope: str,
) -> set[str]:
    active: set[str] = set()

    for event in events:
        payload = event.payload

        if payload.get("reconciliation_scope") != scope:
            continue

        discrepancy_id = payload.get(
            "discrepancy_id"
        )

        if not isinstance(discrepancy_id, str):
            continue

        if (
            event.event_type
            == ExecutionLedgerEventType
            .RECONCILIATION_DISCREPANCY
            .value
        ):
            active.add(discrepancy_id)

        elif (
            event.event_type
            == ExecutionLedgerEventType
            .RECONCILIATION_RESOLVED
            .value
        ):
            active.discard(discrepancy_id)

    return active


async def persist_reconciliation_result(
    service: ExecutionLedgerPersistenceService,
    result: ReconciliationResult,
) -> tuple[LedgerPersistResult, ...]:
    """Persist one result with durable lifecycle/resolution evidence."""

    if result.instrument_id is None:
        persisted: list[LedgerPersistResult] = []

        for discrepancy in result.discrepancies:
            persisted.append(
                await persist_reconciliation_discrepancy(
                    service,
                    discrepancy,
                )
            )

        return tuple(persisted)

    run_id = _run_id(result)
    scope = _reconciliation_scope_key(result)

    persisted = []

    persisted.append(
        await service.persist(
            event=_run_event_model(
                result,
                run_id=run_id,
                event_type=(
                    ExecutionLedgerEventType
                    .RECONCILIATION_STARTED
                ),
                sequence_no=0,
            ),
            mutate_projection=_no_projection_mutation,
        )
    )

    history = await service.list_for_account(
        user_id=result.user_id,
        venue_id=str(result.account_id.venue_id),
        account_value=result.account_id.value,
    )

    previously_active = _active_discrepancy_ids(
        history,
        scope=scope,
    )

    current: dict[
        str,
        tuple[
            DiscrepancyId,
            ReconciliationDiscrepancy,
        ],
    ] = {}

    for discrepancy in result.discrepancies:
        discrepancy_id = reconciliation_discrepancy_id(
            discrepancy,
            scope_instrument_id=result.instrument_id,
        )

        current[str(discrepancy_id)] = (
            discrepancy_id,
            discrepancy,
        )

    for discrepancy_id, discrepancy in current.values():
        persisted.append(
            await service.persist(
                event=_lifecycle_discrepancy_model(
                    result,
                    discrepancy,
                    run_id=run_id,
                    discrepancy_id=discrepancy_id,
                ),
                mutate_projection=_no_projection_mutation,
            )
        )

    for resolved_discrepancy_id in sorted(
        previously_active - set(current)
    ):
        persisted.append(
            await service.persist(
                event=_resolved_model(
                    result,
                    run_id=run_id,
                    discrepancy_id=resolved_discrepancy_id,
                ),
                mutate_projection=_no_projection_mutation,
            )
        )

    if result.state in _DEGRADED_RESULT_STATES:
        terminal_type = (
            ExecutionLedgerEventType
            .RECONCILIATION_DEGRADED
        )
    else:
        terminal_type = (
            ExecutionLedgerEventType
            .RECONCILIATION_COMPLETED
        )

    persisted.append(
        await service.persist(
            event=_run_event_model(
                result,
                run_id=run_id,
                event_type=terminal_type,
                sequence_no=30,
            ),
            mutate_projection=_no_projection_mutation,
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
