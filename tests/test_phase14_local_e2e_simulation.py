"""Phase 14A deterministic local E2E simulation readiness."""

from __future__ import annotations

import asyncio
import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from enum import StrEnum

from apps.core.application.execution_coordinator import SingleLegExecutionCoordinator
from apps.core.application.reconciliation_orchestrator import ReconciliationPassOrchestrator
from apps.core.domain.execution_orders import ExecutionOrder, ExecutionOrderStatus
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.domain.reconciliation import (
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
)
from apps.core.ports.execution_coordinator import ExecutionCoordinatorStateRecord
from apps.core.ports.venue import (
    VenueOrderRequest,
    VenueOrderResult,
    VenueOrderState,
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

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
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

class SimulatedVenue:
    def __init__(self) -> None:
        self.result: VenueOrderResult | None = None
        self.submitted: list[VenueOrderRequest] = []

    @property
    def capabilities(self):
        return frozenset()

    async def submit_order(self, request: VenueOrderRequest) -> VenueOrderResult:
        self.submitted.append(request)
        self.result = VenueOrderResult(
            client_order_id=request.client_order_id,
            venue_order_id=VenueOrderId("sim-order-1"),
            state=VenueOrderState.ACCEPTED,
            requested_quantity=request.quantity,
            filled_quantity=Decimal("0"),
        )
        return self.result

    async def cancel_order(self, *, account_id, instrument_id, venue_order_id):
        raise AssertionError("cancel is not part of this Phase14A slice")

    async def get_order(self, *, account_id, instrument_id, venue_order_id):
        if self.result is None:
            raise RuntimeError("order not submitted")
        return self.result

    async def get_open_orders(self, *, account_id, instrument_id=None):
        return () if self.result is None else (self.result,)

    async def get_positions(self, *, account_id):
        return ()

    async def get_account_state(self, *, account_id):
        raise AssertionError("account observation is outside this slice")

    async def get_fills(self, *, account_id, instrument_id=None, since=None):
        return ()

def make_order() -> ExecutionOrder:
    return ExecutionOrder(
        order_id=OrderId("phase14-order-1"),
        plan_id="phase14-plan-1",
        group_id="phase14-group-1",
        leg_id="phase14-leg-1",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=ClientOrderId("phase14-client-1"),
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

@dataclass(frozen=True, slots=True)
class ShadowComparisonEvidence:
    order_status: str
    reconciliation_state: str
    discrepancy_count: int

    def fingerprint(self) -> str:
        payload = {
            "discrepancy_count": self.discrepancy_count,
            "order_status": self.order_status,
            "reconciliation_state": self.reconciliation_state,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

def _comparison_evidence(*, order_status: ExecutionOrderStatus, result: ReconciliationResult) -> ShadowComparisonEvidence:
    return ShadowComparisonEvidence(
        order_status=order_status.value,
        reconciliation_state=result.state.value,
        discrepancy_count=len(result.discrepancies),
    )

class ShadowParityState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_COMPARABLE = "NOT_COMPARABLE"

@dataclass(frozen=True, slots=True)
class ShadowParityResult:
    state: ShadowParityState
    mismatches: tuple[str, ...]

def compare_shadow_evidence(
    baseline: ShadowComparisonEvidence,
    candidate: ShadowComparisonEvidence,
) -> ShadowParityResult:
    non_comparable_states = {
        ReconciliationResultState.STALE.value,
    }
    if (
        baseline.reconciliation_state in non_comparable_states
        or candidate.reconciliation_state in non_comparable_states
    ):
        return ShadowParityResult(ShadowParityState.NOT_COMPARABLE, ())

    mismatches = tuple(
        field
        for field in (
            "order_status",
            "reconciliation_state",
            "discrepancy_count",
        )
        if getattr(baseline, field) != getattr(candidate, field)
    )
    return ShadowParityResult(
        ShadowParityState.FAIL if mismatches else ShadowParityState.PASS,
        mismatches,
    )

def test_local_execution_to_reconciliation_is_deterministic_and_matched() -> None:
    async def scenario() -> tuple[ReconciliationResult, RecordingEvidencePort]:
        venue = SimulatedVenue()
        coordinator = SingleLegExecutionCoordinator(user_id=1, venue=venue, state_store=MemoryStateStore())
        outcome = await coordinator.execute(make_order(), now=NOW)
        assert outcome.order.status is ExecutionOrderStatus.ACCEPTED
        assert outcome.venue_result is not None
        assert venue.submitted
        evidence = RecordingEvidencePort()
        runner = ReconciliationPassOrchestrator(evidence)
        result = await runner.run(
            user_id=1, account_id=ACCOUNT, instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.CURRENT, observed_at=NOW,
            local_orders=(outcome.order,), venue_orders=(outcome.venue_result,),
            local_fills=(), venue_fills=(), local_positions=(), venue_positions=(),
        )
        return result, evidence
    first, first_evidence = asyncio.run(scenario())
    second, second_evidence = asyncio.run(scenario())
    assert first.state is ReconciliationResultState.MATCHED
    assert first.discrepancies == ()
    assert second == first
    assert first_evidence.results == [first]
    assert second_evidence.results == [second]

def test_local_reconciliation_stale_source_fails_closed_deterministically() -> None:
    async def scenario() -> ReconciliationResult:
        evidence = RecordingEvidencePort()
        runner = ReconciliationPassOrchestrator(evidence)
        result = await runner.run(
            user_id=1, account_id=ACCOUNT, instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.STALE, observed_at=NOW,
            local_orders=(), venue_orders=(), local_fills=(), venue_fills=(),
            local_positions=(), venue_positions=(),
        )
        assert evidence.results == [result]
        return result
    first = asyncio.run(scenario())
    second = asyncio.run(scenario())
    assert first.state is ReconciliationResultState.STALE
    assert second == first
    assert first.discrepancies

def test_execution_restart_does_not_duplicate_submit_with_persisted_coordinator_state() -> None:
    async def scenario():
        venue = SimulatedVenue()
        store = MemoryStateStore()
        first = SingleLegExecutionCoordinator(user_id=1, venue=venue, state_store=store)
        order = make_order()
        first_outcome = await first.execute(order, now=NOW)
        restarted = SingleLegExecutionCoordinator(user_id=1, venue=venue, state_store=store)
        second_outcome = await restarted.execute(order, now=NOW)
        return venue, first_outcome, second_outcome
    venue, first, second = asyncio.run(scenario())
    assert len(venue.submitted) == 1
    assert first.order.status is ExecutionOrderStatus.ACCEPTED
    assert second.order.order_id == first.order.order_id

def test_shadow_comparison_fingerprint_is_deterministic() -> None:
    async def scenario() -> tuple[ExecutionOrderStatus, ReconciliationResult]:
        venue = SimulatedVenue()
        coordinator = SingleLegExecutionCoordinator(user_id=1, venue=venue, state_store=MemoryStateStore())
        outcome = await coordinator.execute(make_order(), now=NOW)
        evidence = RecordingEvidencePort()
        result = await ReconciliationPassOrchestrator(evidence).run(
            user_id=1, account_id=ACCOUNT, instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.CURRENT, observed_at=NOW,
            local_orders=(outcome.order,), venue_orders=(outcome.venue_result,),
            local_fills=(), venue_fills=(), local_positions=(), venue_positions=(),
        )
        return outcome.order.status, result
    first_status, first_result = asyncio.run(scenario())
    second_status, second_result = asyncio.run(scenario())
    first = _comparison_evidence(order_status=first_status, result=first_result)
    second = _comparison_evidence(order_status=second_status, result=second_result)
    assert first == second
    assert first.fingerprint() == second.fingerprint()
    assert len(first.fingerprint()) == 64

def test_stale_shadow_evidence_is_distinct_and_repeatable() -> None:
    async def stale_result() -> ReconciliationResult:
        evidence = RecordingEvidencePort()
        return await ReconciliationPassOrchestrator(evidence).run(
            user_id=1, account_id=ACCOUNT, instrument_id=INSTRUMENT,
            source_state=ReconciliationSourceState.STALE, observed_at=NOW,
            local_orders=(), venue_orders=(), local_fills=(), venue_fills=(),
            local_positions=(), venue_positions=(),
        )
    first = asyncio.run(stale_result())
    second = asyncio.run(stale_result())
    first_evidence = _comparison_evidence(order_status=ExecutionOrderStatus.UNKNOWN, result=first)
    second_evidence = _comparison_evidence(order_status=ExecutionOrderStatus.UNKNOWN, result=second)
    assert first_evidence == second_evidence
    assert first_evidence.fingerprint() == second_evidence.fingerprint()
    assert first_evidence.reconciliation_state == ReconciliationResultState.STALE.value
    assert first_evidence.discrepancy_count > 0


def test_shadow_current_and_stale_fingerprints_are_distinct() -> None:
    current = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    stale = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.UNKNOWN.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )

    assert current.fingerprint() != stale.fingerprint()


def _import_roots() -> frozenset[str]:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return frozenset(roots)


def test_phase14a_local_slice_has_no_external_network_authority() -> None:
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
    }
    assert _import_roots().isdisjoint(forbidden_import_roots)

class RecoveryAfterSubmitTimeoutVenue(SimulatedVenue):
    """Simulate an ambiguous submit where the venue accepted the order before timeout."""

    def __init__(self) -> None:
        super().__init__()
        self.submit_attempts = 0
        self.open_order_queries = 0
        self.accepted_after_timeout = VenueOrderResult(
            client_order_id=ClientOrderId("phase14-client-1"),
            venue_order_id=VenueOrderId("sim-recovery-order-1"),
            state=VenueOrderState.ACCEPTED,
            requested_quantity=Decimal("0.001"),
            filled_quantity=Decimal("0"),
        )

    async def submit_order(self, request: VenueOrderRequest) -> VenueOrderResult:
        self.submit_attempts += 1
        self.submitted.append(request)
        if self.submit_attempts == 1:
            self.result = self.accepted_after_timeout
            raise TimeoutError("simulated submit acknowledgement timeout")
        raise AssertionError("unsafe duplicate submit attempted during recovery")

    async def get_open_orders(self, *, account_id, instrument_id=None):
        self.open_order_queries += 1
        return (self.accepted_after_timeout,)


class UnresolvedSubmitTimeoutVenue(RecoveryAfterSubmitTimeoutVenue):
    """Simulate an ambiguous submit that remains absent from venue observations."""

    async def get_open_orders(self, *, account_id, instrument_id=None):
        self.open_order_queries += 1
        return ()


def test_submit_timeout_restart_recovers_known_venue_order_without_duplicate_submit() -> None:
    async def scenario():
        venue = RecoveryAfterSubmitTimeoutVenue()
        store = MemoryStateStore()
        order = make_order()

        first = SingleLegExecutionCoordinator(
            user_id=1,
            venue=venue,
            state_store=store,
        )
        ambiguous = await first.execute(order, now=NOW)

        assert ambiguous.requires_recovery is True
        assert ambiguous.order.status is ExecutionOrderStatus.UNKNOWN
        assert venue.submit_attempts == 1

        restarted = SingleLegExecutionCoordinator(
            user_id=1,
            venue=venue,
            state_store=store,
        )
        recovered = await restarted.recover(order, now=NOW)
        return venue, ambiguous, recovered

    venue, ambiguous, recovered = asyncio.run(scenario())

    assert ambiguous.requires_recovery is True
    assert recovered.requires_recovery is False
    assert recovered.order.status is ExecutionOrderStatus.ACCEPTED
    assert recovered.order.venue_order_id == VenueOrderId("sim-recovery-order-1")
    assert venue.submit_attempts == 1
    assert venue.open_order_queries >= 1


def test_submit_timeout_unresolved_recovery_remains_fail_closed_and_repeatable() -> None:
    async def scenario():
        venue = UnresolvedSubmitTimeoutVenue()
        store = MemoryStateStore()
        order = make_order()

        first = SingleLegExecutionCoordinator(
            user_id=1,
            venue=venue,
            state_store=store,
        )
        ambiguous = await first.execute(order, now=NOW)

        restarted = SingleLegExecutionCoordinator(
            user_id=1,
            venue=venue,
            state_store=store,
        )
        unresolved = await restarted.recover(order, now=NOW)
        return venue, ambiguous, unresolved

    first_venue, first_ambiguous, first_unresolved = asyncio.run(scenario())
    second_venue, second_ambiguous, second_unresolved = asyncio.run(scenario())

    assert first_ambiguous.requires_recovery is True
    assert second_ambiguous.requires_recovery is True
    assert first_unresolved.requires_recovery is True
    assert second_unresolved.requires_recovery is True
    assert first_unresolved.order.status is ExecutionOrderStatus.UNKNOWN
    assert second_unresolved.order.status is ExecutionOrderStatus.UNKNOWN
    assert first_venue.submit_attempts == 1
    assert second_venue.submit_attempts == 1
    assert first_venue.open_order_queries >= 1
    assert second_venue.open_order_queries >= 1

    first_evidence = ShadowComparisonEvidence(
        order_status=first_unresolved.order.status.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )
    second_evidence = ShadowComparisonEvidence(
        order_status=second_unresolved.order.status.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )

    assert first_evidence == second_evidence
    assert first_evidence.fingerprint() == second_evidence.fingerprint()


def test_shadow_parity_identical_current_evidence_passes() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    result = compare_shadow_evidence(baseline, baseline)
    assert result.state is ShadowParityState.PASS
    assert result.mismatches == ()

def test_shadow_parity_classifies_deterministic_mismatches() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.UNKNOWN.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=1,
    )
    first = compare_shadow_evidence(baseline, candidate)
    second = compare_shadow_evidence(baseline, candidate)
    assert first == second
    assert first.state is ShadowParityState.FAIL
    assert first.mismatches == ("order_status", "discrepancy_count")

def test_shadow_parity_stale_input_is_not_comparable() -> None:
    current = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    stale = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.UNKNOWN.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )
    forward = compare_shadow_evidence(current, stale)
    reverse = compare_shadow_evidence(stale, current)
    assert forward.state is ShadowParityState.NOT_COMPARABLE
    assert reverse.state is ShadowParityState.NOT_COMPARABLE
    assert forward.mismatches == reverse.mismatches == ()

def test_recovery_simulation_never_introduces_exchange_or_secret_access() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert "environ" not in names
    assert "getenv" not in names
    assert "subprocess" not in _import_roots()

class ShadowAuthorityViolation(RuntimeError):
    """Raised when shadow-only code attempts to cross a venue write boundary."""


class ShadowVenueGuard:
    """Read-only VenueAdapter facade for Phase 14 shadow simulation.

    The wrapped venue may support writes, but the shadow facade never forwards
    submit/cancel calls. Read observations remain available for comparison.
    """

    def __init__(self, delegate: SimulatedVenue) -> None:
        self._delegate = delegate
        self.blocked_write_attempts = 0

    @property
    def capabilities(self):
        return self._delegate.capabilities

    async def submit_order(self, request: VenueOrderRequest) -> VenueOrderResult:
        self.blocked_write_attempts += 1
        raise ShadowAuthorityViolation("shadow mode blocks venue order submission")

    async def cancel_order(self, *, account_id, instrument_id, venue_order_id):
        self.blocked_write_attempts += 1
        raise ShadowAuthorityViolation("shadow mode blocks venue order cancellation")

    async def get_order(self, *, account_id, instrument_id, venue_order_id):
        return await self._delegate.get_order(
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=venue_order_id,
        )

    async def get_open_orders(self, *, account_id, instrument_id=None):
        return await self._delegate.get_open_orders(
            account_id=account_id,
            instrument_id=instrument_id,
        )

    async def get_positions(self, *, account_id):
        return await self._delegate.get_positions(account_id=account_id)

    async def get_account_state(self, *, account_id):
        return await self._delegate.get_account_state(account_id=account_id)

    async def get_fills(self, *, account_id, instrument_id=None, since=None):
        return await self._delegate.get_fills(
            account_id=account_id,
            instrument_id=instrument_id,
            since=since,
        )


def test_shadow_guard_allows_observation_without_write_authority() -> None:
    async def scenario():
        delegate = SimulatedVenue()
        delegate.result = VenueOrderResult(
            client_order_id=ClientOrderId("phase14-client-1"),
            venue_order_id=VenueOrderId("sim-shadow-observed-1"),
            state=VenueOrderState.ACCEPTED,
            requested_quantity=Decimal("0.001"),
            filled_quantity=Decimal("0"),
        )
        shadow = ShadowVenueGuard(delegate)
        observed = await shadow.get_open_orders(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
        return delegate, shadow, observed

    delegate, shadow, observed = asyncio.run(scenario())
    assert len(observed) == 1
    assert observed[0].venue_order_id == VenueOrderId("sim-shadow-observed-1")
    assert delegate.submitted == []
    assert shadow.blocked_write_attempts == 0


def test_shadow_guard_blocks_submit_before_delegate_write_boundary() -> None:
    async def scenario():
        delegate = SimulatedVenue()
        shadow = ShadowVenueGuard(delegate)
        request_source = SimulatedVenue()
        request_coordinator = SingleLegExecutionCoordinator(
            user_id=1,
            venue=request_source,
            state_store=MemoryStateStore(),
        )
        await request_coordinator.execute(make_order(), now=NOW)
        request = request_source.submitted[0]
        try:
            await shadow.submit_order(request)
        except ShadowAuthorityViolation as exc:
            return delegate, shadow, str(exc)
        raise AssertionError("shadow submit unexpectedly crossed the write boundary")

    delegate, shadow, message = asyncio.run(scenario())
    assert "blocks venue order submission" in message
    assert shadow.blocked_write_attempts == 1
    assert delegate.submitted == []
    assert delegate.result is None


def test_shadow_guard_blocks_cancel_before_delegate_write_boundary() -> None:
    class CancelRecordingVenue(SimulatedVenue):
        def __init__(self) -> None:
            super().__init__()
            self.cancel_calls = 0

        async def cancel_order(self, *, account_id, instrument_id, venue_order_id):
            self.cancel_calls += 1
            raise AssertionError("delegate cancel must never execute in shadow mode")

    async def scenario():
        delegate = CancelRecordingVenue()
        shadow = ShadowVenueGuard(delegate)
        try:
            await shadow.cancel_order(
                account_id=ACCOUNT,
                instrument_id=INSTRUMENT,
                venue_order_id=VenueOrderId("sim-shadow-cancel-blocked"),
            )
        except ShadowAuthorityViolation as exc:
            return delegate, shadow, str(exc)
        raise AssertionError("shadow cancel unexpectedly crossed the write boundary")

    delegate, shadow, message = asyncio.run(scenario())
    assert "blocks venue order cancellation" in message
    assert shadow.blocked_write_attempts == 1
    assert delegate.cancel_calls == 0


def test_shadow_comparison_can_run_without_execution_authority() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    result = compare_shadow_evidence(baseline, candidate)
    assert result.state is ShadowParityState.PASS
    assert result.mismatches == ()


class ShadowMismatchSeverity(StrEnum):
    NON_CRITICAL = "NON_CRITICAL"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class ClassifiedShadowMismatch:
    field: str
    severity: ShadowMismatchSeverity


@dataclass(frozen=True, slots=True)
class ShadowGateDecision:
    state: ShadowParityState
    mismatches: tuple[ClassifiedShadowMismatch, ...]
    gate_open: bool


_CRITICAL_SHADOW_FIELDS = frozenset(
    {
        "order_status",
        "reconciliation_state",
        "discrepancy_count",
    }
)


def classify_shadow_mismatches(
    result: ShadowParityResult,
) -> ShadowGateDecision:
    if result.state is ShadowParityState.NOT_COMPARABLE:
        return ShadowGateDecision(
            state=ShadowParityState.NOT_COMPARABLE,
            mismatches=(),
            gate_open=False,
        )

    classified = tuple(
        ClassifiedShadowMismatch(
            field=field,
            severity=(
                ShadowMismatchSeverity.CRITICAL
                if field in _CRITICAL_SHADOW_FIELDS
                else ShadowMismatchSeverity.NON_CRITICAL
            ),
        )
        for field in result.mismatches
    )
    has_critical = any(
        item.severity is ShadowMismatchSeverity.CRITICAL
        for item in classified
    )
    return ShadowGateDecision(
        state=result.state,
        mismatches=classified,
        gate_open=(
            result.state is ShadowParityState.PASS
            and not has_critical
        ),
    )


def test_shadow_gate_opens_only_for_comparable_pass() -> None:
    evidence = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    decision = classify_shadow_mismatches(
        compare_shadow_evidence(evidence, evidence)
    )
    assert decision.state is ShadowParityState.PASS
    assert decision.mismatches == ()
    assert decision.gate_open is True


def test_shadow_gate_fails_closed_on_execution_divergence() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.CANCELLED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    decision = classify_shadow_mismatches(
        compare_shadow_evidence(baseline, candidate)
    )
    assert decision.state is ShadowParityState.FAIL
    assert decision.gate_open is False
    assert decision.mismatches == (
        ClassifiedShadowMismatch(
            field="order_status",
            severity=ShadowMismatchSeverity.CRITICAL,
        ),
    )


def test_shadow_gate_fails_closed_on_reconciliation_divergence() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state="DIVERGENT",
        discrepancy_count=1,
    )
    decision = classify_shadow_mismatches(
        compare_shadow_evidence(baseline, candidate)
    )
    assert decision.state is ShadowParityState.FAIL
    assert decision.gate_open is False
    assert tuple(item.field for item in decision.mismatches) == (
        "reconciliation_state",
        "discrepancy_count",
    )
    assert all(
        item.severity is ShadowMismatchSeverity.CRITICAL
        for item in decision.mismatches
    )


def test_shadow_gate_is_not_comparable_for_stale_evidence() -> None:
    current = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    stale = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )
    decision = classify_shadow_mismatches(
        compare_shadow_evidence(current, stale)
    )
    assert decision.state is ShadowParityState.NOT_COMPARABLE
    assert decision.mismatches == ()
    assert decision.gate_open is False


def test_shadow_gate_classification_is_deterministic() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.CANCELLED.value,
        reconciliation_state="DIVERGENT",
        discrepancy_count=2,
    )
    first = classify_shadow_mismatches(
        compare_shadow_evidence(baseline, candidate)
    )
    second = classify_shadow_mismatches(
        compare_shadow_evidence(baseline, candidate)
    )
    assert first == second
    assert first.gate_open is False

class Phase14AReadinessState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True, slots=True)
class Phase14AReadinessReport:
    state: Phase14AReadinessState
    execution_verified: bool
    reconciliation_verified: bool
    restart_recovery_verified: bool
    shadow_isolation_verified: bool
    parity_state: ShadowParityState
    critical_mismatches: tuple[str, ...]
    gate_open: bool
    fingerprint: str


def build_phase14a_readiness_report(
    *,
    execution_verified: bool,
    reconciliation_verified: bool,
    restart_recovery_verified: bool,
    shadow_isolation_verified: bool,
    gate_decision: ShadowGateDecision,
) -> Phase14AReadinessReport:
    critical_mismatches = tuple(
        item.field
        for item in gate_decision.mismatches
        if item.severity is ShadowMismatchSeverity.CRITICAL
    )

    prerequisites_ok = all(
        (
            execution_verified,
            reconciliation_verified,
            restart_recovery_verified,
            shadow_isolation_verified,
        )
    )

    if gate_decision.state is ShadowParityState.NOT_COMPARABLE:
        state = Phase14AReadinessState.NOT_COMPARABLE
        gate_open = False
    elif (
        prerequisites_ok
        and gate_decision.state is ShadowParityState.PASS
        and gate_decision.gate_open
        and not critical_mismatches
    ):
        state = Phase14AReadinessState.READY
        gate_open = True
    else:
        state = Phase14AReadinessState.BLOCKED
        gate_open = False

    payload = {
        "state": state.value,
        "execution_verified": execution_verified,
        "reconciliation_verified": reconciliation_verified,
        "restart_recovery_verified": restart_recovery_verified,
        "shadow_isolation_verified": shadow_isolation_verified,
        "parity_state": gate_decision.state.value,
        "critical_mismatches": critical_mismatches,
        "gate_open": gate_open,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return Phase14AReadinessReport(
        state=state,
        execution_verified=execution_verified,
        reconciliation_verified=reconciliation_verified,
        restart_recovery_verified=restart_recovery_verified,
        shadow_isolation_verified=shadow_isolation_verified,
        parity_state=gate_decision.state,
        critical_mismatches=critical_mismatches,
        gate_open=gate_open,
        fingerprint=fingerprint,
    )


def test_phase14a_readiness_report_is_ready_only_when_every_local_gate_passes() -> None:
    evidence = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    report = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=True,
        shadow_isolation_verified=True,
        gate_decision=classify_shadow_mismatches(
            compare_shadow_evidence(evidence, evidence)
        ),
    )

    assert report.state is Phase14AReadinessState.READY
    assert report.parity_state is ShadowParityState.PASS
    assert report.critical_mismatches == ()
    assert report.gate_open is True


def test_phase14a_readiness_report_fails_closed_when_one_prerequisite_is_missing() -> None:
    evidence = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    report = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=False,
        shadow_isolation_verified=True,
        gate_decision=classify_shadow_mismatches(
            compare_shadow_evidence(evidence, evidence)
        ),
    )

    assert report.state is Phase14AReadinessState.BLOCKED
    assert report.gate_open is False


def test_phase14a_readiness_report_carries_critical_parity_mismatches() -> None:
    baseline = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    candidate = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.CANCELLED.value,
        reconciliation_state="DIVERGENT",
        discrepancy_count=2,
    )
    report = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=True,
        shadow_isolation_verified=True,
        gate_decision=classify_shadow_mismatches(
            compare_shadow_evidence(baseline, candidate)
        ),
    )

    assert report.state is Phase14AReadinessState.BLOCKED
    assert report.gate_open is False
    assert report.critical_mismatches == (
        "order_status",
        "reconciliation_state",
        "discrepancy_count",
    )


def test_phase14a_readiness_report_is_not_comparable_for_stale_shadow_evidence() -> None:
    current = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    stale = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.STALE.value,
        discrepancy_count=1,
    )
    report = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=True,
        shadow_isolation_verified=True,
        gate_decision=classify_shadow_mismatches(
            compare_shadow_evidence(current, stale)
        ),
    )

    assert report.state is Phase14AReadinessState.NOT_COMPARABLE
    assert report.parity_state is ShadowParityState.NOT_COMPARABLE
    assert report.gate_open is False


def test_phase14a_readiness_report_fingerprint_is_deterministic() -> None:
    evidence = ShadowComparisonEvidence(
        order_status=ExecutionOrderStatus.ACCEPTED.value,
        reconciliation_state=ReconciliationResultState.MATCHED.value,
        discrepancy_count=0,
    )
    decision = classify_shadow_mismatches(
        compare_shadow_evidence(evidence, evidence)
    )
    first = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=True,
        shadow_isolation_verified=True,
        gate_decision=decision,
    )
    second = build_phase14a_readiness_report(
        execution_verified=True,
        reconciliation_verified=True,
        restart_recovery_verified=True,
        shadow_isolation_verified=True,
        gate_decision=decision,
    )

    assert first == second
    assert first.fingerprint == second.fingerprint
