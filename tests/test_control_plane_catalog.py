from datetime import UTC, datetime

from apps.core.application.control_plane import (
    WidgetRegistry,
    WorkspaceComposer,
)
from apps.core.application.control_plane_catalog import (
    INITIAL_WIDGET_DEFINITIONS,
    curated_workspace_templates,
)
from packages.contracts.workspace import SafetyPresentationPolicy

NOW = datetime(2026, 9, 12, 20, 0, tzinfo=UTC)


def test_initial_widget_registry_covers_required_product_families() -> None:
    keys = {item.manifest.widget_key for item in INITIAL_WIDGET_DEFINITIONS}
    assert {
        "portfolio.nav",
        "portfolio.pnl",
        "portfolio.positions",
        "execution.orders_fills",
        "strategy.status",
        "grid.desk",
        "risk.portfolio",
        "reconciliation.health",
        "venue.account_health",
        "intelligence.market_context",
        "intelligence.news_events",
        "aiea.research",
        "aiea.backtest_oos_wf",
        "audit.events",
        "system.health",
    } <= keys


def test_registry_marks_safety_capabilities_mandatory() -> None:
    mandatory = {
        item.manifest.widget_key
        for item in INITIAL_WIDGET_DEFINITIONS
        if item.manifest.safety_policy is SafetyPresentationPolicy.MANDATORY
    }
    assert mandatory == {
        "risk.portfolio",
        "reconciliation.health",
        "venue.account_health",
        "system.health",
    }


def test_curated_templates_match_master_plan_and_validate() -> None:
    templates = curated_workspace_templates(NOW)
    assert {item.template_key for item in templates} == {
        "command-center",
        "active-trader",
        "grid-desk",
        "aiea-researcher",
        "risk-operations",
        "multi-account-desk",
        "blank-workspace",
    }
    composer = WorkspaceComposer(WidgetRegistry(INITIAL_WIDGET_DEFINITIONS))
    for template in templates:
        layout = composer.from_template(
            template=template,
            tenant_workspace_id="tenant-a",
            user_workspace_id=f"desk-{template.template_key}",
            user_id=7,
            created_at=NOW,
        )
        composer.validate_layout(layout)
