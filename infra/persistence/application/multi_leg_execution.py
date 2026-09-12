"""SQLAlchemy state-store adapter for pair/basket execution."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.ports.multi_leg_execution import (
    MultiLegExecutionStateRecord,
)
from infra.persistence.repositories.multi_leg_execution import (
    MultiLegExecutionStateRepository,
)


class SqlAlchemyMultiLegExecutionStateStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load(
        self,
        *,
        user_id: int,
        plan_id: str,
    ) -> MultiLegExecutionStateRecord | None:
        return await MultiLegExecutionStateRepository(self._session).get(
            user_id=user_id,
            plan_id=plan_id,
        )

    async def checkpoint(
        self,
        record: MultiLegExecutionStateRecord,
    ) -> None:
        await MultiLegExecutionStateRepository(self._session).upsert(record)
