"""Application transaction adapter for coordinator checkpoints."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from apps.core.ports.execution_coordinator import (
    ExecutionCoordinatorStateRecord,
    ExecutionCoordinatorStateStore,
)
from infra.persistence.repositories.execution_coordinator import (
    ExecutionCoordinatorStateRepository,
)


class SqlAlchemyExecutionCoordinatorStateStore(
    ExecutionCoordinatorStateStore,
):
    """Persist coordinator checkpoints in independent transactions."""

    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = factory

    async def load(
        self,
        *,
        user_id: int,
        order_id,
    ) -> ExecutionCoordinatorStateRecord | None:
        async with self._factory() as session:
            repository = ExecutionCoordinatorStateRepository(session)
            return await repository.get(
                user_id=user_id,
                order_id=order_id,
            )

    async def checkpoint(
        self,
        record: ExecutionCoordinatorStateRecord,
    ) -> None:
        async with self._factory() as session:
            repository = ExecutionCoordinatorStateRepository(session)

            try:
                await repository.add_or_update(record)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
