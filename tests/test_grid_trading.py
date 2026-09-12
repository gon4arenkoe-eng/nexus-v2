"""Phase 7G Grid Trading Desk deterministic behavior tests."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.core.application.grid_trading import (
    GridTradingDesk,
    GridTradingError,
    build_grid_levels,
    project_grid_pnl,
    simulate_grid_cycle,
)
from apps.core.domain.grid_trading import (
    GridBias,
    GridConfiguration,
    GridCycle,
    GridCycleState,
    GridFillAttribution,
    GridInstance,
    GridInstanceState,
    GridLevelState,
    GridMarketEvent,
    GridProgram,
    GridProgramState,
    GridReconciliationState,
    GridRiskBudget,
    GridSimulationAssumptions,
    GridSpacingType,
    GridStuckPositionPolicy,
)
from apps.core.domain.orders import OrderSide
from apps.core.ports.grid_trading import GridOrderOutcome
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    FillId,
    InstrumentId,
    InstrumentType,
    VenueId,
)

NOW = datetime(2026, 9, 12, 18, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BINANCE"), 7)
INSTRUMENT = InstrumentId(
    VenueId("BINANCE"),
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


def config(**changes) -> GridConfiguration:
    values = {
        "lower_price": Decimal("90"),
        "upper_price": Decimal("110"),
        "center_price": Decimal("100"),
        "spacing_type": GridSpacingType.ARITHMETIC,
        "levels_per_side": 2,
        "order_quantity": Decimal("1"),
        "dynamic_step_ratio": Decimal("0.02"),
        "bias": GridBias.NEUTRAL,
        "recenter_threshold_ratio": Decimal("0.05"),
        "maker_fee_rate": Decimal("0.001"),
        "taker_fee_rate": Decimal("0.002"),
        "max_slippage_bps": Decimal("25"),
        "allowed_regimes": ("SIDEWAYS", "TREND_UP"),
    }
    values.update(changes)
    return GridConfiguration(**values)


def budget(**changes) -> GridRiskBudget:
    values = {
        "reserved_capital": Decimal("1000"),
        "max_gross_exposure": Decimal("2000"),
        "max_inventory_notional": Decimal("500"),
        "max_drawdown_ratio": Decimal("0.10"),
        "max_stuck_seconds": 3600,
        "stuck_policy": GridStuckPositionPolicy.HALT,
    }
    values.update(changes)
    return GridRiskBudget(**values)


def program(**changes) -> GridProgram:
    values = {
        "program_id": "grid-program-1",
        "user_id": 7,
        "account_id": ACCOUNT,
        "instrument_id": INSTRUMENT,
        "state": GridProgramState.ACTIVE,
        "risk_budget": budget(),
    }
    values.update(changes)
    return GridProgram(**values)


class MemoryStore:
    def __init__(self) -> None:
        self.data: dict[tuple[int, str], GridInstance] = {}

    async def load(self, *, user_id: int, instance_id: str):
        return self.data.get((user_id, instance_id))

    async def checkpoint(self, instance: GridInstance) -> None:
        self.data[(instance.user_id, instance.instance_id)] = instance

    async def list_for_user(self, *, user_id: int):
        return tuple(
            value
            for (owner, _), value in sorted(self.data.items())
            if owner == user_id
        )


class Execution:
    def __init__(self, *, unknown_at: int | None = None) -> None:
        self.calls: list[tuple[str, int]] = []
        self.unknown_at = unknown_at

    async def place_level(self, *, instance, level, now):
        self.calls.append(("place", level.level_index))
        unknown = self.unknown_at == len(self.calls)
        return GridOrderOutcome(
            client_order_ref=f"grid-{instance.instance_id}-{level.level_index}",  # noqa: E501
            accepted=not unknown,
            unknown=unknown,
        )

    async def cancel_level(self, *, instance, level, now):
        self.calls.append(("cancel", level.level_index))
        return GridOrderOutcome(
            client_order_ref=level.client_order_ref or "cancel",
            accepted=True,
        )

    async def reduce_inventory(self, *, instance, quantity, now):
        self.calls.append(("reduce", 0))
        return GridOrderOutcome(client_order_ref="reduce", accepted=True)


class Risk:
    def __init__(self, approved: bool = True) -> None:
        self.approved = approved
        self.reserved: list[str] = []
        self.released: list[str] = []

    async def reserve(self, *, instance):
        self.reserved.append(instance.instance_id)
        return self.approved

    async def release(self, *, instance):
        self.released.append(instance.instance_id)


class Reconciliation:
    def __init__(self, state=GridReconciliationState.MATCHED) -> None:
        self.state = state

    async def state_for_instance(self, *, instance):
        return self.state


class Ledger:
    def __init__(self, fills=()) -> None:
        self.fills = fills

    async def fills_for_instance(self, *, user_id, instance_id):
        return self.fills


def desk(*, execution=None, risk=None, reconciliation=None, ledger=None):
    store = MemoryStore()
    service = GridTradingDesk(
        store=store,
        execution=execution or Execution(),
        risk=risk or Risk(),
        reconciliation=reconciliation or Reconciliation(),
        ledger=ledger or Ledger(),
    )
    return service, store


def create_active(service: GridTradingDesk):
    async def scenario():
        await service.create_instance(
            program=program(),
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )
        return await service.activate(user_id=7, instance_id="grid-1", now=NOW)

    return asyncio.run(scenario())


def test_arithmetic_grid_build_is_deterministic_and_symmetric() -> None:
    levels = build_grid_levels(config())
    assert [item.level_index for item in levels] == [-2, -1, 1, 2]
    assert [item.price for item in levels] == [
        Decimal("90"),
        Decimal("95"),
        Decimal("105"),
        Decimal("110"),
    ]
    assert [item.side for item in levels] == [
        OrderSide.BUY,
        OrderSide.BUY,
        OrderSide.SELL,
        OrderSide.SELL,
    ]


def test_long_and_short_bias_filter_grid_sides() -> None:
    long_levels = build_grid_levels(config(bias=GridBias.LONG))
    short_levels = build_grid_levels(config(bias=GridBias.SHORT))
    assert all(item.side is OrderSide.BUY for item in long_levels)
    assert all(item.side is OrderSide.SELL for item in short_levels)


def test_geometric_grid_stays_inside_configured_range() -> None:
    levels = build_grid_levels(config(spacing_type=GridSpacingType.GEOMETRIC))
    assert len(levels) == 4
    assert min(item.price for item in levels) >= Decimal("90")
    assert max(item.price for item in levels) <= Decimal("110")


def test_dynamic_grid_uses_dynamic_step_ratio() -> None:
    levels = build_grid_levels(
        config(
            spacing_type=GridSpacingType.DYNAMIC,
            dynamic_step_ratio=Decimal("0.02"),
        )
    )
    assert [item.price for item in levels] == [
        Decimal("96"),
        Decimal("98"),
        Decimal("102"),
        Decimal("104"),
    ]


def test_create_reserves_capital_before_checkpoint() -> None:
    risk = Risk()
    service, store = desk(risk=risk)

    async def scenario():
        return await service.create_instance(
            program=program(),
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )

    instance = asyncio.run(scenario())
    assert risk.reserved == ["grid-1"]
    assert instance.state is GridInstanceState.PENDING
    assert store.data[(7, "grid-1")] == instance


def test_create_fails_closed_when_capital_reservation_rejected() -> None:
    service, _ = desk(risk=Risk(approved=False))

    async def scenario():
        await service.create_instance(
            program=program(),
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )

    with pytest.raises(GridTradingError, match="reservation rejected"):
        asyncio.run(scenario())


def test_activate_places_all_levels_via_execution_boundary() -> None:
    execution = Execution()
    service, _ = desk(execution=execution)
    instance = create_active(service)
    assert instance.state is GridInstanceState.ACTIVE
    assert [kind for kind, _ in execution.calls] == ["place"] * 4
    assert all(level.state is GridLevelState.OPEN for level in instance.cycle.levels)  # noqa: E501


def test_unknown_level_outcome_moves_grid_to_recovery_and_stops_submission() -> None:  # noqa: E501
    execution = Execution(unknown_at=2)
    service, _ = desk(execution=execution)
    instance = create_active(service)
    assert instance.state is GridInstanceState.RECOVERY
    assert len(execution.calls) == 2
    assert instance.cycle.state is GridCycleState.RECOVERY


def test_fill_updates_level_and_inventory() -> None:
    service, _ = desk()
    create_active(service)
    fill = GridFillAttribution(
        fill_id=FillId("fill-1"),
        cycle_id="grid-1:1",
        level_index=-1,
        side=OrderSide.BUY,
        quantity=Decimal("0.5"),
        price=Decimal("95"),
        fee=Decimal("0.05"),
        maker=True,
        occurred_at=NOW,
    )

    async def scenario():
        return await service.record_fill(
            user_id=7,
            instance_id="grid-1",
            fill=fill,
            now=NOW,
        )

    instance = asyncio.run(scenario())
    assert instance.inventory_quantity == Decimal("0.5")
    level = next(item for item in instance.cycle.levels if item.level_index == -1)  # noqa: E501
    assert level.state is GridLevelState.PARTIALLY_FILLED


def test_inventory_limit_moves_instance_to_recovery() -> None:
    service, _ = desk()

    async def scenario():
        instance = await service.create_instance(
            program=program(risk_budget=budget(max_inventory_notional=Decimal("50"))),  # noqa: E501
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )
        await service.activate(user_id=7, instance_id="grid-1", now=NOW)
        fill = GridFillAttribution(
            fill_id=FillId("fill-risk"),
            cycle_id=instance.cycle.cycle_id,
            level_index=-1,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("95"),
            fee=Decimal("0"),
            maker=True,
            occurred_at=NOW,
        )
        return await service.record_fill(
            user_id=7,
            instance_id="grid-1",
            fill=fill,
            now=NOW,
        )

    updated = asyncio.run(scenario())
    assert updated.state is GridInstanceState.RECOVERY


def test_non_matched_reconciliation_is_explicit_and_fail_closed() -> None:
    service, _ = desk(
        reconciliation=Reconciliation(GridReconciliationState.DISCREPANCY)
    )
    create_active(service)

    async def scenario():
        return await service.reconcile(user_id=7, instance_id="grid-1", now=NOW)  # noqa: E501

    updated = asyncio.run(scenario())
    assert updated.state is GridInstanceState.RECOVERY


def test_recenter_cancels_old_orders_and_opens_new_cycle() -> None:
    execution = Execution()
    service, _ = desk(execution=execution)
    create_active(service)

    async def scenario():
        return await service.recenter(
            user_id=7,
            instance_id="grid-1",
            new_center=Decimal("120"),
            now=NOW + timedelta(minutes=1),
        )

    updated = asyncio.run(scenario())
    assert updated.state is GridInstanceState.PENDING
    assert updated.cycle.sequence == 2
    assert updated.cycle.cycle_id == "grid-1:2"
    assert sum(1 for kind, _ in execution.calls if kind == "cancel") == 4


def test_stop_releases_reserved_capital() -> None:
    risk = Risk()
    service, _ = desk(risk=risk)
    create_active(service)

    async def scenario():
        return await service.stop(user_id=7, instance_id="grid-1", now=NOW)

    stopped = asyncio.run(scenario())
    assert stopped.state is GridInstanceState.STOPPED
    assert risk.released == ["grid-1"]


def test_flatten_requires_explicit_reduce_only_policy() -> None:
    service, store = desk()
    active = create_active(service)
    store.data[(7, "grid-1")] = replace(active, inventory_quantity=Decimal("1"))  # noqa: E501

    async def scenario():
        await service.stop(user_id=7, instance_id="grid-1", now=NOW, flatten=True)  # noqa: E501

    with pytest.raises(GridTradingError, match="REDUCE_ONLY"):
        asyncio.run(scenario())


def test_reduce_only_stuck_policy_allows_flatten_through_execution_boundary() -> None:  # noqa: E501
    execution = Execution()
    service, store = desk(execution=execution)

    async def scenario():
        instance = await service.create_instance(
            program=program(
                risk_budget=budget(stuck_policy=GridStuckPositionPolicy.REDUCE_ONLY)  # noqa: E501
            ),
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )
        instance = await service.activate(user_id=7, instance_id="grid-1", now=NOW)  # noqa: E501
        store.data[(7, "grid-1")] = replace(
            instance,
            inventory_quantity=Decimal("1"),
        )
        return await service.stop(
            user_id=7,
            instance_id="grid-1",
            now=NOW,
            flatten=True,
        )

    stopped = asyncio.run(scenario())
    assert stopped.state is GridInstanceState.STOPPED
    assert ("reduce", 0) in execution.calls


def test_multi_user_control_listing_is_scoped() -> None:
    service, store = desk()

    async def scenario():
        first = await service.create_instance(
            program=program(),
            instance_id="grid-1",
            config=config(),
            now=NOW,
        )
        second = replace(first, instance_id="grid-2", user_id=8, program_id="grid-program-2")  # noqa: E501
        await store.checkpoint(second)
        return await service.list_for_user(user_id=7)

    listed = asyncio.run(scenario())
    assert [item.instance_id for item in listed] == ["grid-1"]


def test_grid_pnl_projection_uses_fill_source_once_and_tracks_inventory() -> None:  # noqa: E501
    levels = build_grid_levels(config())
    instance = GridInstance(
        instance_id="grid-1",
        program_id="program-1",
        user_id=7,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        state=GridInstanceState.ACTIVE,
        config=config(),
        risk_budget=budget(),
        cycle=GridCycle(
            cycle_id="grid-1:1",
            sequence=1,
            state=GridCycleState.OPEN,
            center_price=Decimal("100"),
            levels=levels,
            opened_at=NOW,
        ),
        inventory_quantity=Decimal("0"),
        created_at=NOW,
        updated_at=NOW,
    )
    fills = (
        GridFillAttribution(
            FillId("buy-1"), "grid-1:1", -1, OrderSide.BUY,
            Decimal("1"), Decimal("95"), Decimal("0.1"), True, NOW,
        ),
        GridFillAttribution(
            FillId("sell-1"), "grid-1:1", 1, OrderSide.SELL,
            Decimal("1"), Decimal("105"), Decimal("0.1"), True,
            NOW + timedelta(seconds=1),
        ),
    )
    pnl = project_grid_pnl(instance=instance, fills=fills, mark_price=Decimal("100"))  # noqa: E501
    assert pnl.realized_pnl == Decimal("10")
    assert pnl.unrealized_pnl == Decimal("0")
    assert pnl.fees == Decimal("0.2")
    assert pnl.net_pnl == Decimal("9.8")
    assert pnl.inventory_quantity == 0


def test_grid_pnl_rejects_duplicate_fill_to_prevent_double_count() -> None:
    service, _ = desk()
    instance = create_active(service)
    fill = GridFillAttribution(
        FillId("dup"), "grid-1:1", -1, OrderSide.BUY,
        Decimal("1"), Decimal("95"), Decimal("0"), True, NOW,
    )
    with pytest.raises(GridTradingError, match="duplicate fill"):
        project_grid_pnl(
            instance=instance,
            fills=(fill, fill),
            mark_price=Decimal("100"),
        )


def test_simulator_models_queue_liquidity_fees_and_adverse_selection() -> None:
    cycle = GridCycle(
        cycle_id="sim-cycle",
        sequence=1,
        state=GridCycleState.OPEN,
        center_price=Decimal("100"),
        levels=build_grid_levels(config()),
        opened_at=NOW,
    )
    assumptions = GridSimulationAssumptions(
        maker_fee_rate=Decimal("0.001"),
        taker_fee_rate=Decimal("0.002"),
        slippage_bps=Decimal("5"),
        adverse_selection_bps=Decimal("10"),
        queue_fill_fraction=Decimal("0.5"),
        latency_ms=50,
    )
    events = (
        GridMarketEvent(
            bid=Decimal("94.8"),
            ask=Decimal("95"),
            available_bid_quantity=Decimal("10"),
            available_ask_quantity=Decimal("1"),
            occurred_at=NOW + timedelta(milliseconds=100),
        ),
    )
    fills = simulate_grid_cycle(cycle=cycle, events=events, assumptions=assumptions)  # noqa: E501
    assert len(fills) == 1
    assert fills[0].quantity == Decimal("0.5")
    assert fills[0].fee > 0
    assert fills[0].price > Decimal("95")


def test_application_layer_has_no_direct_venue_or_sqlalchemy_authority() -> None:  # noqa: E501
    source = __import__("pathlib").Path(
        "apps/core/application/grid_trading.py"
    ).read_text()
    forbidden = (
        "VenueAdapter",
        "submit_order(",
        "cancel_order(",
        "sqlalchemy",
        "FastAPI",
        "commit(",
        "rollback(",
    )
    assert not any(item in source for item in forbidden)


def test_regime_outside_allowlist_stops_grid_fail_closed() -> None:
    service, _ = desk()
    create_active(service)

    async def scenario():
        return await service.apply_regime(
            user_id=7,
            instance_id="grid-1",
            regime="VOLATILE",
            mark_price=Decimal("100"),
            now=NOW,
        )

    updated = asyncio.run(scenario())
    assert updated.state is GridInstanceState.STOPPED


def test_regime_deviation_triggers_recenter() -> None:
    service, _ = desk()
    create_active(service)

    async def scenario():
        return await service.apply_regime(
            user_id=7,
            instance_id="grid-1",
            regime="SIDEWAYS",
            mark_price=Decimal("120"),
            now=NOW,
        )

    updated = asyncio.run(scenario())
    assert updated.state is GridInstanceState.PENDING
    assert updated.cycle.sequence == 2
    assert updated.config.center_price == Decimal("120")


def test_control_plane_pause_and_resume_are_user_scoped() -> None:
    service, _ = desk()
    create_active(service)

    async def scenario():
        paused = await service.pause(
            user_id=7,
            instance_id="grid-1",
            now=NOW,
        )
        resumed = await service.resume(
            user_id=7,
            instance_id="grid-1",
            now=NOW,
        )
        return paused, resumed

    paused, resumed = asyncio.run(scenario())
    assert paused.state is GridInstanceState.STOPPED
    assert resumed.state is GridInstanceState.PENDING


@pytest.mark.parametrize(
    "source_state",
    (
        GridReconciliationState.STALE,
        GridReconciliationState.UNKNOWN,
        GridReconciliationState.DISCREPANCY,
    ),
)
def test_non_current_grid_reconciliation_never_hides_state(source_state) -> None:  # noqa: E501
    service, _ = desk(reconciliation=Reconciliation(source_state))
    create_active(service)

    async def scenario():
        return await service.reconcile(
            user_id=7,
            instance_id="grid-1",
            now=NOW,
        )

    assert asyncio.run(scenario()).state is GridInstanceState.RECOVERY
