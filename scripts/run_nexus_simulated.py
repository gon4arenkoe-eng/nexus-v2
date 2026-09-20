"""Executable fail-closed NEXUS V2 simulated Core runtime smoke."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

from apps.core.application.execution_coordinator import SingleLegExecutionCoordinator
from apps.core.application.portfolio_risk import PortfolioRiskEngine
from apps.core.application.reconciliation_orchestrator import ReconciliationPassOrchestrator
from apps.core.application.startup_reconciliation import StartupReconciliationActivationGate, StartupReconciliationInput
from apps.core.domain.execution_orders import ExecutionOrder, ExecutionOrderStatus
from apps.core.domain.intents import TradeIntentShape, TradeSide
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.domain.portfolio_risk import PortfolioRiskDecisionState, PortfolioRiskLimits, PortfolioRiskRequest, PortfolioRiskSnapshot, PortfolioRiskState, RiskLegCandidate, RiskObservationState
from apps.core.domain.reconciliation import ReconciliationResult, ReconciliationResultState, ReconciliationSourceState
from apps.core.ports.execution_coordinator import ExecutionCoordinatorStateRecord
from apps.core.ports.portfolio_risk import SingleLegRiskDecision
from apps.core.ports.venue import VenueCapabilities, VenueOrderRequest, VenueOrderResult, VenueOrderState
from packages.contracts.identities import AccountId, AssetClass, ClientOrderId, InstrumentId, InstrumentType, OrderId, VenueId, VenueOrderId

NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
USER_ID = 1
VENUE = VenueId("SIM")
ACCOUNT = AccountId(VENUE, 1)
INSTRUMENT = InstrumentId(VENUE, "BTCUSDT", InstrumentType.PERPETUAL, AssetClass.CRYPTO)

class MemoryStateStore:
    def __init__(self) -> None:
        self.records: dict[tuple[int, str], ExecutionCoordinatorStateRecord] = {}
    async def load(self, *, user_id: int, order_id: OrderId):
        return self.records.get((user_id, str(order_id)))
    async def checkpoint(self, record: ExecutionCoordinatorStateRecord) -> None:
        self.records[(record.user_id, str(record.order_id))] = record

class RecordingEvidencePort:
    def __init__(self) -> None:
        self.results: list[ReconciliationResult] = []
    async def persist_result(self, result: ReconciliationResult) -> None:
        self.results.append(result)

class AllowSingleLegPolicy:
    def evaluate(self, *, candidate, portfolio):
        return SingleLegRiskDecision(approved=True)

class SimulatedVenue:
    def __init__(self) -> None:
        self.result: VenueOrderResult | None = None
        self.submitted: list[VenueOrderRequest] = []
    @property
    def capabilities(self) -> VenueCapabilities:
        return VenueCapabilities(frozenset())
    async def submit_order(self, request: VenueOrderRequest) -> VenueOrderResult:
        self.submitted.append(request)
        self.result = VenueOrderResult(client_order_id=request.client_order_id, venue_order_id=VenueOrderId("sim-order-1"), state=VenueOrderState.ACCEPTED, requested_quantity=request.quantity, filled_quantity=Decimal("0"))
        return self.result
    async def cancel_order(self, *, account_id, instrument_id, venue_order_id):
        raise RuntimeError("simulation runtime does not cancel")
    async def get_order(self, *, account_id, instrument_id, venue_order_id):
        if self.result is None:
            raise RuntimeError("order not submitted")
        return self.result
    async def get_open_orders(self, *, account_id, instrument_id=None):
        return () if self.result is None else (self.result,)
    async def get_positions(self, *, account_id): return ()
    async def get_account_state(self, *, account_id): raise RuntimeError("not required")
    async def get_fills(self, *, account_id, instrument_id=None, since=None): return ()

def risk_engine() -> PortfolioRiskEngine:
    return PortfolioRiskEngine(limits=PortfolioRiskLimits(max_open_position_groups=10, max_gross_exposure=Decimal("20000"), max_net_exposure=Decimal("15000"), max_account_exposure=Decimal("10000"), max_venue_exposure=Decimal("15000"), max_strategy_exposure=Decimal("10000"), max_instrument_exposure=Decimal("6000"), max_currency_concentration=Decimal("1"), max_correlation_cluster_exposure=Decimal("12000"), max_leverage=Decimal("5"), max_margin_utilization=Decimal("0.8"), max_daily_drawdown=Decimal("0.05"), max_rolling_drawdown=Decimal("0.10"), max_order_liquidity_ratio=Decimal("0.10"), max_expected_slippage_bps=Decimal("25"), hedge_tolerance=Decimal("0.05")), single_leg_policy=AllowSingleLegPolicy())

def make_order() -> ExecutionOrder:
    return ExecutionOrder(order_id=OrderId("runtime-order-1"), plan_id="runtime-plan-1", group_id="runtime-group-1", leg_id="runtime-leg-1", account_id=ACCOUNT, instrument_id=INSTRUMENT, client_order_id=ClientOrderId("runtime-client-1"), venue_order_id=None, side=OrderSide.BUY, order_type=OrderType.LIMIT, requested_quantity=Decimal("0.001"), filled_quantity=Decimal("0"), average_fill_price=None, limit_price=Decimal("100"), reduce_only=False, status=ExecutionOrderStatus.PENDING, rejection_reason=None, submitted_at=None, accepted_at=None, filled_at=None, cancelled_at=None, created_at=NOW, updated_at=NOW)

async def run() -> dict[str, object]:
    venue = SimulatedVenue(); evidence = RecordingEvidencePort(); reconciliation = ReconciliationPassOrchestrator(evidence)
    startup = await StartupReconciliationActivationGate(reconciliation).evaluate((StartupReconciliationInput(user_id=USER_ID, account_id=ACCOUNT, instrument_id=INSTRUMENT, source_state=ReconciliationSourceState.CURRENT, observed_at=NOW),))
    if not startup.strategy_execution_allowed: raise RuntimeError("startup reconciliation blocked execution")
    request = PortfolioRiskRequest(intent_id="runtime-intent-1", user_id=USER_ID, shape=TradeIntentShape.SINGLE_LEG, strategy="runtime-smoke", legs=(RiskLegCandidate(leg_id="runtime-leg-1", account_id=ACCOUNT, instrument_id=INSTRUMENT, side=TradeSide.BUY, quantity=Decimal("0.001"), reduce_only=False, mark_price=Decimal("100"), settlement_currency="USDT", correlation_cluster="CRYPTO-MAJOR", available_liquidity_notional=Decimal("100000"), expected_slippage_bps=Decimal("1"), leverage=Decimal("1")),))
    snapshot = PortfolioRiskSnapshot(user_id=USER_ID, observation_state=RiskObservationState.CURRENT, trading_state=PortfolioRiskState.ACTIVE, equity=Decimal("10000"), daily_start_equity=Decimal("10000"), rolling_peak_equity=Decimal("10000"), exposures=(), observed_at=NOW)
    risk = risk_engine().evaluate(request=request, snapshot=snapshot)
    if risk.state is not PortfolioRiskDecisionState.APPROVED: raise RuntimeError(f"risk blocked execution: {risk.reasons}")
    outcome = await SingleLegExecutionCoordinator(user_id=USER_ID, venue=venue, state_store=MemoryStateStore()).execute(make_order(), now=NOW)
    if outcome.venue_result is None: raise RuntimeError("execution produced no venue evidence")
    final = await reconciliation.run(user_id=USER_ID, account_id=ACCOUNT, instrument_id=INSTRUMENT, source_state=ReconciliationSourceState.CURRENT, observed_at=NOW, local_orders=(outcome.order,), venue_orders=(outcome.venue_result,), local_fills=(), venue_fills=(), local_positions=(), venue_positions=())
    if final.state is not ReconciliationResultState.MATCHED: raise RuntimeError("post-execution reconciliation failed")
    return {"service":"nexus-v2-core","mode":"SIMULATION_ONLY","startup_reconciliation":"MATCHED","strategy_execution_allowed":True,"portfolio_risk":risk.state.value,"execution_state":outcome.state.value,"order_status":outcome.order.status.value,"post_execution_reconciliation":final.state.value,"venue_writes":len(venue.submitted),"real_exchange_writes":0,"production_authority":False,"status":"RUNNING"}

def main() -> None:
    print(json.dumps(asyncio.run(run()), sort_keys=True))

if __name__ == "__main__": main()
