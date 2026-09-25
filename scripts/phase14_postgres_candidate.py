"""PostgreSQL-backed Phase 14 simulated execution candidate.

This candidate has no real exchange write authority.

Durable path:

ExecutionPlan / PositionGroup / PositionLeg / ExecutionOrder
    -> PostgreSQL
ExecutionCoordinatorState
    -> PostgreSQL
simulated VenueOrderResult observation
    -> PostgreSQL
restart
    -> PostgreSQL reload
    -> coordinator recovery
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from apps.core.application.execution_coordinator import (
    SingleLegExecutionCoordinator,
)
from apps.core.application.portfolio_risk import PortfolioRiskEngine
from apps.core.application.reconciliation_orchestrator import (
    ReconciliationPassOrchestrator,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
    StartupReconciliationInput,
)
from apps.core.domain.execution import (
    ExecutionLegPlan,
    ExecutionPlan,
)
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.intents import (
    TradeIntentShape,
    TradeSide,
)
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.domain.portfolio_risk import (
    PortfolioRiskDecisionState,
    PortfolioRiskLimits,
    PortfolioRiskRequest,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskLegCandidate,
    RiskObservationState,
)
from apps.core.domain.positions import (
    PositionGroup,
    PositionGroupStatus,
    PositionLeg,
    PositionLegStatus,
)
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.portfolio_risk import SingleLegRiskDecision
from apps.core.ports.venue import (
    VenueCapabilities,
    VenueOrderRequest,
    VenueOrderResult,
    VenueOrderState,
)
from infra.persistence.application.core_execution import (
    CoreExecutionPersistenceService,
)
from infra.persistence.application.execution_coordinator import (
    SqlAlchemyExecutionCoordinatorStateStore,
)
from infra.persistence.application.phase14_simulated_venue import (
    SqlAlchemyPhase14SimulatedVenueObservationStore,
)
from infra.persistence.application.reconciliation_snapshot import (
    SqlAlchemyLocalReconciliationSnapshotProvider,
)
from infra.persistence.session import (
    create_persistence_engine,
    create_session_factory,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    OrderId,
    VenueId,
    VenueOrderId,
)


NOW = datetime(2026, 9, 21, 18, 0, tzinfo=UTC)
USER_ID = 1
VENUE = VenueId("SIM")
ACCOUNT = AccountId(VENUE, 1)
INSTRUMENT = InstrumentId(
    VENUE,
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


class RecordingEvidencePort:
    def __init__(self) -> None:
        self.results: list[ReconciliationResult] = []

    async def persist_result(
        self,
        result: ReconciliationResult,
    ) -> None:
        self.results.append(result)


class AllowSingleLegPolicy:
    def evaluate(self, *, candidate, portfolio):
        return SingleLegRiskDecision(approved=True)


class Phase14PersistentSimulatedVenue:
    """Simulation-only VenueAdapter backed by durable observations."""

    def __init__(
        self,
        *,
        store: SqlAlchemyPhase14SimulatedVenueObservationStore,
        user_id: int,
    ) -> None:
        self._store = store
        self._user_id = user_id
        self.submitted: list[VenueOrderRequest] = []

    @property
    def capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(frozenset())

    async def submit_order(
        self,
        request: VenueOrderRequest,
    ) -> VenueOrderResult:
        venue_order_id = VenueOrderId(
            f"sim-{request.client_order_id}"
        )

        result = VenueOrderResult(
            client_order_id=request.client_order_id,
            venue_order_id=venue_order_id,
            state=VenueOrderState.ACCEPTED,
            requested_quantity=request.quantity,
            filled_quantity=Decimal("0"),
        )

        await self._store.record_accepted(
            user_id=self._user_id,
            account_id=request.account_id,
            instrument_id=request.instrument_id,
            result=result,
            observed_at=NOW,
        )

        self.submitted.append(request)
        return result

    async def cancel_order(
        self,
        *,
        account_id,
        instrument_id,
        venue_order_id,
    ):
        raise RuntimeError(
            "Phase14 simulated candidate does not cancel"
        )

    async def get_order(
        self,
        *,
        account_id,
        instrument_id,
        venue_order_id,
    ):
        return await self._store.load_by_venue_order_id(
            user_id=self._user_id,
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=venue_order_id,
        )

    async def get_open_orders(
        self,
        *,
        account_id,
        instrument_id=None,
    ):
        if instrument_id is None:
            raise RuntimeError(
                "Phase14 simulated recovery requires instrument scope"
            )

        return await self._store.load_open_orders(
            user_id=self._user_id,
            account_id=account_id,
            instrument_id=instrument_id,
        )

    async def get_positions(self, *, account_id):
        return ()

    async def get_account_state(self, *, account_id):
        raise RuntimeError("not required")

    async def get_fills(
        self,
        *,
        account_id,
        instrument_id=None,
        since=None,
    ):
        return ()


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()

    if not value:
        raise RuntimeError(
            f"required environment variable is missing: {name}"
        )

    return value


def _run_id() -> str:
    value = os.environ.get(
        "NEXUS_PHASE14_CANDIDATE_RUN_ID",
        "bingx-shadow",
    ).strip()

    if not value:
        raise RuntimeError(
            "NEXUS_PHASE14_CANDIDATE_RUN_ID must be non-empty"
        )

    if len(value) > 80:
        raise RuntimeError(
            "NEXUS_PHASE14_CANDIDATE_RUN_ID is too long"
        )

    return value


def _risk_engine() -> PortfolioRiskEngine:
    return PortfolioRiskEngine(
        limits=PortfolioRiskLimits(
            max_open_position_groups=10,
            max_gross_exposure=Decimal("20000"),
            max_net_exposure=Decimal("15000"),
            max_account_exposure=Decimal("10000"),
            max_venue_exposure=Decimal("15000"),
            max_strategy_exposure=Decimal("10000"),
            max_instrument_exposure=Decimal("6000"),
            max_currency_concentration=Decimal("1"),
            max_correlation_cluster_exposure=Decimal("12000"),
            max_leverage=Decimal("5"),
            max_margin_utilization=Decimal("0.8"),
            max_daily_drawdown=Decimal("0.05"),
            max_rolling_drawdown=Decimal("0.10"),
            max_order_liquidity_ratio=Decimal("0.10"),
            max_expected_slippage_bps=Decimal("25"),
            hedge_tolerance=Decimal("0.05"),
        ),
        single_leg_policy=AllowSingleLegPolicy(),
    )


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _shadow_evidence(
    *,
    plan: ExecutionPlan,
    position_legs: tuple[PositionLeg, ...],
    request: PortfolioRiskRequest,
    risk: Any,
    outcome: Any,
    startup_state: str,
    final_state: str,
    venue_writes: int,
) -> dict[str, object]:
    leg = plan.legs[0]
    position = position_legs[0]
    order = outcome.order

    requested = order.requested_quantity
    filled = order.filled_quantity
    fill_ratio = (
        Decimal("0")
        if requested == 0
        else filled / requested
    )

    return {
        "signals_intents": {
            "strategy": plan.strategy,
            "strategy_version": plan.strategy_version,
            "source": plan.source,
            "shape": plan.shape.value,
            "intent_semantics": {
                "instrument": str(leg.instrument_id),
                "side": leg.side.value,
                "quantity": _decimal_text(leg.quantity),
                "reduce_only": leg.reduce_only,
            },
            "strategy_signal_observed": False,
            "signal_note": (
                "Phase14 deterministic candidate constructs canonical intent "
                "semantics directly; no StrategyRuntime signal is claimed"
            ),
        },
        "risk_decisions": {
            "decision": risk.state.value,
            "shape": request.shape.value,
            "strategy": request.strategy,
            "observation_state": "CURRENT",
            "leg_count": len(request.legs),
            "reasons": [str(item) for item in risk.reasons],
        },
        "order_intent": {
            "instrument": str(order.instrument_id),
            "side": order.side.value,
            "order_type": order.order_type.value,
            "requested_quantity": _decimal_text(order.requested_quantity),
            "limit_price": (
                None
                if order.limit_price is None
                else _decimal_text(order.limit_price)
            ),
            "reduce_only": order.reduce_only,
        },
        "positions": {
            "instrument": str(position.instrument_id),
            "side": position.side.value,
            "target_quantity": _decimal_text(position.target_quantity),
            "filled_quantity": _decimal_text(position.filled_quantity),
            "current_quantity": _decimal_text(position.current_quantity),
            "status": position.status.value,
        },
        "fills_reconciliation": {
            "filled_quantity": _decimal_text(filled),
            "fill_count": 0,
            "startup_reconciliation": startup_state,
            "post_execution_reconciliation": final_state,
        },
        "pnl_attribution": {
            "realized_pnl": "0",
            "unrealized_pnl": "0",
            "fees": "0",
            "funding": "0",
            "net_pnl": "0",
            "attribution_state": "NO_FILL",
        },
        "execution_quality": {
            "order_status": order.status.value,
            "requested_quantity": _decimal_text(requested),
            "filled_quantity": _decimal_text(filled),
            "fill_ratio": _decimal_text(fill_ratio),
            "average_fill_price": (
                None
                if order.average_fill_price is None
                else _decimal_text(order.average_fill_price)
            ),
            "slippage_bps": None,
            "simulated_submit_count": venue_writes,
            "real_exchange_writes": 0,
        },
        "failures_stale_states": {
            "candidate_status": "RUNNING",
            "risk_observation_state": "CURRENT",
            "reconciliation_source_state": "CURRENT",
            "requires_recovery": outcome.requires_recovery,
            "rejection_reason": order.rejection_reason,
            "errors": [],
        },
    }

def _graph(
    run_id: str,
) -> tuple[
    ExecutionPlan,
    PositionGroup,
    tuple[PositionLeg, ...],
    ExecutionOrder,
]:
    leg_id = f"{run_id}-leg"
    order_id = OrderId(f"{run_id}-order")
    client_order_id = ClientOrderId(f"{run_id}-client")

    planned_leg = ExecutionLegPlan(
        leg_id=leg_id,
        order_id=order_id,
        client_order_id=client_order_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=TradeSide.BUY,
        quantity=Decimal("0.001"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
        reduce_only=False,
    )

    plan = ExecutionPlan(
        plan_id=f"{run_id}-plan",
        intent_id=f"{run_id}-intent",
        user_id=USER_ID,
        shape=TradeIntentShape.SINGLE_LEG,
        strategy="phase14-postgres-shadow",
        strategy_version="1",
        source="PHASE14_SHADOW",
        legs=(planned_leg,),
        created_at=NOW,
    )

    group = PositionGroup(
        group_id=f"{run_id}-group",
        plan_id=plan.plan_id,
        user_id=USER_ID,
        shape=plan.shape,
        strategy=plan.strategy,
        strategy_version=plan.strategy_version,
        trade_source=plan.source,
        status=PositionGroupStatus.PENDING,
        opened_at=None,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    position_leg = PositionLeg(
        group_id=group.group_id,
        leg_id=leg_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        side=TradeSide.BUY,
        target_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
        current_quantity=Decimal("0"),
        average_entry_price=None,
        average_exit_price=None,
        status=PositionLegStatus.PENDING,
        opened_at=None,
        closed_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    order = ExecutionOrder(
        order_id=order_id,
        plan_id=plan.plan_id,
        group_id=group.group_id,
        leg_id=leg_id,
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=client_order_id,
        venue_order_id=None,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=Decimal("100"),
        reduce_only=False,
        status=ExecutionOrderStatus.PENDING,
        rejection_reason=None,
        submitted_at=None,
        accepted_at=None,
        filled_at=None,
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )

    return plan, group, (position_leg,), order


async def run() -> dict[str, object]:
    database_url = _required_env("NEXUS_V2_DATABASE_URL")
    run_id = _run_id()

    engine = create_persistence_engine(database_url)
    factory = create_session_factory(engine)

    try:
        plan, group, position_legs, initial_order = _graph(
            run_id
        )

        snapshot_provider = (
            SqlAlchemyLocalReconciliationSnapshotProvider(factory)
        )

        existing_snapshot = await snapshot_provider.load(
            user_id=USER_ID,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )

        matching_orders = tuple(
            order
            for order in existing_snapshot.orders
            if order.order_id == initial_order.order_id
        )

        if len(matching_orders) > 1:
            raise RuntimeError(
                "duplicate canonical execution order detected"
            )

        root_seeded = not matching_orders

        if root_seeded:
            await CoreExecutionPersistenceService(
                factory
            ).persist_root(
                plan=plan,
                group=group,
                position_legs=position_legs,
                order=initial_order,
                recorded_at=NOW,
            )
            order = initial_order
        else:
            order = matching_orders[0]

        evidence = RecordingEvidencePort()
        reconciliation = ReconciliationPassOrchestrator(
            evidence
        )

        startup = await StartupReconciliationActivationGate(
            reconciliation
        ).evaluate(
            (
                StartupReconciliationInput(
                    user_id=USER_ID,
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    source_state=ReconciliationSourceState.CURRENT,
                    observed_at=NOW,
                ),
            )
        )

        if not startup.strategy_execution_allowed:
            raise RuntimeError(
                "startup reconciliation blocked execution"
            )

        request = PortfolioRiskRequest(
            intent_id=plan.intent_id,
            user_id=USER_ID,
            shape=TradeIntentShape.SINGLE_LEG,
            strategy=plan.strategy,
            legs=(
                RiskLegCandidate(
                    leg_id=position_legs[0].leg_id,
                    account_id=ACCOUNT,
                    instrument_id=INSTRUMENT,
                    side=TradeSide.BUY,
                    quantity=Decimal("0.001"),
                    reduce_only=False,
                    mark_price=Decimal("100"),
                    settlement_currency="USDT",
                    correlation_cluster="CRYPTO-MAJOR",
                    available_liquidity_notional=Decimal(
                        "100000"
                    ),
                    expected_slippage_bps=Decimal("1"),
                    leverage=Decimal("1"),
                ),
            ),
        )

        risk_snapshot = PortfolioRiskSnapshot(
            user_id=USER_ID,
            observation_state=RiskObservationState.CURRENT,
            trading_state=PortfolioRiskState.ACTIVE,
            equity=Decimal("10000"),
            daily_start_equity=Decimal("10000"),
            rolling_peak_equity=Decimal("10000"),
            exposures=(),
            observed_at=NOW,
        )

        risk = _risk_engine().evaluate(
            request=request,
            snapshot=risk_snapshot,
        )

        if (
            risk.state
            is not PortfolioRiskDecisionState.APPROVED
        ):
            raise RuntimeError(
                f"risk blocked execution: {risk.reasons}"
            )

        observation_store = (
            SqlAlchemyPhase14SimulatedVenueObservationStore(
                factory
            )
        )

        venue = Phase14PersistentSimulatedVenue(
            store=observation_store,
            user_id=USER_ID,
        )

        coordinator = SingleLegExecutionCoordinator(
            user_id=USER_ID,
            venue=venue,
            state_store=SqlAlchemyExecutionCoordinatorStateStore(
                factory
            ),
        )

        outcome = await coordinator.execute(
            order,
            now=NOW,
        )

        if outcome.venue_result is None:
            raise RuntimeError(
                "execution/recovery produced no venue evidence"
            )

        # Persist the materialized local lifecycle after execution/recovery.
        await CoreExecutionPersistenceService(
            factory
        ).persist_root(
            plan=plan,
            group=group,
            position_legs=position_legs,
            order=outcome.order,
            recorded_at=NOW,
        )

        final = await reconciliation.run(
            user_id=USER_ID,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=NOW,
            local_orders=(outcome.order,),
            venue_orders=(outcome.venue_result,),
            local_fills=(),
            venue_fills=(),
            local_positions=(),
            venue_positions=(),
        )

        if final.state is not ReconciliationResultState.MATCHED:
            raise RuntimeError(
                "post-execution reconciliation failed"
            )

        shadow_evidence = _shadow_evidence(
            plan=plan,
            position_legs=position_legs,
            request=request,
            risk=risk,
            outcome=outcome,
            startup_state="MATCHED",
            final_state=final.state.value,
            venue_writes=len(venue.submitted),
        )

        return {
            "service": "nexus-v2-core",
            "mode": "PHASE14_POSTGRES_SIMULATION_ONLY",
            "startup_reconciliation": "MATCHED",
            "strategy_execution_allowed": True,
            "portfolio_risk": risk.state.value,
            "execution_state": outcome.state.value,
            "order_status": outcome.order.status.value,
            "post_execution_reconciliation": final.state.value,
            "venue_writes": len(venue.submitted),
            "real_exchange_writes": 0,
            "production_authority": False,
            "database_persistence": True,
            "root_seeded": root_seeded,
            "coordinator_idempotent": outcome.idempotent,
            "requires_recovery": outcome.requires_recovery,
            "run_id": run_id,
            "status": "RUNNING",
            "shadow_evidence": shadow_evidence,
        }
    finally:
        await engine.dispose()
