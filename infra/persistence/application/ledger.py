"""Atomic persistence boundary for execution Ledger evidence."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.models import ExecutionLedgerEventModel
from infra.persistence.repositories import ExecutionLedgerRepository


class LedgerEventConflictError(RuntimeError):
    """Same event identity was reused with different immutable content."""


class LedgerPersistDisposition(str, Enum):
    """Outcome of one deterministic Ledger persistence request."""

    APPENDED = "APPENDED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class LedgerPersistResult:
    """Result of a Ledger persistence request."""

    disposition: LedgerPersistDisposition
    event: ExecutionLedgerEventModel


class LedgerRepositoryPort(Protocol):
    """Minimal repository surface required by the application boundary."""

    async def add(
        self,
        event: ExecutionLedgerEventModel,
    ) -> ExecutionLedgerEventModel:
        """Append and flush one immutable event."""

        ...

    async def get_by_event_id(
        self,
        *,
        user_id: int,
        event_id: str,
    ) -> ExecutionLedgerEventModel | None:
        """Read an existing event inside user ownership."""

        ...

    async def list_for_account(
        self,
        *,
        user_id: int,
        venue_id: str,
        account_value: int,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read immutable Ledger evidence for one user-owned account."""

        ...


ProjectionMutation = Callable[[AsyncSession], Awaitable[None]]


class ExecutionLedgerPersistenceService:
    """Coordinate projection mutation and immutable Ledger persistence."""

    def __init__(
        self,
        session: AsyncSession,
        repository: LedgerRepositoryPort | None = None,
    ) -> None:
        self._session = session
        self._repository: LedgerRepositoryPort = (
            repository
            if repository is not None
            else ExecutionLedgerRepository(session)
        )

    async def persist(
        self,
        *,
        event: ExecutionLedgerEventModel,
        mutate_projection: ProjectionMutation,
    ) -> LedgerPersistResult:
        """Persist one mutation without owning the caller transaction."""

        existing = await self._repository.get_by_event_id(
            user_id=event.user_id,
            event_id=event.event_id,
        )

        if existing is not None:
            if not _events_equivalent(existing, event):
                raise LedgerEventConflictError(
                    "event_id already exists with conflicting "
                    "immutable Ledger content"
                )

            return LedgerPersistResult(
                disposition=LedgerPersistDisposition.DUPLICATE,
                event=existing,
            )

        await mutate_projection(self._session)

        appended = await self._repository.add(event)

        return LedgerPersistResult(
            disposition=LedgerPersistDisposition.APPENDED,
            event=appended,
        )

    async def list_for_account(
        self,
        *,
        user_id: int,
        venue_id: str,
        account_value: int,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read account evidence through the configured repository."""

        return await self._repository.list_for_account(
            user_id=user_id,
            venue_id=venue_id,
            account_value=account_value,
        )


def _events_equivalent(
    left: ExecutionLedgerEventModel,
    right: ExecutionLedgerEventModel,
) -> bool:
    return _event_signature(left) == _event_signature(right)


def _event_signature(
    event: ExecutionLedgerEventModel,
) -> tuple[object, ...]:
    """Return all immutable business content except persistence PK."""

    return (
        event.event_id,
        event.event_type,
        event.event_version,
        event.user_id,
        event.plan_id,
        event.group_id,
        event.leg_id,
        event.order_id,
        event.fill_id,
        event.venue_id,
        event.account_value,
        event.instrument_venue_id,
        event.native_symbol,
        event.instrument_type,
        event.asset_class,
        event.source,
        event.correlation_id,
        event.causation_id,
        event.occurred_at,
        event.recorded_at,
        event.sequence_no,
        event.evidence_source,
        event.evidence_quality,
        event.schema_version,
        dict(event.payload),
    )
