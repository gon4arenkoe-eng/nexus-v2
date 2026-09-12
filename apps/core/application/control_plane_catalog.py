"""Canonical Phase 11 Widget Registry and curated workspace templates."""

from __future__ import annotations

from datetime import datetime

from packages.contracts.control_plane import (
    WidgetCategory,
    WidgetDefinition,
    WidgetInstance,
    WorkspaceTemplate,
)
from packages.contracts.product_access import FeatureKey
from packages.contracts.workspace import (
    ContextKey,
    SafetyPresentationPolicy,
    WidgetManifest,
    WidgetPlacement,
    WidgetSize,
)


def _definition(
    key: str,
    *,
    category: WidgetCategory,
    contexts: frozenset[ContextKey] = frozenset(),
    feature: str | None = None,
    permission: str = "workspace.read",
    minimum: tuple[int, int] = (2, 2),
    default: tuple[int, int] = (6, 3),
    safety: SafetyPresentationPolicy = SafetyPresentationPolicy.STANDARD,
) -> WidgetDefinition:
    return WidgetDefinition(
        manifest=WidgetManifest(
            widget_key=key,
            version=1,
            supported_context_keys=contexts,
            minimum_size=WidgetSize(*minimum),
            default_size=WidgetSize(*default),
            required_feature=(None if feature is None else FeatureKey(feature)),  # noqa: E501
            required_permission=permission,
            safety_policy=safety,
        ),
        category=category,
        title_key=f"widget.{key}.title",
        description_key=f"widget.{key}.description",
        realtime_channel=f"control-plane.{key}",
    )


INITIAL_WIDGET_DEFINITIONS: tuple[WidgetDefinition, ...] = (
    _definition("portfolio.nav", category=WidgetCategory.OVERVIEW),
    _definition("portfolio.pnl", category=WidgetCategory.OVERVIEW),
    _definition(
        "portfolio.positions",
        category=WidgetCategory.TRADING,
        contexts=frozenset(
            {
                ContextKey.INSTRUMENT_ID,
                ContextKey.VENUE_ID,
                ContextKey.EXCHANGE_ACCOUNT_ID,
                ContextKey.POSITION_GROUP_ID,
            }
        ),
        default=(8, 5),
    ),
    _definition(
        "execution.orders_fills",
        category=WidgetCategory.TRADING,
        contexts=frozenset(
            {
                ContextKey.INSTRUMENT_ID,
                ContextKey.VENUE_ID,
                ContextKey.EXCHANGE_ACCOUNT_ID,
                ContextKey.POSITION_GROUP_ID,
            }
        ),
        default=(8, 5),
    ),
    _definition(
        "strategy.status",
        category=WidgetCategory.TRADING,
        contexts=frozenset(
            {
                ContextKey.STRATEGY_ID,
                ContextKey.STRATEGY_VERSION_ID,
                ContextKey.INSTRUMENT_ID,
            }
        ),
    ),
    _definition(
        "grid.desk",
        category=WidgetCategory.GRID,
        contexts=frozenset(
            {
                ContextKey.GRID_INSTANCE_ID,
                ContextKey.INSTRUMENT_ID,
                ContextKey.EXCHANGE_ACCOUNT_ID,
            }
        ),
        feature="grid.instance.create",
        default=(12, 6),
    ),
    _definition(
        "risk.portfolio",
        category=WidgetCategory.RISK,
        default=(8, 4),
        safety=SafetyPresentationPolicy.MANDATORY,
    ),
    _definition(
        "reconciliation.health",
        category=WidgetCategory.OPERATIONS,
        contexts=frozenset(
            {
                ContextKey.VENUE_ID,
                ContextKey.EXCHANGE_ACCOUNT_ID,
                ContextKey.INSTRUMENT_ID,
            }
        ),
        safety=SafetyPresentationPolicy.MANDATORY,
    ),
    _definition(
        "venue.account_health",
        category=WidgetCategory.OPERATIONS,
        contexts=frozenset(
            {ContextKey.VENUE_ID, ContextKey.EXCHANGE_ACCOUNT_ID}
        ),
        safety=SafetyPresentationPolicy.MANDATORY,
    ),
    _definition(
        "intelligence.market_context",
        category=WidgetCategory.INTELLIGENCE,
        contexts=frozenset(
            {ContextKey.INSTRUMENT_ID, ContextKey.VENUE_ID}
        ),
        default=(10, 5),
    ),
    _definition(
        "intelligence.news_events",
        category=WidgetCategory.INTELLIGENCE,
        contexts=frozenset({ContextKey.INSTRUMENT_ID}),
    ),
    _definition(
        "aiea.research",
        category=WidgetCategory.AIEA,
        contexts=frozenset(
            {ContextKey.AIEA_EXPERIMENT_ID, ContextKey.INSTRUMENT_ID}
        ),
        feature="aiea.experiment.run",
        default=(12, 6),
    ),
    _definition(
        "aiea.backtest_oos_wf",
        category=WidgetCategory.AIEA,
        contexts=frozenset(
            {
                ContextKey.AIEA_EXPERIMENT_ID,
                ContextKey.STRATEGY_ID,
                ContextKey.STRATEGY_VERSION_ID,
            }
        ),
        feature="aiea.experiment.run",
        default=(10, 5),
    ),
    _definition("audit.events", category=WidgetCategory.ADMIN, default=(8, 4)),
    _definition(
        "system.health",
        category=WidgetCategory.OPERATIONS,
        safety=SafetyPresentationPolicy.MANDATORY,
    ),
)


def _instance(
    instance_id: str,
    key: str,
    *,
    column: int,
    row: int,
    columns: int,
    rows: int,
    context_group: str | None = None,
) -> WidgetInstance:
    return WidgetInstance(
        placement=WidgetPlacement(
            instance_id=instance_id,
            widget_key=key,
            widget_version=1,
            column=column,
            row=row,
            size=WidgetSize(columns, rows),
            context_group=context_group,
        )
    )


def curated_workspace_templates(created_at: datetime) -> tuple[WorkspaceTemplate, ...]:  # noqa: E501
    return (
        WorkspaceTemplate(
            template_key="command-center",
            version=1,
            title_key="template.command_center",
            widgets=(
                _instance("nav", "portfolio.nav", column=0, row=0, columns=6, rows=3),  # noqa: E501
                _instance("pnl", "portfolio.pnl", column=6, row=0, columns=6, rows=3),  # noqa: E501
                _instance("risk", "risk.portfolio", column=12, row=0, columns=6, rows=3),  # noqa: E501
                _instance("health", "system.health", column=18, row=0, columns=6, rows=3),  # noqa: E501
                _instance("positions", "portfolio.positions", column=0, row=3, columns=12, rows=5, context_group="market"),  # noqa: E501
                _instance("intel", "intelligence.market_context", column=12, row=3, columns=12, rows=5, context_group="market"),  # noqa: E501
                _instance("strategies", "strategy.status", column=0, row=8, columns=8, rows=4, context_group="market"),  # noqa: E501
                _instance("recon", "reconciliation.health", column=8, row=8, columns=8, rows=4, context_group="market"),  # noqa: E501
                _instance("events", "audit.events", column=16, row=8, columns=8, rows=4),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="active-trader",
            version=1,
            title_key="template.active_trader",
            widgets=(
                _instance("positions", "portfolio.positions", column=0, row=0, columns=12, rows=6, context_group="market"),  # noqa: E501
                _instance("orders", "execution.orders_fills", column=12, row=0, columns=12, rows=6, context_group="market"),  # noqa: E501
                _instance("risk", "risk.portfolio", column=0, row=6, columns=8, rows=4),  # noqa: E501
                _instance("intel", "intelligence.market_context", column=8, row=6, columns=8, rows=4, context_group="market"),  # noqa: E501
                _instance("recon", "reconciliation.health", column=16, row=6, columns=8, rows=4, context_group="market"),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="grid-desk",
            version=1,
            title_key="template.grid_desk",
            widgets=(
                _instance("grid", "grid.desk", column=0, row=0, columns=14, rows=7, context_group="grid"),  # noqa: E501
                _instance("positions", "portfolio.positions", column=14, row=0, columns=10, rows=7, context_group="grid"),  # noqa: E501
                _instance("risk", "risk.portfolio", column=0, row=7, columns=8, rows=4),  # noqa: E501
                _instance("recon", "reconciliation.health", column=8, row=7, columns=8, rows=4, context_group="grid"),  # noqa: E501
                _instance("events", "audit.events", column=16, row=7, columns=8, rows=4),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="aiea-researcher",
            version=1,
            title_key="template.aiea_researcher",
            widgets=(
                _instance("research", "aiea.research", column=0, row=0, columns=12, rows=7, context_group="research"),  # noqa: E501
                _instance("oos", "aiea.backtest_oos_wf", column=12, row=0, columns=12, rows=7, context_group="research"),  # noqa: E501
                _instance("intel", "intelligence.market_context", column=0, row=7, columns=12, rows=5, context_group="research"),  # noqa: E501
                _instance("events", "audit.events", column=12, row=7, columns=12, rows=5),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="risk-operations",
            version=1,
            title_key="template.risk_operations",
            widgets=(
                _instance("risk", "risk.portfolio", column=0, row=0, columns=8, rows=5),  # noqa: E501
                _instance("recon", "reconciliation.health", column=8, row=0, columns=8, rows=5),  # noqa: E501
                _instance("venue", "venue.account_health", column=16, row=0, columns=8, rows=5),  # noqa: E501
                _instance("orders", "execution.orders_fills", column=0, row=5, columns=12, rows=6, context_group="ops"),  # noqa: E501
                _instance("events", "audit.events", column=12, row=5, columns=12, rows=6),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="multi-account-desk",
            version=1,
            title_key="template.multi_account_desk",
            widgets=(
                _instance("venue", "venue.account_health", column=0, row=0, columns=8, rows=5, context_group="accounts"),  # noqa: E501
                _instance("positions", "portfolio.positions", column=8, row=0, columns=8, rows=5, context_group="accounts"),  # noqa: E501
                _instance("risk", "risk.portfolio", column=16, row=0, columns=8, rows=5),  # noqa: E501
                _instance("orders", "execution.orders_fills", column=0, row=5, columns=12, rows=6, context_group="accounts"),  # noqa: E501
                _instance("recon", "reconciliation.health", column=12, row=5, columns=12, rows=6, context_group="accounts"),  # noqa: E501
            ),
            created_at=created_at,
        ),
        WorkspaceTemplate(
            template_key="blank-workspace",
            version=1,
            title_key="template.blank_workspace",
            widgets=(),
            created_at=created_at,
        ),
    )
