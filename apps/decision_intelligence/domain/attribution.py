"""Canonical lineage and accounting evidence for DecisionOutcome attribution.

Decision Intelligence never owns fills or PnL truth.  These contracts only
link one immutable portfolio decision to Core execution lineage and represent
accounting evidence already emitted by the canonical Ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from packages.contracts.primitives import normalize_utc_datetime, require_decimal


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _positive_user_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("user_id must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class DecisionExecutionLink:
    """Immutable decision -> TradeIntent lineage created before execution."""

    link_id: str
    workspace_id: str
    user_id: int
    decision_id: str
    intent_id: str
    strategy_id: str
    strategy_version: str
    linked_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "link_id",
            "workspace_id",
            "decision_id",
            "intent_id",
            "strategy_id",
            "strategy_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        object.__setattr__(self, "user_id", _positive_user_id(self.user_id))
        object.__setattr__(
            self,
            "linked_at",
            normalize_utc_datetime(self.linked_at, field_name="linked_at"),
        )


@dataclass(frozen=True, slots=True)
class ExecutionPlanLineage:
    """Read-only Core execution-plan identity needed by attribution."""

    plan_id: str
    intent_id: str
    user_id: int
    strategy_id: str
    strategy_version: str

    def __post_init__(self) -> None:
        for name in ("plan_id", "intent_id", "strategy_id", "strategy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        object.__setattr__(self, "user_id", _positive_user_id(self.user_id))


@dataclass(frozen=True, slots=True)
class LedgerAttributionEvent:
    """Accounting evidence projected from one canonical FILL_RECORDED event."""

    event_id: str
    plan_id: str
    user_id: int
    occurred_at: datetime
    realized_pnl: Decimal
    realized_r_multiple: Decimal
    fees: Decimal
    funding: Decimal
    slippage: Decimal

    def __post_init__(self) -> None:
        for name in ("event_id", "plan_id"):
            object.__setattr__(self, name, _text(getattr(self, name), field_name=name))
        object.__setattr__(self, "user_id", _positive_user_id(self.user_id))
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(self.occurred_at, field_name="occurred_at"),
        )
        for name in (
            "realized_pnl",
            "realized_r_multiple",
            "fees",
            "funding",
            "slippage",
        ):
            object.__setattr__(
                self,
                name,
                require_decimal(getattr(self, name), field_name=name),
            )
