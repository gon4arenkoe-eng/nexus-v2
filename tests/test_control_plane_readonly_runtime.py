from __future__ import annotations

import inspect
import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import scripts.control_plane_readonly_runtime as runtime


def test_control_plane_runtime_is_loopback_read_only() -> None:
    assert runtime.DEFAULT_HOST == "127.0.0.1"
    source = inspect.getsource(runtime).lower()
    for forbidden in (
        "submit_order(",
        "cancel_order(",
        "executioncoordinator",
        "venueadapter",
        "api_key",
        "api_secret",
    ):
        assert forbidden not in source


def test_control_plane_runtime_exposes_only_get_http_boundary() -> None:
    source = inspect.getsource(runtime.ControlPlaneHandler)
    assert "def do_GET" in source
    assert "def do_POST" not in source
    assert "def do_PUT" not in source
    assert "def do_DELETE" not in source
    assert "/api/v2/control-plane/overview" in source


def test_control_plane_runtime_serves_overview_and_v83_site(monkeypatch) -> None:
    async def fake_overview():
        return {
            "workspace_id": "ws-a",
            "user_id": 7,
            "positions": [],
            "orders": [],
            "fills": [],
            "open_position_count": 0,
            "open_order_count": 0,
            "reconciliation_discrepancy_count": 0,
            "reconciliation_discrepancies": [],
            "reconciliation_state": "MATCHED",
            "reconciliation_last_sync": "2026-09-27T18:00:00+00:00",
            "portfolio_state": "UNAVAILABLE",
            "risk_state": "UNAVAILABLE",
            "portfolio": None,
            "risk": None,
            "portfolio_history": [],
        }

    monkeypatch.setattr(runtime, "_load_overview", fake_overview)
    server = ThreadingHTTPServer(("127.0.0.1", 0), runtime.ControlPlaneHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        connection = HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/api/v2/control-plane/overview")
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["reconciliation_state"] == "MATCHED"
        assert payload["risk_state"] == "UNAVAILABLE"
        connection.close()

        connection = HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/")
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "NEXUS V2" in body
        assert "/api/v2/control-plane/overview" in body
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_control_plane_runtime_serializes_portfolio_and_risk_projection(monkeypatch) -> None:
    async def fake_overview():
        return {
            "workspace_id": "ws-a",
            "user_id": 7,
            "positions": [],
            "orders": [],
            "fills": [],
            "open_position_count": 0,
            "open_order_count": 0,
            "reconciliation_discrepancy_count": 0,
            "reconciliation_discrepancies": [],
            "reconciliation_state": "MATCHED",
            "reconciliation_last_sync": "2026-09-27T18:00:00+00:00",
            "portfolio_state": "CURRENT",
            "risk_state": "ACTIVE",
            "portfolio": {
                "observation_state": "CURRENT",
                "equity": "9500",
                "daily_pnl": "-500",
                "daily_pnl_ratio": "-0.05",
                "drawdown_ratio": "0.208333333333333333",
                "gross_exposure": "2500",
                "net_exposure": "2500",
                "margin_used": "500",
                "leverage": "0.263157894736842105",
                "margin_utilization": "0.052631578947368421",
                "observed_at": "2026-09-27T18:00:00+00:00",
            },
            "risk": {
                "observation_state": "CURRENT",
                "trading_state": "ACTIVE",
                "headline_utilization": "2.08333333333333333",
                "gross_exposure_utilization": "0.125",
                "net_exposure_utilization": "0.166666666666666667",
                "leverage_utilization": "0.052631578947368421",
                "margin_limit_utilization": "0.065789473684210526",
                "daily_drawdown_utilization": "1",
                "rolling_drawdown_utilization": "2.08333333333333333",
                "observed_at": "2026-09-27T18:00:00+00:00",
            },
            "portfolio_history": [
                {"observed_at": "2026-09-27T17:55:00+00:00", "equity": "9000"},
                {"observed_at": "2026-09-27T18:00:00+00:00", "equity": "9500"},
            ],
        }

    monkeypatch.setattr(runtime, "_load_overview", fake_overview)
    server = ThreadingHTTPServer(("127.0.0.1", 0), runtime.ControlPlaneHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        connection = HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/api/v2/control-plane/overview")
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["portfolio"]["equity"] == "9500"
        assert payload["risk"]["trading_state"] == "ACTIVE"
        assert [item["equity"] for item in payload["portfolio_history"]] == ["9000", "9500"]
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
