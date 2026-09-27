from __future__ import annotations

from pathlib import Path


def test_v83_frontend_fetches_canonical_control_plane_overview() -> None:
    source = Path("apps/web/index.html").read_text(encoding="utf-8")
    assert "fetch('/api/v2/control-plane/overview'" in source
    assert "refreshOperationalRows()" in source
    assert "operational?.positions" in source
    assert "operational?.orders" in source
    assert "operational?.reconciliation_discrepancies" in source


def test_portfolio_and_risk_surfaces_consume_server_projected_read_models() -> None:
    source = Path("apps/web/index.html").read_text(encoding="utf-8")
    contracts = Path("apps/web/src/contracts.ts").read_text(encoding="utf-8")
    assert "operational?.portfolio" in source
    assert "operational?.risk" in source
    assert "operational?.portfolio_history" in source
    assert "headline_utilization" in source
    assert "gross_exposure" in source
    assert "daily_pnl" in source
    assert "portfolio: OperationalPortfolioSummary | null" in contracts
    assert "risk: OperationalRiskSummary | null" in contracts
    assert "portfolio_history: OperationalPortfolioHistoryPoint[]" in contracts
    assert "function portfolioData(){return operational?.portfolio||null}" in source
    assert "function riskData(){return operational?.risk||null}" in source
    assert "operational?.positions.reduce" not in source
    assert "operational?.orders.reduce" not in source



def test_v83_runtime_site_has_no_direct_db_or_execution_authority() -> None:
    source = Path("apps/web/index.html").read_text(encoding="utf-8").lower()
    for forbidden in (
        "sqlalchemy",
        "select * from",
        "insert into",
        "venueadapter",
        "executioncoordinator",
        "submit_order(",
        "cancel_order(",
        "api_secret",
    ):
        assert forbidden not in source
