"""Canonical NEXUS V2 immutable execution ledger contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from packages.contracts.identities import AccountId, VenueId

from packages.contracts.primitives import normalize_utc_datetime


class ExecutionLedgerEventType(StrEnum):
    PLAN_CREATED = "PLAN_CREATED"
    GROUP_CREATED = "GROUP_CREATED"
    GROUP_STATE_CHANGED = "GROUP_STATE_CHANGED"
    LEG_CREATED = "LEG_CREATED"
    LEG_STATE_CHANGED = "LEG_STATE_CHANGED"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_PARTIALLY_FILLED = "ORDER_PARTIALLY_FILLED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    FILL_RECORDED = "FILL_RECORDED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    RECONCILIATION_DISCREPANCY = "RECONCILIATION_DISCREPANCY"
    RECONCILIATION_RESOLVED = "RECONCILIATION_RESOLVED"


def _require_non_empty_text(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


def _optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _require_non_empty_text(
        value,
        field_name=field_name,
    )


def _optional_positive_int(
    value: int | None,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(f"{field_name} must be a positive integer")

    return value


def _json_safe_copy(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")

    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "payload must contain JSON-serializable data"
        ) from exc

    if not isinstance(decoded, dict):
        raise ValueError("payload must serialize to a JSON object")

    return MappingProxyType(decoded)


@dataclass(frozen=True, slots=True)
class ExecutionLedgerEvent:
    event_id: str
    event_type: ExecutionLedgerEventType
    event_version: int
    user_id: int
    execution_plan_id: str
    position_group_id: str | None
    position_leg_id: str | None
    execution_order_id: str | None
    execution_fill_id: str | None
    account_id: AccountId | None
    venue_id: VenueId | None
    occurred_at: datetime
    recorded_at: datetime
    source: str
    correlation_id: str | None
    causation_id: str | None
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_non_empty_text(
                self.event_id,
                field_name="event_id",
            ),
        )

        if not isinstance(
            self.event_type,
            ExecutionLedgerEventType,
        ):
            raise ValueError(
                "event_type must be an ExecutionLedgerEventType"
            )

        if (
            not isinstance(self.event_version, int)
            or isinstance(self.event_version, bool)
            or self.event_version <= 0
        ):
            raise ValueError(
                "event_version must be a positive integer"
            )

        if (
            not isinstance(self.user_id, int)
            or isinstance(self.user_id, bool)
            or self.user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")
        if self.account_id is not None:
            if not isinstance(self.account_id, AccountId):
                raise ValueError(
                    "account_id must be an AccountId"
                )

        if self.venue_id is not None:
            if not isinstance(self.venue_id, VenueId):
                raise ValueError(
                    "venue_id must be a VenueId"
                )

        if (
            self.account_id is not None
            and self.venue_id is not None
            and self.account_id.venue_id != self.venue_id
        ):
            raise ValueError(
                "venue_id must match account_id venue"
            )

        object.__setattr__(
            self,
            "execution_plan_id",
            _require_non_empty_text(
                self.execution_plan_id,
                field_name="execution_plan_id",
            ),
        )

        for field_name in (
            "position_group_id",
            "position_leg_id",
            "execution_order_id",
            "execution_fill_id",
            "correlation_id",
            "causation_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        occurred_at = normalize_utc_datetime(
            self.occurred_at,
            field_name="occurred_at",
        )
        recorded_at = normalize_utc_datetime(
            self.recorded_at,
            field_name="recorded_at",
        )

        if recorded_at < occurred_at:
            raise ValueError(
                "recorded_at must not precede occurred_at"
            )

        object.__setattr__(
            self,
            "source",
            _require_non_empty_text(
                self.source,
                field_name="source",
            ),
        )

        object.__setattr__(
            self,
            "payload",
            _json_safe_copy(self.payload),
        )
        object.__setattr__(
            self,
            "occurred_at",
            occurred_at,
        )
        object.__setattr__(
            self,
            "recorded_at",
            recorded_at,
        )


def ledger_events_equivalent(
    left: ExecutionLedgerEvent,
    right: ExecutionLedgerEvent,
) -> bool:
    if left.event_id != right.event_id:
        return False

    return left == right


def sort_ledger_events_for_replay(
    events: Sequence[ExecutionLedgerEvent],
) -> tuple[ExecutionLedgerEvent, ...]:
    if not isinstance(events, Sequence):
        raise ValueError("events must be a sequence")

    seen: dict[str, ExecutionLedgerEvent] = {}

    for event in events:
        if not isinstance(event, ExecutionLedgerEvent):
            raise ValueError(
                "events must contain ExecutionLedgerEvent values"
            )

        existing = seen.get(event.event_id)

        if existing is not None:
            if not ledger_events_equivalent(existing, event):
                raise ValueError(
                    "conflicting immutable ledger event identity"
                )

            continue

        seen[event.event_id] = event

    return tuple(
        sorted(
            seen.values(),
            key=lambda event: (
                event.occurred_at,
                event.recorded_at,
                event.event_id,
            ),
        )
    )
