"""Persistence-only repository for coordinator checkpoints."""

from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.ports.execution_coordinator import (
    ExecutionCoordinatorStateRecord,
)
from infra.persistence.models.execution_coordinator import (
    ExecutionCoordinatorStateModel,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    OrderId,
    VenueId,
)


class ExecutionCoordinatorStateRepository:
    """Flush-only repository for durable coordinator state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        *,
        user_id: int,
        order_id: OrderId,
    ) -> ExecutionCoordinatorStateRecord | None:
        statement = select(
            ExecutionCoordinatorStateModel
        ).where(
            ExecutionCoordinatorStateModel.user_id == user_id,
            ExecutionCoordinatorStateModel.order_id == str(order_id),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_record(model)

    async def add_or_update(
        self,
        record: ExecutionCoordinatorStateRecord,
    ) -> ExecutionCoordinatorStateRecord:
        statement = select(
            ExecutionCoordinatorStateModel
        ).where(
            ExecutionCoordinatorStateModel.user_id == record.user_id,
            ExecutionCoordinatorStateModel.order_id
            == str(record.order_id),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            model = ExecutionCoordinatorStateModel(
                user_id=record.user_id,
                order_id=str(record.order_id),
            )
            self._session.add(model)

        model.client_order_id = str(record.client_order_id)
        model.venue_id = str(record.account_id.venue_id)
        model.account_value = record.account_id.value
        model.instrument_venue_id = str(record.instrument_id.venue_id)
        model.native_symbol = record.instrument_id.native_symbol
        model.instrument_type = record.instrument_id.instrument_type.value
        model.asset_class = record.instrument_id.asset_class.value
        model.state = record.state.value
        model.attempt = record.attempt
        model.venue_order_id = record.venue_order_id
        model.created_at = record.created_at
        model.updated_at = record.updated_at

        await self._session.flush()
        return record

    @staticmethod
    def _restore_utc(
        value,
    ):
        """Restore UTC for databases that drop timezone metadata."""

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value

    @staticmethod
    def _to_record(
        model: ExecutionCoordinatorStateModel,
    ) -> ExecutionCoordinatorStateRecord:
        venue_id = VenueId(model.venue_id)
        account_id = AccountId(
            venue_id=venue_id,
            value=model.account_value,
        )
        instrument_id = InstrumentId(
            venue_id=VenueId(model.instrument_venue_id),
            native_symbol=model.native_symbol,
            instrument_type=InstrumentType(
                model.instrument_type
            ),
            asset_class=AssetClass(model.asset_class),
        )

        return ExecutionCoordinatorStateRecord(
            user_id=model.user_id,
            order_id=OrderId(model.order_id),
            client_order_id=ClientOrderId(
                model.client_order_id
            ),
            account_id=account_id,
            instrument_id=instrument_id,
            state=ExecutionCoordinatorState(model.state),
            attempt=model.attempt,
            venue_order_id=model.venue_order_id,
            updated_at=ExecutionCoordinatorStateRepository._restore_utc(
                model.updated_at,
            ),
            created_at=ExecutionCoordinatorStateRepository._restore_utc(
                model.created_at,
            ),
        )
