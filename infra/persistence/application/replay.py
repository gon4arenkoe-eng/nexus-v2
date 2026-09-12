"""Deterministic replay over persisted execution Ledger evidence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from math import isfinite
from typing import Protocol

from infra.persistence.models import ExecutionLedgerEventModel


class LedgerReplayConflictError(RuntimeError):
    """One event identity has conflicting immutable replay content."""


@dataclass(frozen=True, slots=True)
class ExecutionLedgerReplayProjection:
    """Deterministic projection reconstructed from Ledger evidence."""

    event_count: int
    ordered_event_ids: tuple[str, ...]
    plan_heads: tuple[tuple[str, str, str], ...]
    group_heads: tuple[tuple[str, str, str], ...]
    leg_heads: tuple[tuple[str, str, str, str], ...]
    order_heads: tuple[tuple[str, str, str], ...]
    fill_heads: tuple[tuple[str, str, str], ...]
    digest: str


class LedgerReplayRepositoryPort(Protocol):
    """Read surface required for persisted plan replay."""

    async def list_for_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read all persisted events for one user-owned plan."""

        ...


class ExecutionLedgerReplayService:
    """Read persisted Ledger evidence and rebuild deterministic state."""

    def __init__(
        self,
        repository: LedgerReplayRepositoryPort,
    ) -> None:
        self._repository = repository

    async def replay_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> ExecutionLedgerReplayProjection:
        events = await self._repository.list_for_plan(
            user_id=user_id,
            plan_id=plan_id,
        )

        return project_ledger_events(events)


def project_ledger_events(
    events: Iterable[ExecutionLedgerEventModel],
) -> ExecutionLedgerReplayProjection:
    """Rebuild deterministic persisted evidence projection."""

    events_by_id: dict[str, ExecutionLedgerEventModel] = {}
    documents_by_id: dict[str, dict[str, object]] = {}

    for event in events:
        document = _event_document(event)
        existing_document = documents_by_id.get(event.event_id)

        if existing_document is not None:
            if existing_document != document:
                raise LedgerReplayConflictError(
                    "event_id has conflicting immutable replay content"
                )
            continue

        events_by_id[event.event_id] = event
        documents_by_id[event.event_id] = document

    ordered = tuple(
        sorted(
            events_by_id.values(),
            key=_event_sort_key,
        )
    )

    plan_heads: dict[str, tuple[str, str]] = {}
    group_heads: dict[str, tuple[str, str]] = {}
    leg_heads: dict[tuple[str, str], tuple[str, str]] = {}
    order_heads: dict[str, tuple[str, str]] = {}
    fill_heads: dict[str, tuple[str, str]] = {}

    for event in ordered:
        head = (event.event_type, event.event_id)

        if event.plan_id is not None:
            plan_heads[event.plan_id] = head

        if event.group_id is not None:
            group_heads[event.group_id] = head

        if event.leg_id is not None:
            if event.group_id is None:
                raise ValueError(
                    "Ledger event with leg_id must also have group_id"
                )

            leg_heads[(event.group_id, event.leg_id)] = head

        if event.order_id is not None:
            order_heads[event.order_id] = head

        if event.fill_id is not None:
            fill_heads[event.fill_id] = head

    ordered_documents = [
        documents_by_id[event.event_id]
        for event in ordered
    ]

    encoded = json.dumps(
        ordered_documents,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    digest = sha256(encoded).hexdigest()

    return ExecutionLedgerReplayProjection(
        event_count=len(ordered),
        ordered_event_ids=tuple(
            event.event_id
            for event in ordered
        ),
        plan_heads=tuple(
            (entity_id, event_type, event_id)
            for entity_id, (event_type, event_id)
            in sorted(plan_heads.items())
        ),
        group_heads=tuple(
            (entity_id, event_type, event_id)
            for entity_id, (event_type, event_id)
            in sorted(group_heads.items())
        ),
        leg_heads=tuple(
            (
                group_id,
                leg_id,
                event_type,
                event_id,
            )
            for (group_id, leg_id), (event_type, event_id)
            in sorted(leg_heads.items())
        ),
        order_heads=tuple(
            (entity_id, event_type, event_id)
            for entity_id, (event_type, event_id)
            in sorted(order_heads.items())
        ),
        fill_heads=tuple(
            (entity_id, event_type, event_id)
            for entity_id, (event_type, event_id)
            in sorted(fill_heads.items())
        ),
        digest=digest,
    )


def _event_sort_key(
    event: ExecutionLedgerEventModel,
) -> tuple[str, str, str]:
    return (
        _canonical_datetime(event.occurred_at),
        _canonical_datetime(event.recorded_at),
        event.event_id,
    )


def _event_document(
    event: ExecutionLedgerEventModel,
) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "event_version": event.event_version,
        "user_id": event.user_id,
        "plan_id": event.plan_id,
        "group_id": event.group_id,
        "leg_id": event.leg_id,
        "order_id": event.order_id,
        "fill_id": event.fill_id,
        "venue_id": event.venue_id,
        "account_value": event.account_value,
        "instrument_venue_id": event.instrument_venue_id,
        "native_symbol": event.native_symbol,
        "instrument_type": event.instrument_type,
        "asset_class": event.asset_class,
        "source": event.source,
        "correlation_id": event.correlation_id,
        "causation_id": event.causation_id,
        "occurred_at": _canonical_datetime(event.occurred_at),
        "recorded_at": _canonical_datetime(event.recorded_at),
        "sequence_no": event.sequence_no,
        "evidence_source": event.evidence_source,
        "evidence_quality": event.evidence_quality,
        "schema_version": event.schema_version,
        "payload": _canonical_json_value(event.payload),
    }


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "Ledger replay requires timezone-aware timestamps"
        )

    return (
        value.astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json_value(value: object) -> object:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (str, int)):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(
                "Ledger JSON evidence cannot contain NaN/Infinity"
            )
        return value

    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    "Ledger JSON evidence keys must be strings"
                )

            normalized[key] = _canonical_json_value(item)

        return {
            key: normalized[key]
            for key in sorted(normalized)
        }

    if isinstance(value, (list, tuple)):
        return [
            _canonical_json_value(item)
            for item in value
        ]

    raise TypeError(
        "Unsupported Ledger JSON evidence type: "
        f"{type(value).__name__}"
    )
