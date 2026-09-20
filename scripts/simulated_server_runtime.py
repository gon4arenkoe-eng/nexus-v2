"""Long-running fail-closed NEXUS V2 server runtime in simulation-only mode."""
from __future__ import annotations

import asyncio
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from scripts.run_nexus_simulated import run

DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8080
RUNTIME_EVIDENCE: dict[str, object] = {}


def _json(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-SIM"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._respond(HTTPStatus.OK, _json({
                "service": "nexus-v2-core",
                "status": "healthy",
                "ready": bool(RUNTIME_EVIDENCE),
                "runtime_mode": "SIMULATION_ONLY",
            }))
            return
        if self.path == "/ready":
            ready = bool(RUNTIME_EVIDENCE) and RUNTIME_EVIDENCE.get("status") == "RUNNING"
            self._respond(HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE, _json({
                "service": "nexus-v2-core",
                "status": "ready" if ready else "not_ready",
                "ready": ready,
                "runtime_mode": "SIMULATION_ONLY",
            }))
            return
        if self.path == "/status":
            self._respond(HTTPStatus.OK, _json(dict(RUNTIME_EVIDENCE)))
            return
        self._respond(HTTPStatus.NOT_FOUND, _json({"code": "NOT_FOUND", "message": "not found"}))

    def _respond(self, status: HTTPStatus, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    global RUNTIME_EVIDENCE
    RUNTIME_EVIDENCE = asyncio.run(run())
    if RUNTIME_EVIDENCE.get("production_authority") is not False:
        raise RuntimeError("simulation runtime unexpectedly has production authority")
    if RUNTIME_EVIDENCE.get("real_exchange_writes") != 0:
        raise RuntimeError("simulation runtime unexpectedly performed real exchange writes")

    host = os.environ.get("NEXUS_RUNTIME_HOST", DEFAULT_HOST)
    port = int(os.environ.get("NEXUS_RUNTIME_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), RuntimeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
