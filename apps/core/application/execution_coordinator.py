"""Deterministic single-leg execution coordination application service."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import asyncio

from apps.core.domain.execution_coordinator import (
    ExecutionCoordinatorState,
    require_transition,
)
from apps.core.domain.execution_orders import (
    ExecutionOrder,
    ExecutionOrderStatus,
)
from apps.core.ports.execution_coordinator import (
    ExecutionCoordinatorEventSink,
    ExecutionCoordinatorStateRecord,
    ExecutionCoordinatorStateStore,
)
from apps.core.ports.venue import (
    VenueAdapter,
    VenueOrderRequest,
    VenueOrderResult,
    VenueOrderState,
)
from packages.contracts.identities import VenueOrderId


class ExecutionCoordinatorError(RuntimeError):
    """Base error for execution coordination failures."""


class UnknownExecutionOutcomeError(ExecutionCoordinatorError):
    """Venue outcome is unresolved and requires recovery."""


class UnsafeRetryError(ExecutionCoordinatorError):
    """Retry is not justified by explicit venue evidence."""


@dataclass(frozen=True, slots=True)
class ExecutionCoordinatorOutcome:
    order: ExecutionOrder
    state: ExecutionCoordinatorState
    attempt: int
    venue_result: VenueOrderResult | None
    idempotent: bool = False
    requires_recovery: bool = False


def _request_from_order(order: ExecutionOrder) -> VenueOrderRequest:
    return VenueOrderRequest(
        client_order_id=order.client_order_id,
        account_id=order.account_id,
        instrument_id=order.instrument_id,
        side=order.side,
        quantity=order.requested_quantity,
        order_type=order.order_type,
        limit_price=order.limit_price,
        reduce_only=order.reduce_only,
    )


def _submit_state(
    order: ExecutionOrder,
) -> ExecutionCoordinatorState:
    return (
        ExecutionCoordinatorState.CLOSING
        if order.reduce_only
        else ExecutionCoordinatorState.OPENING
    )


def _terminal_workflow_state(
    order: ExecutionOrder,
    result: VenueOrderResult,
) -> ExecutionCoordinatorState:
    if result.state is VenueOrderState.FILLED:
        return (
            ExecutionCoordinatorState.CLOSED
            if order.reduce_only
            else ExecutionCoordinatorState.OPEN
        )

    if result.state is VenueOrderState.CANCELLED:
        if result.filled_quantity > 0:
            return ExecutionCoordinatorState.OPEN
        if order.reduce_only:
            return ExecutionCoordinatorState.OPEN
        return ExecutionCoordinatorState.CLOSED

    if result.state is VenueOrderState.REJECTED:
        return ExecutionCoordinatorState.FAILED

    raise ExecutionCoordinatorError(
        "terminal workflow state requested for non-terminal venue result"
    )


class SingleLegExecutionCoordinator:
    """Own one deterministic single-leg execution lifecycle."""

    def __init__(
        self,
        *,
        user_id: int,
        venue: VenueAdapter,
        state_store: ExecutionCoordinatorStateStore,
        events: ExecutionCoordinatorEventSink | None = None,
    ) -> None:
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer")

        self._user_id = user_id
        self._venue = venue
        self._state_store = state_store
        self._events = events
        self._locks: dict[str, asyncio.Lock] = {}

    async def execute(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        key = str(order.order_id)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            return await self._execute_locked(
                order,
                now=now,
            )

    async def _execute_locked(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        existing = await self._state_store.load(
            user_id=self._user_id,
            order_id=order.order_id,
        )

        if existing is not None:
            if existing.client_order_id != order.client_order_id:
                raise ExecutionCoordinatorError(
                    "persisted coordinator identity conflicts with order"
                )

            if existing.state in (
                ExecutionCoordinatorState.OPENING,
                ExecutionCoordinatorState.CLOSING,
                ExecutionCoordinatorState.RECOVERY,
            ):
                return await self.recover(
                    order,
                    now=now,
                )

            return ExecutionCoordinatorOutcome(
                order=order,
                state=existing.state,
                attempt=existing.attempt,
                venue_result=None,
                idempotent=True,
            )

        state = _submit_state(order)
        record = self._new_record(
            order,
            state=state,
            now=now,
        )
        await self._checkpoint(
            record,
            order_id=order.order_id,
            event_type="EXECUTION_OPENING"
            if state is ExecutionCoordinatorState.OPENING
            else "EXECUTION_CLOSING",
            now=now,
            payload={"attempt": 0},
        )

        try:
            result = await self._venue.submit_order(
                _request_from_order(order)
            )
        except TimeoutError:
            unknown = self._transition_record(
                record,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
                attempt=record.attempt + 1,
            )
            await self._checkpoint(
                unknown,
                order_id=order.order_id,
                event_type="EXECUTION_RECOVERY_REQUIRED",
                now=now,
                payload={"reason": "submit_timeout"},
            )

            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    submitted_at=order.submitted_at or now,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unknown.attempt,
                venue_result=None,
                requires_recovery=True,
            )
        except Exception as exc:
            unknown = self._transition_record(
                record,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
                attempt=record.attempt + 1,
            )
            await self._checkpoint(
                unknown,
                order_id=order.order_id,
                event_type="EXECUTION_RECOVERY_REQUIRED",
                now=now,
                payload={
                    "reason": "submit_exception",
                    "exception": type(exc).__name__,
                },
            )

            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    submitted_at=order.submitted_at or now,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unknown.attempt,
                venue_result=None,
                requires_recovery=True,
            )

        updated_order, target_state = self._apply_venue_result(
            order,
            result,
            now=now,
        )
        completed = self._transition_record(
            record,
            target=target_state,
            now=now,
            attempt=record.attempt + 1,
            venue_order_id=(
                str(result.venue_order_id)
                if result.venue_order_id is not None
                else None
            ),
        )

        await self._checkpoint(
            completed,
            order_id=order.order_id,
            event_type=f"VENUE_{result.state.value}",
            now=now,
            payload={
                "attempt": completed.attempt,
                "venue_order_id": (
                    str(result.venue_order_id)
                    if result.venue_order_id is not None
                    else None
                ),
            },
        )

        return ExecutionCoordinatorOutcome(
            order=updated_order,
            state=target_state,
            attempt=completed.attempt,
            venue_result=result,
            requires_recovery=(
                target_state is ExecutionCoordinatorState.RECOVERY
            ),
        )

    async def recover(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        record = await self._require_record(order)

        if record.state not in (
            ExecutionCoordinatorState.RECOVERY,
            ExecutionCoordinatorState.OPENING,
            ExecutionCoordinatorState.CLOSING,
        ):
            return ExecutionCoordinatorOutcome(
                order=order,
                state=record.state,
                attempt=record.attempt,
                venue_result=None,
                idempotent=True,
            )

        try:
            result = await self._locate_venue_order(
                order,
                record,
            )
        except Exception as exc:
            await self._checkpoint(
                self._transition_record(
                    record,
                    target=ExecutionCoordinatorState.RECOVERY,
                    now=now,
                ),
                order_id=order.order_id,
                event_type="EXECUTION_RECOVERY_REQUIRED",
                now=now,
                payload={
                    "reason": "recovery_query_exception",
                    "exception": type(exc).__name__,
                },
            )
            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=record.attempt,
                venue_result=None,
                requires_recovery=True,
            )

        if result is None:
            unresolved = self._transition_record(
                record,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
            )
            await self._checkpoint(
                unresolved,
                order_id=order.order_id,
                event_type="EXECUTION_RECOVERY_WAITING",
                now=now,
                payload={"reason": "venue_order_not_located"},
            )

            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unresolved.attempt,
                venue_result=None,
                requires_recovery=True,
            )

        updated_order, target_state = self._apply_venue_result(
            order,
            result,
            now=now,
        )
        resolved = self._transition_record(
            record,
            target=target_state,
            now=now,
            venue_order_id=(
                str(result.venue_order_id)
                if result.venue_order_id is not None
                else record.venue_order_id
            ),
        )
        await self._checkpoint(
            resolved,
            order_id=order.order_id,
            event_type=f"RECOVERY_{result.state.value}",
            now=now,
            payload={"attempt": resolved.attempt},
        )

        return ExecutionCoordinatorOutcome(
            order=updated_order,
            state=target_state,
            attempt=resolved.attempt,
            venue_result=result,
        )

    async def retry_after_confirmed_absence(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
        venue_confirmed_absent: bool,
    ) -> ExecutionCoordinatorOutcome:
        if venue_confirmed_absent is not True:
            raise UnsafeRetryError(
                "retry requires explicit confirmed venue absence"
            )

        record = await self._require_record(order)

        if record.state is not ExecutionCoordinatorState.RECOVERY:
            raise UnsafeRetryError(
                "retry is only permitted from RECOVERY"
            )

        target = _submit_state(order)
        pending_retry = self._transition_record(
            record,
            target=target,
            now=now,
        )
        await self._checkpoint(
            pending_retry,
            order_id=order.order_id,
            event_type="EXECUTION_RETRY_ARMED",
            now=now,
            payload={"attempt": pending_retry.attempt},
        )

        try:
            result = await self._venue.submit_order(
                _request_from_order(order)
            )
        except TimeoutError:
            unknown = self._transition_record(
                pending_retry,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
                attempt=pending_retry.attempt + 1,
            )
            await self._checkpoint(
                unknown,
                order_id=order.order_id,
                event_type="EXECUTION_RECOVERY_REQUIRED",
                now=now,
                payload={"reason": "retry_submit_timeout"},
            )
            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unknown.attempt,
                venue_result=None,
                requires_recovery=True,
            )

        updated_order, final_state = self._apply_venue_result(
            order,
            result,
            now=now,
        )
        completed = self._transition_record(
            pending_retry,
            target=final_state,
            now=now,
            attempt=pending_retry.attempt + 1,
            venue_order_id=(
                str(result.venue_order_id)
                if result.venue_order_id is not None
                else pending_retry.venue_order_id
            ),
        )
        await self._checkpoint(
            completed,
            order_id=order.order_id,
            event_type=f"RETRY_{result.state.value}",
            now=now,
            payload={"attempt": completed.attempt},
        )

        return ExecutionCoordinatorOutcome(
            order=updated_order,
            state=final_state,
            attempt=completed.attempt,
            venue_result=result,
        )

    async def cancel(
        self,
        order: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        record = await self._require_record(order)

        if record.venue_order_id is None:
            raise ExecutionCoordinatorError(
                "cancel requires a known venue order identity"
            )

        try:
            result = await self._venue.cancel_order(
                account_id=order.account_id,
                instrument_id=order.instrument_id,
                venue_order_id=VenueOrderId(record.venue_order_id),
            )
        except Exception as exc:
            unknown = self._transition_record(
                record,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
                attempt=record.attempt + 1,
            )
            await self._checkpoint(
                unknown,
                order_id=order.order_id,
                event_type="CANCEL_RECOVERY_REQUIRED",
                now=now,
                payload={
                    "reason": "cancel_exception",
                    "exception": type(exc).__name__,
                },
            )
            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unknown.attempt,
                venue_result=None,
                requires_recovery=True,
            )

        if result.state is VenueOrderState.UNKNOWN:
            unknown = self._transition_record(
                record,
                target=ExecutionCoordinatorState.RECOVERY,
                now=now,
            )
            await self._checkpoint(
                unknown,
                order_id=order.order_id,
                event_type="CANCEL_RECOVERY_REQUIRED",
                now=now,
                payload={"attempt": unknown.attempt},
            )
            return ExecutionCoordinatorOutcome(
                order=replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    updated_at=now,
                ),
                state=ExecutionCoordinatorState.RECOVERY,
                attempt=unknown.attempt,
                venue_result=result,
                requires_recovery=True,
            )

        updated_order, target_state = self._apply_venue_result(
            order,
            result,
            now=now,
        )
        completed = self._transition_record(
            record,
            target=target_state,
            now=now,
        )
        await self._checkpoint(
            completed,
            order_id=order.order_id,
            event_type=f"CANCEL_{result.state.value}",
            now=now,
            payload={"attempt": completed.attempt},
        )

        return ExecutionCoordinatorOutcome(
            order=updated_order,
            state=target_state,
            attempt=completed.attempt,
            venue_result=result,
            requires_recovery=(
                target_state is ExecutionCoordinatorState.RECOVERY
            ),
        )

    async def cancel_replace(
        self,
        order: ExecutionOrder,
        replacement: ExecutionOrder,
        *,
        now: datetime,
    ) -> ExecutionCoordinatorOutcome:
        if order.order_id == replacement.order_id:
            raise ExecutionCoordinatorError(
                "replacement requires a new order identity"
            )

        if order.client_order_id == replacement.client_order_id:
            raise ExecutionCoordinatorError(
                "replacement requires a new client_order_id"
            )

        if (
            order.account_id != replacement.account_id
            or order.instrument_id != replacement.instrument_id
            or order.side != replacement.side
            or order.reduce_only != replacement.reduce_only
        ):
            raise ExecutionCoordinatorError(
                "replacement changes execution ownership or direction"
            )

        cancelled = await self.cancel(
            order,
            now=now,
        )

        if cancelled.state is ExecutionCoordinatorState.RECOVERY:
            raise UnknownExecutionOutcomeError(
                "replacement blocked until cancellation is resolved"
            )

        if cancelled.venue_result is None:
            raise UnknownExecutionOutcomeError(
                "replacement requires cancellation evidence"
            )

        if cancelled.venue_result.state is not VenueOrderState.CANCELLED:
            raise UnknownExecutionOutcomeError(
                "replacement requires confirmed cancellation"
            )

        if (
            replacement.requested_quantity
            > order.requested_quantity - cancelled.venue_result.filled_quantity
        ):
            raise ExecutionCoordinatorError(
                "replacement quantity exceeds uncancelled remainder"
            )

        return await self.execute(
            replacement,
            now=now,
        )

    async def _require_record(
        self,
        order: ExecutionOrder,
    ) -> ExecutionCoordinatorStateRecord:
        record = await self._state_store.load(
            user_id=self._user_id,
            order_id=order.order_id,
        )
        if record is None:
            raise ExecutionCoordinatorError(
                "coordinator state does not exist for order"
            )
        if (
            record.client_order_id != order.client_order_id
            or record.account_id != order.account_id
            or record.instrument_id != order.instrument_id
        ):
            raise ExecutionCoordinatorError(
                "persisted coordinator identity conflicts with order"
            )
        return record

    async def _locate_venue_order(
        self,
        order: ExecutionOrder,
        record: ExecutionCoordinatorStateRecord,
    ) -> VenueOrderResult | None:
        if record.venue_order_id is not None:
            return await self._venue.get_order(
                account_id=order.account_id,
                instrument_id=order.instrument_id,
                venue_order_id=VenueOrderId(record.venue_order_id),
            )

        open_orders = await self._venue.get_open_orders(
            account_id=order.account_id,
            instrument_id=order.instrument_id,
        )

        for candidate in open_orders:
            if candidate.client_order_id == order.client_order_id:
                return candidate

        return None

    async def _checkpoint(
        self,
        record: ExecutionCoordinatorStateRecord,
        *,
        order_id,
        event_type: str,
        now: datetime,
        payload: dict[str, object],
    ) -> None:
        await self._state_store.checkpoint(record)
        if self._events is not None:
            await self._events.record(
                order_id=order_id,
                event_type=event_type,
                attempt=record.attempt,
                occurred_at=now,
                payload=payload,
            )

    def _new_record(
        self,
        order: ExecutionOrder,
        *,
        state: ExecutionCoordinatorState,
        now: datetime,
    ) -> ExecutionCoordinatorStateRecord:
        return ExecutionCoordinatorStateRecord(
            user_id=self._user_id,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            account_id=order.account_id,
            instrument_id=order.instrument_id,
            state=state,
            attempt=0,
            venue_order_id=(
                str(order.venue_order_id)
                if order.venue_order_id is not None
                else None
            ),
            updated_at=now,
            created_at=order.created_at,
        )

    @staticmethod
    def _transition_record(
        record: ExecutionCoordinatorStateRecord,
        *,
        target: ExecutionCoordinatorState,
        now: datetime,
        attempt: int | None = None,
        venue_order_id: str | None = None,
    ) -> ExecutionCoordinatorStateRecord:
        require_transition(record.state, target)
        return replace(
            record,
            state=target,
            attempt=record.attempt if attempt is None else attempt,
            venue_order_id=(
                record.venue_order_id
                if venue_order_id is None
                else venue_order_id
            ),
            updated_at=now,
        )

    @staticmethod
    def _apply_venue_result(
        order: ExecutionOrder,
        result: VenueOrderResult,
        *,
        now: datetime,
    ) -> tuple[ExecutionOrder, ExecutionCoordinatorState]:
        if result.state is VenueOrderState.PENDING:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.SUBMITTED,
                    venue_order_id=result.venue_order_id,
                    submitted_at=order.submitted_at or now,
                    updated_at=now,
                ),
                _submit_state(order),
            )

        if result.state is VenueOrderState.ACCEPTED:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.ACCEPTED,
                    venue_order_id=result.venue_order_id,
                    submitted_at=order.submitted_at or now,
                    accepted_at=now,
                    updated_at=now,
                ),
                _submit_state(order),
            )

        if result.state is VenueOrderState.PARTIALLY_FILLED:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.PARTIALLY_FILLED,
                    venue_order_id=result.venue_order_id,
                    filled_quantity=result.filled_quantity,
                    average_fill_price=result.average_fill_price,
                    submitted_at=order.submitted_at or now,
                    accepted_at=order.accepted_at or now,
                    updated_at=now,
                ),
                _submit_state(order),
            )

        if result.state is VenueOrderState.FILLED:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.FILLED,
                    venue_order_id=result.venue_order_id,
                    filled_quantity=result.filled_quantity,
                    average_fill_price=result.average_fill_price,
                    submitted_at=order.submitted_at or now,
                    accepted_at=order.accepted_at or now,
                    filled_at=now,
                    updated_at=now,
                ),
                _terminal_workflow_state(order, result),
            )

        if result.state is VenueOrderState.CANCELLED:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.CANCELLED,
                    venue_order_id=result.venue_order_id,
                    filled_quantity=result.filled_quantity,
                    average_fill_price=result.average_fill_price,
                    cancelled_at=now,
                    updated_at=now,
                ),
                _terminal_workflow_state(order, result),
            )

        if result.state is VenueOrderState.REJECTED:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.REJECTED,
                    venue_order_id=result.venue_order_id,
                    rejection_reason=result.rejection_reason,
                    submitted_at=order.submitted_at or now,
                    updated_at=now,
                ),
                ExecutionCoordinatorState.FAILED,
            )

        if result.state is VenueOrderState.UNKNOWN:
            return (
                replace(
                    order,
                    status=ExecutionOrderStatus.UNKNOWN,
                    venue_order_id=result.venue_order_id,
                    submitted_at=order.submitted_at or now,
                    updated_at=now,
                ),
                ExecutionCoordinatorState.RECOVERY,
            )

        raise ExecutionCoordinatorError(
            f"unsupported venue state: {result.state!s}"
        )
