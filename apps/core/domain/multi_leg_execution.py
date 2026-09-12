"""Canonical pair and basket execution workflow contracts."""

from __future__ import annotations

from enum import StrEnum


class MultiLegExecutionState(StrEnum):
    PENDING = "PENDING"
    OPENING = "OPENING"
    OPEN = "OPEN"
    RECOVERY = "RECOVERY"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


class MultiLegRecoveryPolicy(StrEnum):
    FAIL_CLOSED = "FAIL_CLOSED"
    COORDINATED_CLOSE = "COORDINATED_CLOSE"


class MultiLegExecutionError(RuntimeError):
    """Base error for invalid multi-leg execution workflow state."""
