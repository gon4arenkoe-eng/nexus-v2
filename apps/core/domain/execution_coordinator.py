"""Canonical single-leg execution coordinator workflow states."""

from __future__ import annotations

from enum import StrEnum


class ExecutionCoordinatorState(StrEnum):
    PENDING = "PENDING"
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    RECOVERY = "RECOVERY"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[
    ExecutionCoordinatorState,
    frozenset[ExecutionCoordinatorState],
] = {
    ExecutionCoordinatorState.PENDING: frozenset(
        {
            ExecutionCoordinatorState.OPENING,
            ExecutionCoordinatorState.CLOSING,
        }
    ),
    ExecutionCoordinatorState.OPENING: frozenset(
        {
            ExecutionCoordinatorState.OPENING,
            ExecutionCoordinatorState.OPEN,
            ExecutionCoordinatorState.RECOVERY,
            ExecutionCoordinatorState.CLOSED,
            ExecutionCoordinatorState.FAILED,
        }
    ),
    ExecutionCoordinatorState.OPEN: frozenset(
        {
            ExecutionCoordinatorState.OPEN,
            ExecutionCoordinatorState.CLOSING,
        }
    ),
    ExecutionCoordinatorState.CLOSING: frozenset(
        {
            ExecutionCoordinatorState.CLOSING,
            ExecutionCoordinatorState.OPEN,
            ExecutionCoordinatorState.CLOSED,
            ExecutionCoordinatorState.RECOVERY,
            ExecutionCoordinatorState.FAILED,
        }
    ),
    ExecutionCoordinatorState.RECOVERY: frozenset(
        {
            ExecutionCoordinatorState.RECOVERY,
            ExecutionCoordinatorState.OPENING,
            ExecutionCoordinatorState.CLOSING,
            ExecutionCoordinatorState.OPEN,
            ExecutionCoordinatorState.CLOSED,
            ExecutionCoordinatorState.FAILED,
        }
    ),
    ExecutionCoordinatorState.CLOSED: frozenset(),
    ExecutionCoordinatorState.FAILED: frozenset(),
}


class ExecutionCoordinatorTransitionError(RuntimeError):
    """Raised when a workflow state transition is not permitted."""


def require_transition(
    current: ExecutionCoordinatorState,
    target: ExecutionCoordinatorState,
) -> None:
    """Validate one deterministic workflow transition."""

    if not isinstance(current, ExecutionCoordinatorState):
        raise ValueError("current must be an ExecutionCoordinatorState")
    if not isinstance(target, ExecutionCoordinatorState):
        raise ValueError("target must be an ExecutionCoordinatorState")

    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ExecutionCoordinatorTransitionError(
            f"invalid execution coordinator transition: "
            f"{current.value} -> {target.value}"
        )
