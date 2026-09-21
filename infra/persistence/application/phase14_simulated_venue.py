"""Transactional Phase 14 simulated-venue persistence adapter."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from apps.core.ports.venue import VenueOrderResult
from infra.persistence.repositories.phase14_simulated_venue import (
    Phase14SimulatedVenueObservationRepository,
)
from packages.contracts.identities import (
    AccountId,
    InstrumentId,
    VenueOrderId,
)


class SqlAlchemyPhase14SimulatedVenueObservationStore:
    """Durable observation store; grants no real venue authority."""

    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = factory

    async def record_accepted(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
        result: VenueOrderResult,
        observed_at: datetime,
    ) -> None:
        async with self._factory() as session:
            repository = (
                Phase14SimulatedVenueObservationRepository(session)
            )
            try:
                await repository.record_accepted(
                    user_id=user_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    result=result,
                    observed_at=observed_at,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def load_by_venue_order_id(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult | None:
        async with self._factory() as session:
            repository = (
                Phase14SimulatedVenueObservationRepository(session)
            )
            return await repository.load_by_venue_order_id(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
                venue_order_id=venue_order_id,
            )

    async def load_open_orders(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> tuple[VenueOrderResult, ...]:
        async with self._factory() as session:
            repository = (
                Phase14SimulatedVenueObservationRepository(session)
            )
            return await repository.load_open_orders(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
            )
