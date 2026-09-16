"""Application adapter for read-only local reconciliation snapshots."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshot,
    LocalReconciliationSnapshotProvider,
)
from infra.persistence.repositories.reconciliation_snapshot import (
    LocalReconciliationSnapshotRepository,
)
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)


class SqlAlchemyLocalReconciliationSnapshotProvider(
    LocalReconciliationSnapshotProvider,
):
    """Open a read transaction and return canonical local reconciliation state."""

    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = factory

    async def load(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> LocalReconciliationSnapshot:
        async with self._factory() as session:
            repository = LocalReconciliationSnapshotRepository(
                session
            )
            return await repository.load(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
            )
