"""Read-only Control Plane operational projection contracts.

This module exposes presentation read models only. It does not own trading
state and it carries no execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ControlPlanePosition:
    symbol: str
    side: str
    quantity: Decimal
    average_entry_price: Decimal | None
    status: str
    venue_id: str
    account_value: int


@dataclass(frozen=True, slots=True)
class ControlPlaneOrder:
    order_id: str
    symbol: str
    side: str
    order_type: str
    requested_quantity: Decimal
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    limit_price: Decimal | None
    status: str
    venue_id: str
    account_value: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ControlPlaneFill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    fee_currency: str | None
    venue_id: str
    account_value: int
    executed_at: datetime


@dataclass(frozen=True, slots=True)
class ControlPlaneReconciliationDiscrepancy:
    discrepancy_id: str
    kind: str
    subject: str
    symbol: str | None
    local_value: str | None
    venue_value: str | None
    venue_id: str | None
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ControlPlanePortfolioSummary:
    observation_state: str
    equity: Decimal
    daily_pnl: Decimal
    daily_pnl_ratio: Decimal
    drawdown_ratio: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    margin_used: Decimal
    leverage: Decimal
    margin_utilization: Decimal
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ControlPlaneRiskSummary:
    observation_state: str
    trading_state: str
    headline_utilization: Decimal
    gross_exposure_utilization: Decimal
    net_exposure_utilization: Decimal
    leverage_utilization: Decimal
    margin_limit_utilization: Decimal
    daily_drawdown_utilization: Decimal
    rolling_drawdown_utilization: Decimal
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ControlPlanePortfolioHistoryPoint:
    observed_at: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class ControlPlaneOverview:
    workspace_id: str
    user_id: int
    positions: tuple[ControlPlanePosition, ...]
    orders: tuple[ControlPlaneOrder, ...]
    fills: tuple[ControlPlaneFill, ...]
    open_position_count: int
    open_order_count: int
    reconciliation_discrepancy_count: int | None
    reconciliation_discrepancies: tuple[ControlPlaneReconciliationDiscrepancy, ...]
    reconciliation_state: str
    reconciliation_last_sync: datetime | None
    portfolio_state: str
    risk_state: str
    portfolio: ControlPlanePortfolioSummary | None
    risk: ControlPlaneRiskSummary | None
    portfolio_history: tuple[ControlPlanePortfolioHistoryPoint, ...]


class ControlPlaneReadPort(Protocol):
    async def overview(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> ControlPlaneOverview:
        """Return tenant-membership-checked, user-scoped operational state."""
