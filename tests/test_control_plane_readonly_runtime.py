from __future__ import annotations

import inspect
import json
import threading
from types import SimpleNamespace
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import scripts.control_plane_readonly_runtime as runtime


def test_control_plane_runtime_is_loopback_without_trading_authority() -> None:
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


def test_control_plane_runtime_exposes_presentation_write_only_boundary() -> None:
    source = inspect.getsource(
        runtime.ControlPlaneHandler
    )

    assert "def do_GET" in source
    assert "def do_POST" in source
    assert "def do_PUT" not in source
    assert "def do_DELETE" not in source

    assert (
        "/api/v2/control-plane/overview"
        in source
    )
    assert (
        "/api/v2/control-plane/workspaces"
        in source
    )
    assert (
        "/api/v2/control-plane/workspaces/save"
        in source
    )


def test_workspace_projection_preserves_canonical_layout_fields() -> None:
    workspace = SimpleNamespace(
        user_workspace_id="desk",
        name="Desk",
        locale=SimpleNamespace(value="ru"),
        theme=SimpleNamespace(value="dark"),
        active_layout_version=3,
    )

    layout = SimpleNamespace(
        widgets=(
            SimpleNamespace(
                placement=SimpleNamespace(
                    instance_id="positions-1",
                    widget_key="portfolio.positions",
                    widget_version=2,
                    column=3,
                    row=5,
                    size=SimpleNamespace(
                        columns=6,
                        rows=4,
                    ),
                    context_group="btc",
                ),
                settings_json='{"timeframe":"1h"}',
            ),
        ),
    )

    payload = runtime._workspace_projection(
        workspace,
        layout,
    )

    assert payload["id"] == "desk"
    assert payload["name"] == "Desk"
    assert payload["locale"] == "ru"
    assert payload["theme"] == "dark"
    assert payload["activeLayoutVersion"] == 3

    assert payload["widgets"][0] == {
        "id": "positions-1",
        "key": "portfolio.positions",
        "widgetVersion": 2,
        "column": 3,
        "row": 5,
        "width": 6,
        "height": 4,
        "contextGroup": "btc",
        "settingsJson": '{"timeframe":"1h"}',
    }


def test_workspace_loader_keeps_server_identity_scoped() -> None:
    source = inspect.getsource(runtime._load_workspaces)

    assert (
        "tenant_workspace_id=tenant_workspace_id"
        in source
    )

    assert source.count("user_id=user_id") >= 2

    assert (
        "workspace.active_layout_version"
        in source
    )


def test_control_plane_runtime_serves_workspace_projection(
    monkeypatch,
) -> None:
    async def fake_workspaces():
        return [
            {
                "id": "desk",
                "name": "Desk",
                "locale": "ru",
                "theme": "dark",
                "activeLayoutVersion": 1,
                "widgets": [
                    {
                        "id": "positions-1",
                        "key": "portfolio.positions",
                        "widgetVersion": 1,
                        "column": 0,
                        "row": 0,
                        "width": 4,
                        "height": 3,
                        "contextGroup": None,
                        "settingsJson": "{}",
                    }
                ],
            }
        ]

    monkeypatch.setattr(
        runtime,
        "_load_workspaces",
        fake_workspaces,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "GET",
            "/api/v2/control-plane/workspaces",
        )

        response = connection.getresponse()
        payload = json.loads(response.read())

        assert response.status == 200
        assert payload[0]["id"] == "desk"
        assert payload[0]["activeLayoutVersion"] == 1
        assert payload[0]["widgets"][0]["column"] == 0
        assert payload[0]["widgets"][0]["row"] == 0
        assert (
            payload[0]["widgets"][0]["settingsJson"]
            == "{}"
        )

        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


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

def test_control_plane_runtime_serves_workspace_save(
    monkeypatch,
) -> None:
    async def fake_save(payload):
        assert payload["workspaceId"] == "desk"
        assert payload["baseVersion"] == 1

        return {
            "id": "desk",
            "name": "Desk",
            "locale": "ru",
            "theme": "dark",
            "activeLayoutVersion": 2,
            "widgets": [],
        }

    monkeypatch.setattr(
        runtime,
        "_save_workspace_payload",
        fake_save,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        body = json.dumps(
            {
                "workspaceId": "desk",
                "baseVersion": 1,
                "widgets": [],
            }
        )

        connection.request(
            "POST",
            "/api/v2/control-plane/workspaces/save",
            body=body,
            headers={
                "content-type": "application/json"
            },
        )

        response = connection.getresponse()
        payload = json.loads(
            response.read()
        )

        assert response.status == 200
        assert payload["id"] == "desk"
        assert (
            payload["activeLayoutVersion"]
            == 2
        )

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_control_plane_runtime_maps_stale_workspace_save_to_409(
    monkeypatch,
) -> None:
    async def fake_save(payload):
        raise runtime.WorkspaceSaveConflict(
            "stale"
        )

    monkeypatch.setattr(
        runtime,
        "_save_workspace_payload",
        fake_save,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "POST",
            "/api/v2/control-plane/workspaces/save",
            body=json.dumps(
                {
                    "workspaceId": "desk",
                    "baseVersion": 1,
                    "widgets": [],
                }
            ),
            headers={
                "content-type": "application/json"
            },
        )

        response = connection.getresponse()
        payload = json.loads(
            response.read()
        )

        assert response.status == 409
        assert (
            payload["code"]
            == "WORKSPACE_VERSION_CONFLICT"
        )

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
def test_control_plane_runtime_serves_blank_workspace_create(
    monkeypatch,
) -> None:
    async def fake_create(payload):
        assert payload == {
            "name": "Research",
            "locale": "ru",
            "theme": "dark",
        }

        return {
            "id": "ws-created",
            "name": "Research",
            "locale": "ru",
            "theme": "dark",
            "activeLayoutVersion": 1,
            "widgets": [],
        }

    monkeypatch.setattr(
        runtime,
        "_create_blank_workspace_payload",
        fake_create,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "POST",
            "/api/v2/control-plane/workspaces",
            body=json.dumps(
                {
                    "name": "Research",
                    "locale": "ru",
                    "theme": "dark",
                }
            ),
            headers={
                "content-type": "application/json"
            },
        )

        response = connection.getresponse()

        payload = json.loads(
            response.read()
        )

        assert response.status == 201
        assert payload["id"] == "ws-created"
        assert payload["name"] == "Research"

        assert (
            payload["activeLayoutVersion"]
            == 1
        )

        assert payload["widgets"] == []

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
def test_control_plane_runtime_serves_workspace_restore(
    monkeypatch,
) -> None:
    async def fake_restore(payload):
        assert payload == {
            "workspaceId": "desk",
            "baseVersion": 2,
            "targetVersion": 1,
        }

        return {
            "id": "desk",
            "name": "Desk",
            "locale": "ru",
            "theme": "dark",
            "activeLayoutVersion": 3,
            "widgets": [],
        }

    monkeypatch.setattr(
        runtime,
        "_restore_workspace_payload",
        fake_restore,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "POST",
            "/api/v2/control-plane/workspaces/restore",
            body=json.dumps(
                {
                    "workspaceId": "desk",
                    "baseVersion": 2,
                    "targetVersion": 1,
                }
            ),
            headers={
                "content-type": "application/json"
            },
        )

        response = connection.getresponse()

        payload = json.loads(
            response.read()
        )

        assert response.status == 200

        assert (
            payload["activeLayoutVersion"]
            == 3
        )

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_control_plane_runtime_maps_stale_workspace_restore_to_409(
    monkeypatch,
) -> None:
    async def fake_restore(payload):
        raise runtime.WorkspaceRestoreConflict(
            "stale"
        )

    monkeypatch.setattr(
        runtime,
        "_restore_workspace_payload",
        fake_restore,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.ControlPlaneHandler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "POST",
            "/api/v2/control-plane/workspaces/restore",
            body=json.dumps(
                {
                    "workspaceId": "desk",
                    "baseVersion": 2,
                    "targetVersion": 1,
                }
            ),
            headers={
                "content-type": "application/json"
            },
        )

        response = connection.getresponse()

        payload = json.loads(
            response.read()
        )

        assert response.status == 409

        assert (
            payload["code"]
            == "WORKSPACE_VERSION_CONFLICT"
        )

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
