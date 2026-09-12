"""Deterministic Grid Trading Desk application services."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal

from apps.core.domain.grid_trading import (
    GridBias,
    GridConfiguration,
    GridCycle,
    GridCycleState,
    GridFillAttribution,
    GridInstance,
    GridInstanceState,
    GridLevel,
    GridLevelState,
    GridMarketEvent,
    GridPnL,
    GridProgram,
    GridProgramState,
    GridReconciliationState,
    GridSimulationAssumptions,
    GridSpacingType,
    GridStuckPositionPolicy,
)
from apps.core.domain.orders import OrderSide
from apps.core.ports.grid_trading import (
    GridCapitalRiskPort,
    GridExecutionBoundary,
    GridInstanceStore,
    GridLedgerReader,
    GridReconciliationPort,
)
from packages.contracts.identities import FillId


class GridTradingError(RuntimeError):
    pass


def _level_price(
    config: GridConfiguration,
    *,
    index: int,
) -> Decimal:
    if config.spacing_type is GridSpacingType.GEOMETRIC:
        exponent = Decimal(abs(index)) / Decimal(config.levels_per_side)
        if index < 0:
            ratio = config.lower_price / config.center_price
            return config.center_price * (ratio ** exponent)
        ratio = config.upper_price / config.center_price
        return config.center_price * (ratio ** exponent)

    if config.spacing_type is GridSpacingType.DYNAMIC:
        step = config.center_price * config.dynamic_step_ratio
    else:
        lower_span = config.center_price - config.lower_price
        upper_span = config.upper_price - config.center_price
        step = min(lower_span, upper_span) / Decimal(config.levels_per_side)

    return config.center_price + step * Decimal(index)


def build_grid_levels(config: GridConfiguration) -> tuple[GridLevel, ...]:
    levels: list[GridLevel] = []
    for index in range(-config.levels_per_side, config.levels_per_side + 1):
        if index == 0:
            continue
        if config.bias is GridBias.LONG and index > 0:
            continue
        if config.bias is GridBias.SHORT and index < 0:
            continue
        price = _level_price(config, index=index)
        if price < config.lower_price or price > config.upper_price:
            continue
        levels.append(
            GridLevel(
                level_index=index,
                side=OrderSide.BUY if index < 0 else OrderSide.SELL,
                price=price,
                quantity=config.order_quantity,
            )
        )
    if not levels:
        raise GridTradingError("configuration produced no executable grid levels")  # noqa: E501
    return tuple(sorted(levels, key=lambda item: item.level_index))


class GridTradingDesk:
    def __init__(
        self,
        *,
        store: GridInstanceStore,
        execution: GridExecutionBoundary,
        risk: GridCapitalRiskPort,
        reconciliation: GridReconciliationPort,
        ledger: GridLedgerReader,
    ) -> None:
        self._store = store
        self._execution = execution
        self._risk = risk
        self._reconciliation = reconciliation
        self._ledger = ledger

    async def create_instance(
        self,
        *,
        program: GridProgram,
        instance_id: str,
        config: GridConfiguration,
        now: datetime,
    ) -> GridInstance:
        if program.state is not GridProgramState.ACTIVE:
            raise GridTradingError("grid program must be ACTIVE")
        cycle = GridCycle(
            cycle_id=f"{instance_id}:1",
            sequence=1,
            state=GridCycleState.OPEN,
            center_price=config.center_price,
            levels=build_grid_levels(config),
            opened_at=now,
        )
        instance = GridInstance(
            instance_id=instance_id,
            program_id=program.program_id,
            user_id=program.user_id,
            account_id=program.account_id,
            instrument_id=program.instrument_id,
            state=GridInstanceState.PENDING,
            config=config,
            risk_budget=program.risk_budget,
            cycle=cycle,
            inventory_quantity=Decimal("0"),
            created_at=now,
            updated_at=now,
        )
        if not await self._risk.reserve(instance=instance):
            raise GridTradingError("grid capital reservation rejected")
        await self._store.checkpoint(instance)
        return instance

    async def activate(self, *, user_id: int, instance_id: str, now: datetime) -> GridInstance:  # noqa: E501
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        if instance.state not in (GridInstanceState.PENDING, GridInstanceState.RECOVERY):  # noqa: E501
            return instance
        levels: list[GridLevel] = []
        recovery = False
        for level in instance.cycle.levels:
            if level.state is not GridLevelState.PENDING:
                levels.append(level)
                continue
            outcome = await self._execution.place_level(instance=instance, level=level, now=now)  # noqa: E501
            if outcome.unknown:
                recovery = True
                levels.append(level)
                break
            if not outcome.accepted:
                recovery = True
                levels.append(level)
                break
            levels.append(
                replace(
                    level,
                    state=GridLevelState.OPEN,
                    client_order_ref=outcome.client_order_ref,
                )
            )
        updated = replace(
            instance,
            state=GridInstanceState.RECOVERY if recovery else GridInstanceState.ACTIVE,  # noqa: E501
            cycle=replace(
                instance.cycle,
                state=GridCycleState.RECOVERY if recovery else instance.cycle.state,  # noqa: E501
                levels=tuple(levels) + instance.cycle.levels[len(levels):],
            ),
            updated_at=now,
        )
        await self._store.checkpoint(updated)
        return updated

    async def record_fill(
        self,
        *,
        user_id: int,
        instance_id: str,
        fill: GridFillAttribution,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        if fill.cycle_id != instance.cycle.cycle_id:
            raise GridTradingError("fill cycle does not belong to active grid cycle")  # noqa: E501
        levels: list[GridLevel] = []
        matched = False
        for level in instance.cycle.levels:
            if level.level_index != fill.level_index:
                levels.append(level)
                continue
            matched = True
            filled = level.filled_quantity + fill.quantity
            if filled > level.quantity:
                raise GridTradingError("grid fill exceeds level quantity")
            levels.append(
                replace(
                    level,
                    filled_quantity=filled,
                    state=(
                        GridLevelState.FILLED
                        if filled == level.quantity
                        else GridLevelState.PARTIALLY_FILLED
                    ),
                )
            )
        if not matched:
            raise GridTradingError("fill references unknown grid level")
        signed = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity  # noqa: E501
        updated = replace(
            instance,
            cycle=replace(instance.cycle, levels=tuple(levels)),
            inventory_quantity=instance.inventory_quantity + signed,
            updated_at=now,
        )
        notional = abs(updated.inventory_quantity) * fill.price
        if notional > updated.risk_budget.max_inventory_notional:
            updated = replace(updated, state=GridInstanceState.RECOVERY)
        await self._store.checkpoint(updated)
        return updated

    async def reconcile(
        self,
        *,
        user_id: int,
        instance_id: str,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        state = await self._reconciliation.state_for_instance(instance=instance)  # noqa: E501
        if state is GridReconciliationState.MATCHED:
            return instance
        updated = replace(instance, state=GridInstanceState.RECOVERY, updated_at=now)  # noqa: E501
        await self._store.checkpoint(updated)
        return updated

    async def pause(
        self,
        *,
        user_id: int,
        instance_id: str,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(
            user_id=user_id,
            instance_id=instance_id,
        )
        updated = replace(
            instance,
            state=GridInstanceState.STOPPED,
            updated_at=now,
        )
        await self._store.checkpoint(updated)
        return updated

    async def resume(
        self,
        *,
        user_id: int,
        instance_id: str,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(
            user_id=user_id,
            instance_id=instance_id,
        )
        if instance.state is not GridInstanceState.STOPPED:
            raise GridTradingError("only STOPPED grid may resume")
        updated = replace(
            instance,
            state=GridInstanceState.PENDING,
            updated_at=now,
        )
        await self._store.checkpoint(updated)
        return updated

    async def apply_regime(
        self,
        *,
        user_id: int,
        instance_id: str,
        regime: str,
        mark_price: Decimal,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(
            user_id=user_id,
            instance_id=instance_id,
        )
        normalized = regime.strip().upper()
        if normalized not in instance.config.allowed_regimes:
            updated = replace(
                instance,
                state=GridInstanceState.STOPPED,
                updated_at=now,
            )
            await self._store.checkpoint(updated)
            return updated
        deviation = abs(mark_price - instance.config.center_price) / instance.config.center_price  # noqa: E501
        if deviation >= instance.config.recenter_threshold_ratio:
            return await self.recenter(
                user_id=user_id,
                instance_id=instance_id,
                new_center=mark_price,
                now=now,
            )
        return instance

    async def recenter(
        self,
        *,
        user_id: int,
        instance_id: str,
        new_center: Decimal,
        now: datetime,
    ) -> GridInstance:
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        if instance.state not in (GridInstanceState.ACTIVE, GridInstanceState.RECOVERY):  # noqa: E501
            raise GridTradingError("grid instance cannot recenter from current state")  # noqa: E501
        checkpoint = replace(instance, state=GridInstanceState.RECENTERING, updated_at=now)  # noqa: E501
        await self._store.checkpoint(checkpoint)
        for level in checkpoint.cycle.levels:
            if level.state in (GridLevelState.OPEN, GridLevelState.PARTIALLY_FILLED):  # noqa: E501
                outcome = await self._execution.cancel_level(instance=checkpoint, level=level, now=now)  # noqa: E501
                if outcome.unknown or not outcome.accepted:
                    recovery = replace(checkpoint, state=GridInstanceState.RECOVERY, updated_at=now)  # noqa: E501
                    await self._store.checkpoint(recovery)
                    return recovery
        width_low = instance.config.center_price - instance.config.lower_price
        width_high = instance.config.upper_price - instance.config.center_price
        config = replace(
            instance.config,
            center_price=new_center,
            lower_price=new_center - width_low,
            upper_price=new_center + width_high,
        )
        sequence = instance.cycle.sequence + 1
        cycle = GridCycle(
            cycle_id=f"{instance.instance_id}:{sequence}",
            sequence=sequence,
            state=GridCycleState.OPEN,
            center_price=new_center,
            levels=build_grid_levels(config),
            opened_at=now,
        )
        updated = replace(
            checkpoint,
            state=GridInstanceState.PENDING,
            config=config,
            cycle=cycle,
            updated_at=now,
        )
        await self._store.checkpoint(updated)
        return updated

    async def stop(
        self,
        *,
        user_id: int,
        instance_id: str,
        now: datetime,
        flatten: bool = False,
    ) -> GridInstance:
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        if flatten and instance.inventory_quantity != 0:
            if instance.risk_budget.stuck_policy is not GridStuckPositionPolicy.REDUCE_ONLY:  # noqa: E501
                raise GridTradingError("flatten requires approved REDUCE_ONLY stuck policy")  # noqa: E501
            outcome = await self._execution.reduce_inventory(
                instance=instance,
                quantity=abs(instance.inventory_quantity),
                now=now,
            )
            if outcome.unknown or not outcome.accepted:
                recovery = replace(instance, state=GridInstanceState.RECOVERY, updated_at=now)  # noqa: E501
                await self._store.checkpoint(recovery)
                return recovery
        updated = replace(instance, state=GridInstanceState.STOPPED, updated_at=now)  # noqa: E501
        await self._store.checkpoint(updated)
        await self._risk.release(instance=updated)
        return updated

    async def pnl(
        self,
        *,
        user_id: int,
        instance_id: str,
        mark_price: Decimal,
    ) -> GridPnL:
        instance = await self._require_owned(user_id=user_id, instance_id=instance_id)  # noqa: E501
        fills = await self._ledger.fills_for_instance(user_id=user_id, instance_id=instance_id)  # noqa: E501
        return project_grid_pnl(instance=instance, fills=fills, mark_price=mark_price)  # noqa: E501

    async def list_for_user(self, *, user_id: int) -> tuple[GridInstance, ...]:
        return await self._store.list_for_user(user_id=user_id)

    async def _require_owned(self, *, user_id: int, instance_id: str) -> GridInstance:  # noqa: E501
        instance = await self._store.load(user_id=user_id, instance_id=instance_id)  # noqa: E501
        if instance is None:
            raise GridTradingError("grid instance not found for user")
        if instance.user_id != user_id:
            raise GridTradingError("grid ownership mismatch")
        return instance


def project_grid_pnl(
    *,
    instance: GridInstance,
    fills: tuple[GridFillAttribution, ...],
    mark_price: Decimal,
) -> GridPnL:
    if not isinstance(fills, tuple):
        raise ValueError("fills must be tuple")
    mark_price = abs(mark_price)
    if mark_price <= 0:
        raise ValueError("mark_price must be positive")
    quantity = Decimal("0")
    average_cost = Decimal("0")
    realized = Decimal("0")
    fees = Decimal("0")
    seen: set[str] = set()
    for fill in sorted(fills, key=lambda item: (item.occurred_at, str(item.fill_id))):  # noqa: E501
        fill_key = str(fill.fill_id)
        if fill_key in seen:
            raise GridTradingError("duplicate fill in grid PnL projection")
        seen.add(fill_key)
        signed = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity  # noqa: E501
        fees += fill.fee
        if quantity == 0 or quantity * signed > 0:
            new_qty = quantity + signed
            average_cost = (
                (abs(quantity) * average_cost + abs(signed) * fill.price) / abs(new_qty)  # noqa: E501
            )
            quantity = new_qty
            continue
        closing = min(abs(quantity), abs(signed))
        if quantity > 0:
            realized += (fill.price - average_cost) * closing
        else:
            realized += (average_cost - fill.price) * closing
        quantity += signed
        if quantity == 0:
            average_cost = Decimal("0")
        elif abs(signed) > closing:
            average_cost = fill.price
    if quantity > 0:
        unrealized = (mark_price - average_cost) * quantity
    elif quantity < 0:
        unrealized = (average_cost - mark_price) * abs(quantity)
    else:
        unrealized = Decimal("0")
    return GridPnL(
        instance_id=instance.instance_id,
        cycle_id=instance.cycle.cycle_id,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        fees=fees,
        net_pnl=realized + unrealized - fees,
        inventory_quantity=quantity,
        mark_price=mark_price,
    )


def simulate_grid_cycle(
    *,
    cycle: GridCycle,
    events: tuple[GridMarketEvent, ...],
    assumptions: GridSimulationAssumptions,
) -> tuple[GridFillAttribution, ...]:
    fills: list[GridFillAttribution] = []
    remaining = {level.level_index: level.quantity for level in cycle.levels}
    sequence = 0
    active_at = cycle.opened_at + timedelta(milliseconds=assumptions.latency_ms)  # noqa: E501
    for event in sorted(events, key=lambda item: item.occurred_at):
        if event.occurred_at < active_at:
            continue
        for level in cycle.levels:
            available = remaining[level.level_index]
            if available <= 0:
                continue
            touched = (
                level.side is OrderSide.BUY and event.ask <= level.price
            ) or (
                level.side is OrderSide.SELL and event.bid >= level.price
            )
            if not touched:
                continue
            book_quantity = (
                event.available_ask_quantity
                if level.side is OrderSide.BUY
                else event.available_bid_quantity
            )
            fill_quantity = min(
                available,
                book_quantity * assumptions.queue_fill_fraction,
            )
            if fill_quantity <= 0:
                continue
            sequence += 1
            adverse = assumptions.adverse_selection_bps / Decimal("10000")
            slippage = assumptions.slippage_bps / Decimal("10000")
            penalty = adverse + slippage
            execution_price = (
                level.price * (Decimal("1") + penalty)
                if level.side is OrderSide.BUY
                else level.price * (Decimal("1") - penalty)
            )
            fee = execution_price * fill_quantity * assumptions.maker_fee_rate
            fills.append(
                GridFillAttribution(
                    fill_id=FillId(f"sim-{cycle.cycle_id}-{sequence}"),
                    cycle_id=cycle.cycle_id,
                    level_index=level.level_index,
                    side=level.side,
                    quantity=fill_quantity,
                    price=execution_price,
                    fee=fee,
                    maker=True,
                    occurred_at=event.occurred_at,
                )
            )
            remaining[level.level_index] -= fill_quantity
    return tuple(fills)
