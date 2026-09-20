from __future__ import annotations

import inspect
import json
import os
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import scripts.target_server_runtime as runtime


def _request(path: str) -> tuple[int, dict[str, object]]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        runtime.RuntimeHandler,
    )
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address
        connection = HTTPConnection(host, port, timeout=2)
        connection.request("GET", path)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_health_is_read_only_and_healthy() -> None:
    os.environ["NEXUS_RUNTIME_MODE"] = "test"

    status, payload = _request("/health")

    assert status == 200
    assert payload == {
        "ready": True,
        "runtime_mode": "test",
        "service": "nexus-v2-core",
        "status": "healthy",
    }


def test_ready_is_read_only_and_ready() -> None:
    os.environ["NEXUS_RUNTIME_MODE"] = "test"

    status, payload = _request("/ready")

    assert status == 200
    assert payload["ready"] is True
    assert payload["status"] == "ready"


def test_unknown_route_fails_closed() -> None:
    status, payload = _request("/unknown")

    assert status == 404
    assert payload["code"] == "NOT_FOUND"


def test_runtime_has_no_db_venue_or_execution_authority() -> None:
    source = inspect.getsource(runtime).lower()

    forbidden = (
        "sqlalchemy",
        "infra.persistence",
        "venueadapter",
        "submit_order(",
        "cancel_order(",
        "executioncoordinator",
        "api_key",
        "api_secret",
        "database_url",
    )

    assert not any(item.lower() in source for item in forbidden)


def test_runtime_composition_is_fail_closed() -> None:
    runtime.validate_runtime_composition()
