"""Canonical NEXUS V2 shared event contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from packages.contracts.primitives import normalize_utc_datetime


PayloadT = TypeVar("PayloadT")


def _required_text(
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

    return _required_text(value, field_name=field_name)


@dataclass(frozen=True, slots=True)
class EventEnvelope(Generic[PayloadT]):
    event_id: str
    event_type: str
    event_version: int
    source: str
    occurred_at: object
    recorded_at: object
    payload: PayloadT
    correlation_id: str | None = None
    causation_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _required_text(self.event_id, field_name="event_id"),
        )
        object.__setattr__(
            self,
            "event_type",
            _required_text(self.event_type, field_name="event_type"),
        )
        object.__setattr__(
            self,
            "source",
            _required_text(self.source, field_name="source"),
        )

        if (
            isinstance(self.event_version, bool)
            or not isinstance(self.event_version, int)
            or self.event_version <= 0
        ):
            raise ValueError("event_version must be a positive integer")

        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(
                self.occurred_at,
                field_name="occurred_at",
            ),
        )
        object.__setattr__(
            self,
            "recorded_at",
            normalize_utc_datetime(
                self.recorded_at,
                field_name="recorded_at",
            ),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _optional_text(
                self.correlation_id,
                field_name="correlation_id",
            ),
        )
        object.__setattr__(
            self,
            "causation_id",
            _optional_text(
                self.causation_id,
                field_name="causation_id",
            ),
        )
