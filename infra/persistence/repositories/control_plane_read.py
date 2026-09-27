"""Read-only persistence adapter for Control Plane operational state."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.application.control_plane_read import (
    ControlPlaneFill,
    ControlPlaneOrder,
    ControlPlaneOverview,
    ControlPlanePortfolioHistoryPoint,
    ControlPlanePortfolioSummary,
    ControlPlanePosition,
    ControlPlaneReconciliationDiscrepancy,
    ControlPlaneRiskSummary,
)
from apps.core.application.portfolio_state_read import project_portfolio_state
from apps.core.domain.execution_orders import ExecutionOrderStatus
from apps.core.domain.ledger import ExecutionLedgerEventType
from infra.persistence.models.execution_orders import (
    ExecutionFillModel,
    ExecutionOrderModel,
)
from infra.persistence.models.ledger import ExecutionLedgerEventModel
from infra.persistence.models.platform_security import WorkspaceMembershipModel
from infra.persistence.models.positions import PositionGroupModel, PositionLegModel
from infra.persistence.repositories.portfolio_risk_snapshot import (
    PortfolioRiskSnapshotRepository,
)


_ACTIVE_ORDER_STATES = frozenset(
    {
        ExecutionOrderStatus.PENDING.value,
        ExecutionOrderStatus.SUBMITTED.value,
        ExecutionOrderStatus.ACCEPTED.value,
        ExecutionOrderStatus.PARTIALLY_FILLED.value,
        ExecutionOrderStatus.UNKNOWN.value,
    }
)
_RECON_EVENT_TYPES = frozenset(
    {
        ExecutionLedgerEventType.RECONCILIATION_STARTED.value,
        ExecutionLedgerEventType.RECONCILIATION_COMPLETED.value,
        ExecutionLedgerEventType.RECONCILIATION_DEGRADED.value,
        ExecutionLedgerEventType.RECONCILIATION_DISCREPANCY.value,
        ExecutionLedgerEventType.RECONCILIATION_RESOLVED.value,
    }
)
_TERMINAL_RECON_EVENT_TYPES = frozenset(
    {
        ExecutionLedgerEventType.RECONCILIATION_COMPLETED.value,
        ExecutionLedgerEventType.RECONCILIATION_DEGRADED.value,
    }
)


class ControlPlaneReadRepository:
    """Project canonical persistence into read-only Control Plane state.

    The active workspace membership check is fail-closed. Current Core trading
    projections are user-scoped rather than workspace-scoped; therefore this
    adapter deliberately does not claim full tenant resource isolation. That
    missing ownership linkage remains a Phase 10/11 integration gap.
    """

    def __init__(self, session: AsyncSession) -> None:
        if not isinstance(session, AsyncSession):
            raise ValueError("session must be AsyncSession")
        self._session = session

    async def _require_active_membership(
        self, *, workspace_id: str, user_id: int
    ) -> None:
        membership = await self._session.get(
            WorkspaceMembershipModel, (workspace_id, user_id)
        )
        if membership is None or not membership.active:
            raise PermissionError("active workspace membership required")

    async def overview(
        self, *, workspace_id: str, user_id: int
    ) -> ControlPlaneOverview:
        await self._require_active_membership(
            workspace_id=workspace_id, user_id=user_id
        )

        position_result = await self._session.execute(
            select(PositionLegModel)
            .join(
                PositionGroupModel,
                PositionGroupModel.group_id == PositionLegModel.group_id,
            )
            .where(
                PositionGroupModel.user_id == user_id,
                PositionLegModel.current_quantity > 0,
            )
            .order_by(PositionLegModel.updated_at.desc())
        )
        position_models = tuple(position_result.scalars().all())
        positions = tuple(
            ControlPlanePosition(
                symbol=model.native_symbol,
                side=model.side,
                quantity=model.current_quantity,
                average_entry_price=model.average_entry_price,
                status=model.status,
                venue_id=model.venue_id,
                account_value=model.account_value,
            )
            for model in position_models
        )

        order_result = await self._session.execute(
            select(ExecutionOrderModel)
            .where(ExecutionOrderModel.user_id == user_id)
            .order_by(ExecutionOrderModel.updated_at.desc())
            .limit(100)
        )
        order_models = tuple(order_result.scalars().all())
        orders = tuple(
            ControlPlaneOrder(
                order_id=model.order_id,
                symbol=model.native_symbol,
                side=model.side,
                order_type=model.order_type,
                requested_quantity=model.requested_quantity,
                filled_quantity=model.filled_quantity,
                average_fill_price=model.average_fill_price,
                limit_price=model.limit_price,
                status=model.local_status,
                venue_id=model.venue_id,
                account_value=model.account_value,
                updated_at=model.updated_at,
            )
            for model in order_models
        )

        fill_result = await self._session.execute(
            select(ExecutionFillModel, ExecutionOrderModel)
            .join(
                ExecutionOrderModel,
                ExecutionOrderModel.order_id == ExecutionFillModel.order_id,
            )
            .where(ExecutionFillModel.user_id == user_id)
            .order_by(ExecutionFillModel.executed_at.desc())
            .limit(100)
        )
        fills = tuple(
            ControlPlaneFill(
                fill_id=fill.fill_id,
                order_id=fill.order_id,
                symbol=order.native_symbol,
                side=order.side,
                quantity=fill.quantity,
                price=fill.price,
                fee=fill.fee,
                fee_currency=fill.fee_currency,
                venue_id=fill.venue_id,
                account_value=fill.account_value,
                executed_at=fill.executed_at,
            )
            for fill, order in fill_result.all()
        )

        reconciliation_result = await self._session.execute(
            select(ExecutionLedgerEventModel)
            .where(
                ExecutionLedgerEventModel.user_id == user_id,
                ExecutionLedgerEventModel.event_type.in_(_RECON_EVENT_TYPES),
            )
            .order_by(
                ExecutionLedgerEventModel.occurred_at.asc(),
                ExecutionLedgerEventModel.id.asc(),
            )
        )
        reconciliation_events = tuple(reconciliation_result.scalars().all())

        active_discrepancy_events: dict[str, ExecutionLedgerEventModel] = {}
        has_unscoped_legacy_discrepancy = False
        latest_terminal: ExecutionLedgerEventModel | None = None
        for event in reconciliation_events:
            payload = event.payload if isinstance(event.payload, dict) else {}
            discrepancy_id = payload.get("discrepancy_id")
            if event.event_type == ExecutionLedgerEventType.RECONCILIATION_DISCREPANCY.value:
                if isinstance(discrepancy_id, str):
                    active_discrepancy_events[discrepancy_id] = event
                else:
                    has_unscoped_legacy_discrepancy = True
            elif event.event_type == ExecutionLedgerEventType.RECONCILIATION_RESOLVED.value:
                if isinstance(discrepancy_id, str):
                    active_discrepancy_events.pop(discrepancy_id, None)
            if event.event_type in _TERMINAL_RECON_EVENT_TYPES:
                latest_terminal = event

        discrepancy_count: int | None
        if has_unscoped_legacy_discrepancy and not active_discrepancy_events:
            discrepancy_count = None
        else:
            discrepancy_count = len(active_discrepancy_events)

        reconciliation_discrepancies = tuple(
            ControlPlaneReconciliationDiscrepancy(
                discrepancy_id=discrepancy_id,
                kind=str(event.payload.get("kind", "UNKNOWN")),
                subject=str(event.payload.get("subject", "UNKNOWN")),
                symbol=event.native_symbol,
                local_value=(
                    None
                    if event.payload.get("local_value") is None
                    else str(event.payload.get("local_value"))
                ),
                venue_value=(
                    None
                    if event.payload.get("venue_value") is None
                    else str(event.payload.get("venue_value"))
                ),
                venue_id=event.venue_id,
                observed_at=event.occurred_at,
            )
            for discrepancy_id, event in sorted(
                active_discrepancy_events.items(),
                key=lambda item: item[1].occurred_at,
                reverse=True,
            )
        )

        if latest_terminal is None:
            reconciliation_state = "UNKNOWN"
            reconciliation_last_sync = None
        else:
            terminal_payload = (
                latest_terminal.payload
                if isinstance(latest_terminal.payload, dict)
                else {}
            )
            result_state = terminal_payload.get("result_state")
            reconciliation_state = (
                result_state if isinstance(result_state, str) else "UNKNOWN"
            )
            reconciliation_last_sync = latest_terminal.occurred_at

        risk_records = await PortfolioRiskSnapshotRepository(
            self._session
        ).list_recent_for_user(user_id=user_id, limit=100)
        if risk_records:
            latest_record = risk_records[0]
            projected = project_portfolio_state(
                snapshot=latest_record.snapshot,
                limits=latest_record.limits,
            )
            portfolio_state = projected.observation_state
            risk_state = (
                projected.observation_state
                if projected.observation_state != "CURRENT"
                else projected.trading_state
            )
            portfolio = ControlPlanePortfolioSummary(
                observation_state=projected.observation_state,
                equity=projected.equity,
                daily_pnl=projected.daily_pnl,
                daily_pnl_ratio=projected.daily_pnl_ratio,
                drawdown_ratio=projected.rolling_drawdown_ratio,
                gross_exposure=projected.gross_exposure,
                net_exposure=projected.net_exposure,
                margin_used=projected.margin_used,
                leverage=projected.leverage,
                margin_utilization=projected.margin_utilization,
                observed_at=projected.observed_at,
            )
            risk = ControlPlaneRiskSummary(
                observation_state=projected.observation_state,
                trading_state=projected.trading_state,
                headline_utilization=projected.headline_risk_utilization,
                gross_exposure_utilization=projected.gross_exposure_utilization,
                net_exposure_utilization=projected.net_exposure_utilization,
                leverage_utilization=projected.leverage_utilization,
                margin_limit_utilization=projected.margin_limit_utilization,
                daily_drawdown_utilization=projected.daily_drawdown_utilization,
                rolling_drawdown_utilization=projected.rolling_drawdown_utilization,
                observed_at=projected.observed_at,
            )
            portfolio_history = tuple(
                ControlPlanePortfolioHistoryPoint(
                    observed_at=item.snapshot.observed_at,
                    equity=item.snapshot.equity,
                )
                for item in reversed(risk_records)
            )
        else:
            portfolio_state = "UNAVAILABLE"
            risk_state = "UNAVAILABLE"
            portfolio = None
            risk = None
            portfolio_history = ()

        return ControlPlaneOverview(
            workspace_id=workspace_id,
            user_id=user_id,
            positions=positions,
            orders=orders,
            fills=fills,
            open_position_count=len(positions),
            open_order_count=sum(
                1 for item in order_models if item.local_status in _ACTIVE_ORDER_STATES
            ),
            reconciliation_discrepancy_count=discrepancy_count,
            reconciliation_discrepancies=reconciliation_discrepancies,
            reconciliation_state=reconciliation_state,
            reconciliation_last_sync=reconciliation_last_sync,
            portfolio_state=portfolio_state,
            risk_state=risk_state,
            portfolio=portfolio,
            risk=risk,
            portfolio_history=portfolio_history,
        )
