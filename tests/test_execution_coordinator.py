"""Phase 4 tests for deterministic single-leg execution coordination."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.core.application.execution_coordinator import (
    ExecutionCoordinatorError,
    SingleLegExecutionCoordinator,
    UnsafeRetryError,
)
from apps.core.domain.execution_coordinator import ExecutionCoordinatorState
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.execution_coordinator import (
    ExecutionCoordinatorStateRecord,
)
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


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
ACCOUNT = AccountId(VenueId("BINANCE"), 7)
INSTRUMENT = InstrumentId(
    VenueId("BINANCE"),
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


def make_order(
    *,
    order_id: str = "order-1",
    client_order_id: str = "client-1",
    reduce_only: bool = False,
    quantity: Decimal = Decimal("1"),
) -> ExecutionOrder:
    return ExecutionOrder(
        order_id=OrderId(order_id),
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        account_id=ACCOUNT,
        instrument_id=INSTRUMENT,
        client_order_id=ClientOrderId(client_order_id),
        venue_order_id=None,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_quantity=quantity,
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=None,
        reduce_only=reduce_only,
        status=ExecutionOrderStatus.PENDING,
        rejection_reason=None,
        submitted_at=None,
        accepted_at=None,
        filled_at=None,
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


class MemoryStateStore:
    def __init__(self) -> None:
        self.records: dict[
            tuple[int, str],
            ExecutionCoordinatorStateRecord,
        ] = {}

    async def load(
        self,
        *,
        user_id: int,
        order_id: OrderId,
    ) -> ExecutionCoordinatorStateRecord | None:
        return self.records.get((user_id, str(order_id)))

    async def checkpoint(
        self,
        record: ExecutionCoordinatorStateRecord,
    ) -> None:
        self.records[(record.user_id, str(record.order_id))] = record


class ScriptedVenue:
    def __init__(self) -> None:
        self.submit_results: list[VenueOrderResult | Exception] = []
        self.cancel_results: list[VenueOrderResult] = []
        self.get_results: list[VenueOrderResult | None] = []
        self.open_orders: list[VenueOrderResult] = []
        self.submit_calls: list[VenueOrderRequest] = []
        self.cancel_calls: list[VenueOrderId] = []
        self.get_calls: list[VenueOrderId] = []
        self.open_calls = 0

    @property
    def capabilities(self):
        return frozenset()

    async def submit_order(
        self,
        request: VenueOrderRequest,
    ) -> VenueOrderResult:
        self.submit_calls.append(request)
        outcome = self.submit_results.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def cancel_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        self.cancel_calls.append(venue_order_id)
        return self.cancel_results.pop(0)

    async def get_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        self.get_calls.append(venue_order_id)
        outcome = self.get_results.pop(0)
        if outcome is None:
            raise RuntimeError("scripted get result unexpectedly absent")
        return outcome

    async def get_open_orders(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
    ) -> tuple[VenueOrderResult, ...]:
        self.open_calls += 1
        return tuple(self.open_orders)

    async def get_positions(self, *, account_id: AccountId):
        return ()

    async def get_account_state(self, *, account_id: AccountId):
        raise NotImplementedError

    async def get_fills(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
        since: datetime | None = None,
    ):
        return ()


def accepted() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("venue-1"),
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
    )


def filled() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("venue-1"),
        state=VenueOrderState.FILLED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("1"),
        average_fill_price=Decimal("50000"),
    )


def partial() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("venue-1"),
        state=VenueOrderState.PARTIALLY_FILLED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0.4"),
        average_fill_price=Decimal("50000"),
    )


def cancelled(quantity: Decimal = Decimal("0")) -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("venue-1"),
        state=VenueOrderState.CANCELLED,
        requested_quantity=Decimal("1"),
        filled_quantity=quantity,
        average_fill_price=Decimal("50000") if quantity else None,
    )


def rejected() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=None,
        state=VenueOrderState.REJECTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        rejection_reason="insufficient margin",
    )


def test_state_machine_open_path_is_deterministic() -> None:
    async def scenario():
        venue = ScriptedVenue()
        venue.submit_results = [accepted(), filled()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()

        first = await coordinator.execute(order, now=NOW)
        venue.get_results = [filled()]

        second_order = first.order

        second = await coordinator.execute(
            second_order,
            now=NOW + timedelta(seconds=1),
        )
        return first, second, store

    first, second, store = asyncio.run(scenario())

    assert first.state is ExecutionCoordinatorState.OPENING
    assert first.order.status is ExecutionOrderStatus.ACCEPTED
    assert second.state is ExecutionCoordinatorState.OPEN
    assert second.order.status is ExecutionOrderStatus.FILLED
    assert second.attempt == 1
    assert (
        store.records[(7, "order-1")].state
        is ExecutionCoordinatorState.OPEN
    )


def test_reject_is_failed_and_terminal() -> None:
    async def scenario():
        venue = ScriptedVenue()
        venue.submit_results = [rejected()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        return await coordinator.execute(
            make_order(),
            now=NOW,
        )

    outcome = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.FAILED
    assert outcome.order.status is ExecutionOrderStatus.REJECTED
    assert outcome.order.rejection_reason == "insufficient margin"


def test_timeout_becomes_unknown_and_never_silently_succeeds() -> None:
    async def scenario():
        venue = ScriptedVenue()
        venue.submit_results = [TimeoutError()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        outcome = await coordinator.execute(
            make_order(),
            now=NOW,
        )
        return outcome, venue

    outcome, venue = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.RECOVERY
    assert outcome.order.status is ExecutionOrderStatus.UNKNOWN
    assert outcome.requires_recovery is True
    assert outcome.attempt == 1
    assert len(venue.submit_calls) == 1


def test_recovery_resolves_known_venue_order_after_restart() -> None:
    async def scenario():
        store = MemoryStateStore()
        first_venue = ScriptedVenue()
        first_venue.submit_results = [TimeoutError()]

        first = SingleLegExecutionCoordinator(
            user_id=7,
            venue=first_venue,
            state_store=store,
        )

        order = make_order()
        unknown = await first.execute(order, now=NOW)

        second_venue = ScriptedVenue()
        second_venue.open_orders = [filled()]

        second = SingleLegExecutionCoordinator(
            user_id=7,
            venue=second_venue,
            state_store=store,
        )

        resolved = await second.recover(
            unknown.order,
            now=NOW + timedelta(seconds=1),
        )
        return unknown, resolved, second_venue

    unknown, resolved, venue = asyncio.run(scenario())

    assert unknown.state is ExecutionCoordinatorState.RECOVERY
    assert resolved.state is ExecutionCoordinatorState.OPEN
    assert resolved.order.status is ExecutionOrderStatus.FILLED
    assert venue.open_calls == 1


def test_retry_requires_explicit_confirmed_absence() -> None:
    async def scenario():
        store = MemoryStateStore()
        venue = ScriptedVenue()
        venue.submit_results = [TimeoutError(), accepted()]

        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        unknown = await coordinator.execute(
            make_order(),
            now=NOW,
        )

        with pytest.raises(UnsafeRetryError):
            await coordinator.retry_after_confirmed_absence(
                unknown.order,
                now=NOW + timedelta(seconds=1),
                venue_confirmed_absent=False,
            )

        return await coordinator.retry_after_confirmed_absence(
            unknown.order,
            now=NOW + timedelta(seconds=1),
            venue_confirmed_absent=True,
        )

    outcome = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.OPENING
    assert outcome.order.status is ExecutionOrderStatus.ACCEPTED


def test_duplicate_execute_after_terminal_state_is_idempotent() -> None:
    async def scenario():
        store = MemoryStateStore()
        venue = ScriptedVenue()
        venue.submit_results = [filled()]

        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        first = await coordinator.execute(
            make_order(),
            now=NOW,
        )
        duplicate = await coordinator.execute(
            first.order,
            now=NOW + timedelta(seconds=1),
        )
        return first, duplicate, venue

    first, duplicate, venue = asyncio.run(scenario())

    assert first.state is ExecutionCoordinatorState.OPEN
    assert duplicate.idempotent is True
    assert duplicate.state is ExecutionCoordinatorState.OPEN
    assert len(venue.submit_calls) == 1


def test_cancel_and_replace_requires_confirmed_cancel() -> None:
    async def scenario():
        store = MemoryStateStore()
        venue = ScriptedVenue()
        venue.submit_results = [accepted()]
        venue.cancel_results = [cancelled()]
        venue.submit_results.append(accepted())

        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        original = await coordinator.execute(
            make_order(),
            now=NOW,
        )
        replacement = make_order(
            order_id="order-2",
            client_order_id="client-2",
            quantity=Decimal("0.8"),
        )

        result = await coordinator.cancel_replace(
            original.order,
            replacement,
            now=NOW + timedelta(seconds=1),
        )
        return original, result, venue

    original, result, venue = asyncio.run(scenario())

    assert original.state is ExecutionCoordinatorState.OPENING
    assert result.state is ExecutionCoordinatorState.OPENING
    assert len(venue.cancel_calls) == 1
    assert len(venue.submit_calls) == 2


def test_cancel_unknown_blocks_replacement_and_enters_recovery() -> None:
    async def scenario():
        store = MemoryStateStore()
        venue = ScriptedVenue()
        venue.submit_results = [accepted()]
        venue.cancel_results = [
            VenueOrderResult(
                client_order_id=ClientOrderId("client-1"),
                venue_order_id=VenueOrderId("venue-1"),
                state=VenueOrderState.UNKNOWN,
                requested_quantity=Decimal("1"),
                filled_quantity=Decimal("0"),
            )
        ]

        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        original = await coordinator.execute(
            make_order(),
            now=NOW,
        )

        return await coordinator.cancel(
            original.order,
            now=NOW + timedelta(seconds=1),
        )

    outcome = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.RECOVERY
    assert outcome.order.status is ExecutionOrderStatus.UNKNOWN
    assert outcome.requires_recovery is True


def test_cancel_replace_rejects_same_identities() -> None:
    async def scenario():
        store = MemoryStateStore()
        venue = ScriptedVenue()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        return await coordinator.cancel_replace(
            make_order(),
            make_order(),
            now=NOW,
        )

    with pytest.raises(Exception):
        asyncio.run(scenario())


def test_cancel_timeout_enters_recovery() -> None:
    class TimeoutCancelVenue(ScriptedVenue):
        async def cancel_order(
            self,
            *,
            account_id: AccountId,
            instrument_id: InstrumentId,
            venue_order_id: VenueOrderId,
        ) -> VenueOrderResult:
            self.cancel_calls.append(venue_order_id)
            raise TimeoutError()

    async def scenario():
        venue = TimeoutCancelVenue()
        venue.submit_results = [accepted()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()

        submitted = await coordinator.execute(order, now=NOW)
        return await coordinator.cancel(
            submitted.order,
            now=NOW + timedelta(seconds=1),
        )

    outcome = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.RECOVERY
    assert outcome.requires_recovery is True
    assert outcome.order.status is ExecutionOrderStatus.UNKNOWN


def test_recovery_query_failure_remains_recovery() -> None:
    class FailingQueryVenue(ScriptedVenue):
        async def get_order(
            self,
            *,
            account_id: AccountId,
            instrument_id: InstrumentId,
            venue_order_id: VenueOrderId,
        ) -> VenueOrderResult:
            raise TimeoutError()

    async def scenario():
        venue = FailingQueryVenue()
        venue.submit_results = [TimeoutError()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()

        outcome = await coordinator.execute(
            order,
            now=NOW,
        )
        venue.get_results = []
        return await coordinator.recover(
            outcome.order,
            now=NOW + timedelta(seconds=1),
        )

    recovered = asyncio.run(scenario())

    assert recovered.state is ExecutionCoordinatorState.RECOVERY
    assert recovered.requires_recovery is True


def test_invalid_state_transition_is_rejected() -> None:
    from apps.core.domain.execution_coordinator import (
        ExecutionCoordinatorTransitionError,
        require_transition,
    )

    with pytest.raises(ExecutionCoordinatorTransitionError):
        require_transition(
            ExecutionCoordinatorState.CLOSED,
            ExecutionCoordinatorState.OPENING,
        )


def test_persisted_account_or_instrument_mismatch_fails_closed() -> None:
    async def scenario():
        venue = ScriptedVenue()
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()
        await coordinator.execute(
            order,
            now=NOW,
        )
        store.records[(7, "order-1")] = ExecutionCoordinatorStateRecord(
            user_id=7,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            account_id=ACCOUNT,
            instrument_id=InstrumentId(
                VenueId("BINANCE"),
                "ETHUSDT",
                InstrumentType.PERPETUAL,
                AssetClass.CRYPTO,
            ),
            state=ExecutionCoordinatorState.OPENING,
            attempt=1,
            venue_order_id=None,
            updated_at=NOW,
            created_at=NOW,
        )

        return await coordinator.execute(
            order,
            now=NOW + timedelta(seconds=1),
        )

    with pytest.raises(ExecutionCoordinatorError):
        asyncio.run(scenario())


def test_partial_fill_is_preserved_and_remains_opening() -> None:
    async def scenario():
        venue = ScriptedVenue()
        venue.submit_results = [partial()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        return await coordinator.execute(
            make_order(),
            now=NOW,
        )

    outcome = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.OPENING
    assert outcome.order.status is ExecutionOrderStatus.PARTIALLY_FILLED
    assert outcome.order.filled_quantity == Decimal("0.4")
    assert outcome.order.average_fill_price == Decimal("50000")


def test_cancel_exception_increments_attempt_and_persists_recovery() -> None:
    class FailingCancelVenue(ScriptedVenue):
        async def cancel_order(
            self,
            *,
            account_id: AccountId,
            instrument_id: InstrumentId,
            venue_order_id: VenueOrderId,
        ) -> VenueOrderResult:
            self.cancel_calls.append(venue_order_id)
            raise RuntimeError("venue unavailable")

    async def scenario():
        venue = FailingCancelVenue()
        venue.submit_results = [accepted()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )

        submitted = await coordinator.execute(
            make_order(),
            now=NOW,
        )
        return await coordinator.cancel(
            submitted.order,
            now=NOW + timedelta(seconds=1),
        ), store

    outcome, store = asyncio.run(scenario())

    assert outcome.state is ExecutionCoordinatorState.RECOVERY
    assert outcome.attempt == 2
    assert store.records[(7, "order-1")].state is (
        ExecutionCoordinatorState.RECOVERY
    )


def test_retry_after_confirmed_absence_reuses_client_identity() -> None:
    async def scenario():
        venue = ScriptedVenue()
        venue.submit_results = [
            TimeoutError(),
            accepted(),
        ]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()

        failed = await coordinator.execute(
            order,
            now=NOW,
        )
        retried = await coordinator.retry_after_confirmed_absence(
            failed.order,
            now=NOW + timedelta(seconds=1),
            venue_confirmed_absent=True,
        )
        return venue, failed, retried

    venue, failed, retried = asyncio.run(scenario())

    assert failed.state is ExecutionCoordinatorState.RECOVERY
    assert retried.state is ExecutionCoordinatorState.OPENING
    assert len(venue.submit_calls) == 2
    assert venue.submit_calls[0].client_order_id == (
        venue.submit_calls[1].client_order_id
    )


def test_concurrent_execute_submits_once() -> None:
    class DelayedVenue(ScriptedVenue):
        async def submit_order(
            self,
            request: VenueOrderRequest,
        ) -> VenueOrderResult:
            await asyncio.sleep(0.01)
            return await super().submit_order(request)

    async def scenario():
        venue = DelayedVenue()
        venue.submit_results = [filled()]
        store = MemoryStateStore()
        coordinator = SingleLegExecutionCoordinator(
            user_id=7,
            venue=venue,
            state_store=store,
        )
        order = make_order()

        return await asyncio.gather(
            coordinator.execute(order, now=NOW),
            coordinator.execute(order, now=NOW),
        ), venue

    outcomes, venue = asyncio.run(scenario())

    assert len(venue.submit_calls) == 1
    assert len(outcomes) == 2
    assert any(outcome.idempotent for outcome in outcomes)
