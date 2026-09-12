"""Persistence-only repository for immutable execution Ledger events."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from infra.persistence.models import ExecutionLedgerEventModel


class ExecutionLedgerRepository:
    """Append and read immutable execution Ledger events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        event: ExecutionLedgerEventModel,
    ) -> ExecutionLedgerEventModel:
        """Append one Ledger event and flush without committing."""

        self._session.add(event)
        await self._session.flush()
        return event

    async def get_by_event_id(
        self,
        *,
        user_id: int,
        event_id: str,
    ) -> ExecutionLedgerEventModel | None:
        """Read one event inside explicit user ownership."""

        statement = select(ExecutionLedgerEventModel).where(
            ExecutionLedgerEventModel.user_id == user_id,
            ExecutionLedgerEventModel.event_id == event_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_plan(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read plan events in deterministic persistence order."""

        return await self._list(
            user_id=user_id,
            criterion=ExecutionLedgerEventModel.plan_id == plan_id,
        )

    async def list_for_group(
        self,
        *,
        user_id: int,
        group_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read position-group events in deterministic order."""

        return await self._list(
            user_id=user_id,
            criterion=ExecutionLedgerEventModel.group_id == group_id,
        )

    async def list_for_leg(
        self,
        *,
        user_id: int,
        group_id: str,
        leg_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read composite PositionLeg events in deterministic order."""

        statement = (
            select(ExecutionLedgerEventModel)
            .where(
                ExecutionLedgerEventModel.user_id == user_id,
                ExecutionLedgerEventModel.group_id == group_id,
                ExecutionLedgerEventModel.leg_id == leg_id,
            )
            .order_by(
                ExecutionLedgerEventModel.occurred_at.asc(),
                ExecutionLedgerEventModel.id.asc(),
            )
        )

        result = await self._session.execute(statement)
        return tuple(result.scalars().all())

    async def list_for_order(
        self,
        *,
        user_id: int,
        order_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read order events in deterministic persistence order."""

        return await self._list(
            user_id=user_id,
            criterion=ExecutionLedgerEventModel.order_id == order_id,
        )

    async def list_for_fill(
        self,
        *,
        user_id: int,
        fill_id: str,
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        """Read fill events in deterministic persistence order."""

        return await self._list(
            user_id=user_id,
            criterion=ExecutionLedgerEventModel.fill_id == fill_id,
        )

    async def _list(
        self,
        *,
        user_id: int,
        criterion: ColumnElement[bool],
    ) -> tuple[ExecutionLedgerEventModel, ...]:
        statement = (
            select(ExecutionLedgerEventModel)
            .where(
                ExecutionLedgerEventModel.user_id == user_id,
                criterion,
            )
            .order_by(
                ExecutionLedgerEventModel.occurred_at.asc(),
                ExecutionLedgerEventModel.id.asc(),
            )
        )

        result = await self._session.execute(statement)
        return tuple(result.scalars().all())
