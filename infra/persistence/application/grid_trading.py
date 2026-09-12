"""SQLAlchemy Grid Trading Desk state-store adapter."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.grid_trading import GridInstance
from infra.persistence.repositories.grid_trading import GridInstanceStateRepository  # noqa: E501


class SqlAlchemyGridInstanceStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load(self, *, user_id: int, instance_id: str) -> GridInstance | None:  # noqa: E501
        return await GridInstanceStateRepository(self._session).get(
            user_id=user_id,
            instance_id=instance_id,
        )

    async def checkpoint(self, instance: GridInstance) -> None:
        await GridInstanceStateRepository(self._session).upsert(instance)

    async def list_for_user(self, *, user_id: int) -> tuple[GridInstance, ...]:
        return await GridInstanceStateRepository(self._session).list_for_user(user_id=user_id)  # noqa: E501
