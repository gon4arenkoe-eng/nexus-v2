"""Phase 14 durable simulated-venue observation persistence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.ports.venue import (
    VenueOrderResult,
    VenueOrderState,
)
from infra.persistence.models.execution_orders import (
    ExecutionOrderModel,
)
from packages.contracts.identities import (
    AccountId,
    ClientOrderId,
    InstrumentId,
    VenueOrderId,
)
from packages.contracts.primitives import normalize_utc_datetime


PHASE14_SIMULATED_SOURCE = "PHASE14_SIMULATED"


class Phase14SimulatedVenueObservationRepository:
    """Persist only the ACCEPTED/zero-fill Phase14 simulated order shape."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_accepted(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
        result: VenueOrderResult,
        observed_at: datetime,
    ) -> None:
        self._validate_scope(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
        )
        observed_at = normalize_utc_datetime(
            observed_at,
            field_name="observed_at",
        )

        if result.state is not VenueOrderState.ACCEPTED:
            raise ValueError(
                "Phase14 simulated persistence accepts only ACCEPTED"
            )
        if result.venue_order_id is None:
            raise ValueError(
                "ACCEPTED simulated result requires venue_order_id"
            )
        if result.filled_quantity != Decimal("0"):
            raise ValueError(
                "Phase14 simulated ACCEPTED result must be zero-fill"
            )
        if result.average_fill_price is not None:
            raise ValueError(
                "zero-fill simulated result must not have average_fill_price"
            )
        if result.rejection_reason is not None:
            raise ValueError(
                "ACCEPTED simulated result must not have rejection_reason"
            )

        query = select(ExecutionOrderModel).where(
            ExecutionOrderModel.user_id == user_id,
            ExecutionOrderModel.venue_id
            == str(account_id.venue_id),
            ExecutionOrderModel.account_value
            == account_id.value,
            ExecutionOrderModel.instrument_venue_id
            == str(instrument_id.venue_id),
            ExecutionOrderModel.native_symbol
            == instrument_id.native_symbol,
            ExecutionOrderModel.instrument_type
            == instrument_id.instrument_type.value,
            ExecutionOrderModel.asset_class
            == instrument_id.asset_class.value,
            ExecutionOrderModel.client_order_id
            == str(result.client_order_id),
        )
        found = await self._session.execute(query)
        model = found.scalar_one_or_none()

        if model is None:
            raise LookupError(
                "canonical execution order not found for simulated observation"
            )

        if model.requested_quantity != result.requested_quantity:
            raise ValueError(
                "simulated venue quantity conflicts with canonical order"
            )

        venue_order_id = str(result.venue_order_id)

        if (
            model.venue_order_id is not None
            and model.venue_order_id != venue_order_id
        ):
            raise ValueError(
                "simulated venue_order_id conflicts with canonical order"
            )

        model.venue_order_id = venue_order_id
        model.last_venue_status = result.state.value
        model.last_venue_observed_at = observed_at
        model.venue_observation_source = PHASE14_SIMULATED_SOURCE

        await self._session.flush()

    async def load_by_venue_order_id(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult | None:
        self._validate_scope(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        query = select(ExecutionOrderModel).where(
            ExecutionOrderModel.user_id == user_id,
            ExecutionOrderModel.venue_id
            == str(account_id.venue_id),
            ExecutionOrderModel.account_value
            == account_id.value,
            ExecutionOrderModel.instrument_venue_id
            == str(instrument_id.venue_id),
            ExecutionOrderModel.native_symbol
            == instrument_id.native_symbol,
            ExecutionOrderModel.instrument_type
            == instrument_id.instrument_type.value,
            ExecutionOrderModel.asset_class
            == instrument_id.asset_class.value,
            ExecutionOrderModel.venue_order_id
            == str(venue_order_id),
            ExecutionOrderModel.venue_observation_source
            == PHASE14_SIMULATED_SOURCE,
            ExecutionOrderModel.last_venue_status
            == VenueOrderState.ACCEPTED.value,
        )
        found = await self._session.execute(query)
        model = found.scalar_one_or_none()

        if model is None:
            return None

        return self._to_result(model)

    async def load_open_orders(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> tuple[VenueOrderResult, ...]:
        self._validate_scope(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        query = (
            select(ExecutionOrderModel)
            .where(
                ExecutionOrderModel.user_id == user_id,
                ExecutionOrderModel.venue_id
                == str(account_id.venue_id),
                ExecutionOrderModel.account_value
                == account_id.value,
                ExecutionOrderModel.instrument_venue_id
                == str(instrument_id.venue_id),
                ExecutionOrderModel.native_symbol
                == instrument_id.native_symbol,
                ExecutionOrderModel.instrument_type
                == instrument_id.instrument_type.value,
                ExecutionOrderModel.asset_class
                == instrument_id.asset_class.value,
                ExecutionOrderModel.venue_observation_source
                == PHASE14_SIMULATED_SOURCE,
                ExecutionOrderModel.last_venue_status
                == VenueOrderState.ACCEPTED.value,
            )
            .order_by(
                ExecutionOrderModel.created_at.asc(),
                ExecutionOrderModel.order_id.asc(),
            )
        )

        found = await self._session.execute(query)

        return tuple(
            self._to_result(model)
            for model in found.scalars().all()
        )

    @staticmethod
    def _to_result(
        model: ExecutionOrderModel,
    ) -> VenueOrderResult:
        if model.venue_order_id is None:
            raise ValueError(
                "persisted simulated observation has no venue_order_id"
            )

        return VenueOrderResult(
            client_order_id=ClientOrderId(model.client_order_id),
            venue_order_id=VenueOrderId(model.venue_order_id),
            state=VenueOrderState.ACCEPTED,
            requested_quantity=model.requested_quantity,
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            rejection_reason=None,
        )

    @staticmethod
    def _validate_scope(
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> None:
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError("user_id must be positive")

        if not isinstance(account_id, AccountId):
            raise ValueError("account_id must be an AccountId")

        if not isinstance(instrument_id, InstrumentId):
            raise ValueError("instrument_id must be an InstrumentId")

        if account_id.venue_id != instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )
