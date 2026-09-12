"""Repository for durable Grid Trading Desk state."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.grid_trading import (
    GridBias,
    GridConfiguration,
    GridCycle,
    GridCycleState,
    GridInstance,
    GridInstanceState,
    GridLevel,
    GridLevelState,
    GridRiskBudget,
    GridSpacingType,
    GridStuckPositionPolicy,
)
from apps.core.domain.orders import OrderSide
from infra.persistence.models.grid_trading import GridInstanceStateModel
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class GridInstanceStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, user_id: int, instance_id: str) -> GridInstance | None:  # noqa: E501
        result = await self._session.execute(
            select(GridInstanceStateModel).where(
                GridInstanceStateModel.user_id == user_id,
                GridInstanceStateModel.instance_id == instance_id,
            )
        )
        model = result.scalar_one_or_none()
        return None if model is None else self._to_domain(model)

    async def list_for_user(self, *, user_id: int) -> tuple[GridInstance, ...]:
        result = await self._session.execute(
            select(GridInstanceStateModel)
            .where(GridInstanceStateModel.user_id == user_id)
            .order_by(GridInstanceStateModel.instance_id)
        )
        return tuple(self._to_domain(model) for model in result.scalars().all())  # noqa: E501

    async def upsert(self, instance: GridInstance) -> None:
        model = await self._session.get(
            GridInstanceStateModel,
            (instance.user_id, instance.instance_id),
        )
        payload = self._serialize(instance)
        if model is None:
            self._session.add(
                GridInstanceStateModel(
                    user_id=instance.user_id,
                    instance_id=instance.instance_id,
                    program_id=instance.program_id,
                    account_venue_id=str(instance.account_id.venue_id),
                    account_id=instance.account_id.value,
                    instrument_venue_id=str(instance.instrument_id.venue_id),
                    instrument_symbol=instance.instrument_id.native_symbol,
                    instrument_type=instance.instrument_id.instrument_type.value,  # noqa: E501
                    asset_class=instance.instrument_id.asset_class.value,
                    state=instance.state.value,
                    payload_json=payload,
                    created_at=instance.created_at,
                    updated_at=instance.updated_at,
                )
            )
            return
        if (
            model.program_id != instance.program_id
            or model.account_id != instance.account_id.value
            or model.instrument_symbol != instance.instrument_id.native_symbol
        ):
            raise ValueError("persisted grid ownership conflict")
        model.state = instance.state.value
        model.payload_json = payload
        model.updated_at = instance.updated_at

    @staticmethod
    def _serialize(instance: GridInstance) -> str:
        config = instance.config
        budget = instance.risk_budget
        cycle = instance.cycle
        return json.dumps(
            {
                "config": {
                    "lower_price": str(config.lower_price),
                    "upper_price": str(config.upper_price),
                    "center_price": str(config.center_price),
                    "spacing_type": config.spacing_type.value,
                    "levels_per_side": config.levels_per_side,
                    "order_quantity": str(config.order_quantity),
                    "dynamic_step_ratio": str(config.dynamic_step_ratio),
                    "bias": config.bias.value,
                    "recenter_threshold_ratio": str(config.recenter_threshold_ratio),  # noqa: E501
                    "maker_fee_rate": str(config.maker_fee_rate),
                    "taker_fee_rate": str(config.taker_fee_rate),
                    "max_slippage_bps": str(config.max_slippage_bps),
                    "allowed_regimes": list(config.allowed_regimes),
                },
                "risk_budget": {
                    "reserved_capital": str(budget.reserved_capital),
                    "max_gross_exposure": str(budget.max_gross_exposure),
                    "max_inventory_notional": str(budget.max_inventory_notional),  # noqa: E501
                    "max_drawdown_ratio": str(budget.max_drawdown_ratio),
                    "max_stuck_seconds": budget.max_stuck_seconds,
                    "stuck_policy": budget.stuck_policy.value,
                },
                "cycle": {
                    "cycle_id": cycle.cycle_id,
                    "sequence": cycle.sequence,
                    "state": cycle.state.value,
                    "center_price": str(cycle.center_price),
                    "opened_at": cycle.opened_at.isoformat(),
                    "closed_at": None if cycle.closed_at is None else cycle.closed_at.isoformat(),  # noqa: E501
                    "levels": [
                        {
                            "level_index": level.level_index,
                            "side": level.side.value,
                            "price": str(level.price),
                            "quantity": str(level.quantity),
                            "state": level.state.value,
                            "client_order_ref": level.client_order_ref,
                            "filled_quantity": str(level.filled_quantity),
                        }
                        for level in cycle.levels
                    ],
                },
                "inventory_quantity": str(instance.inventory_quantity),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def _to_domain(cls, model: GridInstanceStateModel) -> GridInstance:
        raw = json.loads(model.payload_json)
        config_raw = raw["config"]
        budget_raw = raw["risk_budget"]
        cycle_raw = raw["cycle"]
        venue_id = VenueId(model.account_venue_id)
        account_id = AccountId(venue_id=venue_id, value=model.account_id)
        instrument_id = InstrumentId(
            venue_id=VenueId(model.instrument_venue_id),
            native_symbol=model.instrument_symbol,
            instrument_type=InstrumentType(model.instrument_type),
            asset_class=AssetClass(model.asset_class),
        )
        config = GridConfiguration(
            lower_price=Decimal(config_raw["lower_price"]),
            upper_price=Decimal(config_raw["upper_price"]),
            center_price=Decimal(config_raw["center_price"]),
            spacing_type=GridSpacingType(config_raw["spacing_type"]),
            levels_per_side=config_raw["levels_per_side"],
            order_quantity=Decimal(config_raw["order_quantity"]),
            dynamic_step_ratio=Decimal(config_raw["dynamic_step_ratio"]),
            bias=GridBias(config_raw["bias"]),
            recenter_threshold_ratio=Decimal(config_raw["recenter_threshold_ratio"]),  # noqa: E501
            maker_fee_rate=Decimal(config_raw["maker_fee_rate"]),
            taker_fee_rate=Decimal(config_raw["taker_fee_rate"]),
            max_slippage_bps=Decimal(config_raw["max_slippage_bps"]),
            allowed_regimes=tuple(config_raw["allowed_regimes"]),
        )
        budget = GridRiskBudget(
            reserved_capital=Decimal(budget_raw["reserved_capital"]),
            max_gross_exposure=Decimal(budget_raw["max_gross_exposure"]),
            max_inventory_notional=Decimal(budget_raw["max_inventory_notional"]),  # noqa: E501
            max_drawdown_ratio=Decimal(budget_raw["max_drawdown_ratio"]),
            max_stuck_seconds=budget_raw["max_stuck_seconds"],
            stuck_policy=GridStuckPositionPolicy(budget_raw["stuck_policy"]),
        )
        levels = tuple(
            GridLevel(
                level_index=item["level_index"],
                side=OrderSide(item["side"]),
                price=Decimal(item["price"]),
                quantity=Decimal(item["quantity"]),
                state=GridLevelState(item["state"]),
                client_order_ref=item["client_order_ref"],
                filled_quantity=Decimal(item["filled_quantity"]),
            )
            for item in cycle_raw["levels"]
        )
        cycle = GridCycle(
            cycle_id=cycle_raw["cycle_id"],
            sequence=cycle_raw["sequence"],
            state=GridCycleState(cycle_raw["state"]),
            center_price=Decimal(cycle_raw["center_price"]),
            levels=levels,
            opened_at=_dt(cycle_raw["opened_at"]),
            closed_at=None if cycle_raw["closed_at"] is None else _dt(cycle_raw["closed_at"]),  # noqa: E501
        )
        created = model.created_at if model.created_at.tzinfo is not None else model.created_at.replace(tzinfo=UTC)  # noqa: E501
        updated = model.updated_at if model.updated_at.tzinfo is not None else model.updated_at.replace(tzinfo=UTC)  # noqa: E501
        return GridInstance(
            instance_id=model.instance_id,
            program_id=model.program_id,
            user_id=model.user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            state=GridInstanceState(model.state),
            config=config,
            risk_budget=budget,
            cycle=cycle,
            inventory_quantity=Decimal(raw["inventory_quantity"]),
            created_at=created,
            updated_at=updated,
        )
