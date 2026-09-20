from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import scripts.simulated_server_runtime as runtime
from scripts.run_nexus_simulated import run


def _request(path: str) -> tuple[int, dict[str, object]]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), runtime.RuntimeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
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
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_status_exposes_verified_simulation_evidence() -> None:
    import asyncio
    runtime.RUNTIME_EVIDENCE = asyncio.run(run())
    status, payload = _request("/status")
    assert status == 200
    assert payload["status"] == "RUNNING"
    assert payload["mode"] == "SIMULATION_ONLY"
    assert payload["startup_reconciliation"] == "MATCHED"
    assert payload["portfolio_risk"] == "APPROVED"
    assert payload["post_execution_reconciliation"] == "MATCHED"
    assert payload["real_exchange_writes"] == 0
    assert payload["production_authority"] is False


def test_ready_requires_runtime_evidence() -> None:
    runtime.RUNTIME_EVIDENCE = {}
    status, payload = _request("/ready")
    assert status == 503
    assert payload["ready"] is False
