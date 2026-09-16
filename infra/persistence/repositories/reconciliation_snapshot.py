"""Persistence read model for canonical local reconciliation snapshots."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.execution_orders import (
    ExecutionFill,
    ExecutionOrder,
    ExecutionOrderStatus,
    OrderSide,
    OrderType,
)
from apps.core.domain.positions import (
    PositionLeg,
    PositionLegStatus,
    TradeSide,
)
from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshot,
)
from infra.persistence.models.execution_orders import (
    ExecutionFillModel,
    ExecutionOrderModel,
)
from infra.persistence.models.positions import (
    PositionGroupModel,
    PositionLegModel,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    FillId,
    InstrumentId,
    InstrumentType,
    OrderId,
    VenueFillId,
    VenueId,
    VenueOrderId,
)


def _restore_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value


def _restore_optional_utc(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    return _restore_utc(value)


class LocalReconciliationSnapshotRepository:
    """Read materialized local order/fill/position state deterministically."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load(
        self,
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> LocalReconciliationSnapshot:
        self._validate_scope(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        order_result = await self._session.execute(
            self._order_statement(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
            )
        )

        fill_result = await self._session.execute(
            self._fill_statement(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
            )
        )

        position_result = await self._session.execute(
            self._position_statement(
                user_id=user_id,
                account_id=account_id,
                instrument_id=instrument_id,
            )
        )

        orders = tuple(
            self._to_order(model)
            for model in order_result.scalars().all()
        )
        fills = tuple(
            self._to_fill(model)
            for model in fill_result.scalars().all()
        )
        positions = tuple(
            self._to_position(model)
            for model in position_result.scalars().all()
        )

        return LocalReconciliationSnapshot(
            user_id=user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            orders=orders,
            fills=fills,
            positions=positions,
        )

    @staticmethod
    def _validate_scope(
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> None:
        if isinstance(user_id, bool) or not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        if user_id <= 0:
            raise ValueError("user_id must be positive")

        if not isinstance(account_id, AccountId):
            raise ValueError("account_id must be an AccountId")

        if not isinstance(instrument_id, InstrumentId):
            raise ValueError(
                "instrument_id must be an InstrumentId"
            )

        if account_id.venue_id != instrument_id.venue_id:
            raise ValueError(
                "account venue must match instrument venue"
            )

    @staticmethod
    def _order_statement(
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> Select[tuple[ExecutionOrderModel]]:
        return (
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
            )
            .order_by(
                ExecutionOrderModel.created_at.asc(),
                ExecutionOrderModel.order_id.asc(),
                ExecutionOrderModel.id.asc(),
            )
        )

    @staticmethod
    def _fill_statement(
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> Select[tuple[ExecutionFillModel]]:
        return (
            select(ExecutionFillModel)
            .join(
                ExecutionOrderModel,
                ExecutionOrderModel.order_id
                == ExecutionFillModel.order_id,
            )
            .where(
                ExecutionFillModel.user_id == user_id,
                ExecutionFillModel.venue_id
                == str(account_id.venue_id),
                ExecutionFillModel.account_value
                == account_id.value,
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
            )
            .order_by(
                ExecutionFillModel.executed_at.asc(),
                ExecutionFillModel.created_at.asc(),
                ExecutionFillModel.fill_id.asc(),
                ExecutionFillModel.id.asc(),
            )
        )

    @staticmethod
    def _position_statement(
        *,
        user_id: int,
        account_id: AccountId,
        instrument_id: InstrumentId,
    ) -> Select[tuple[PositionLegModel]]:
        return (
            select(PositionLegModel)
            .join(
                PositionGroupModel,
                PositionGroupModel.group_id
                == PositionLegModel.group_id,
            )
            .where(
                PositionGroupModel.user_id == user_id,
                PositionLegModel.venue_id
                == str(account_id.venue_id),
                PositionLegModel.account_value
                == account_id.value,
                PositionLegModel.instrument_venue_id
                == str(instrument_id.venue_id),
                PositionLegModel.native_symbol
                == instrument_id.native_symbol,
                PositionLegModel.instrument_type
                == instrument_id.instrument_type.value,
                PositionLegModel.asset_class
                == instrument_id.asset_class.value,
            )
            .order_by(
                PositionLegModel.created_at.asc(),
                PositionLegModel.group_id.asc(),
                PositionLegModel.leg_id.asc(),
                PositionLegModel.id.asc(),
            )
        )

    @staticmethod
    def _instrument_from_model(model) -> InstrumentId:
        return InstrumentId(
            venue_id=VenueId(model.instrument_venue_id),
            native_symbol=model.native_symbol,
            instrument_type=InstrumentType(
                model.instrument_type
            ),
            asset_class=AssetClass(model.asset_class),
        )

    @staticmethod
    def _account_from_model(model) -> AccountId:
        return AccountId(
            venue_id=VenueId(model.venue_id),
            value=model.account_value,
        )

    @classmethod
    def _to_order(
        cls,
        model: ExecutionOrderModel,
    ) -> ExecutionOrder:
        return ExecutionOrder(
            order_id=OrderId(model.order_id),
            plan_id=model.plan_id,
            group_id=model.group_id,
            leg_id=model.leg_id,
            account_id=cls._account_from_model(model),
            instrument_id=cls._instrument_from_model(model),
            client_order_id=ClientOrderId(
                model.client_order_id
            ),
            venue_order_id=(
                None
                if model.venue_order_id is None
                else VenueOrderId(model.venue_order_id)
            ),
            side=OrderSide(model.side),
            order_type=OrderType(model.order_type),
            requested_quantity=model.requested_quantity,
            filled_quantity=model.filled_quantity,
            average_fill_price=model.average_fill_price,
            limit_price=model.limit_price,
            reduce_only=model.reduce_only,
            status=ExecutionOrderStatus(
                model.local_status
            ),
            rejection_reason=model.rejection_reason,
            submitted_at=_restore_optional_utc(
                model.submitted_at
            ),
            accepted_at=_restore_optional_utc(
                model.accepted_at
            ),
            filled_at=_restore_optional_utc(
                model.filled_at
            ),
            cancelled_at=_restore_optional_utc(
                model.cancelled_at
            ),
            created_at=_restore_utc(model.created_at),
            updated_at=_restore_utc(model.updated_at),
        )

    @staticmethod
    def _to_fill(
        model: ExecutionFillModel,
    ) -> ExecutionFill:
        return ExecutionFill(
            fill_id=FillId(model.fill_id),
            order_id=OrderId(model.order_id),
            venue_fill_id=(
                None
                if model.venue_fill_id is None
                else VenueFillId(model.venue_fill_id)
            ),
            quantity=model.quantity,
            price=model.price,
            fee=model.fee,
            fee_currency=model.fee_currency,
            executed_at=_restore_utc(model.executed_at),
            created_at=_restore_utc(model.created_at),
        )

    @classmethod
    def _to_position(
        cls,
        model: PositionLegModel,
    ) -> PositionLeg:
        return PositionLeg(
            group_id=model.group_id,
            leg_id=model.leg_id,
            account_id=cls._account_from_model(model),
            instrument_id=cls._instrument_from_model(model),
            side=TradeSide(model.side),
            target_quantity=model.target_quantity,
            filled_quantity=model.filled_quantity,
            current_quantity=model.current_quantity,
            average_entry_price=model.average_entry_price,
            average_exit_price=model.average_exit_price,
            status=PositionLegStatus(model.status),
            opened_at=_restore_optional_utc(
                model.opened_at
            ),
            closed_at=_restore_optional_utc(
                model.closed_at
            ),
            created_at=_restore_utc(model.created_at),
            updated_at=_restore_utc(model.updated_at),
        )
