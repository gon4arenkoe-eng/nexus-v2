"""Minimal fail-closed NEXUS V2 target-server runtime foundation."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from apps.core.application.control_plane import SafetyPresentationService
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
)

DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8080


def _payload(*, status: str, ready: bool) -> bytes:
    return json.dumps(
        {
            "service": "nexus-v2-core",
            "status": status,
            "ready": ready,
            "runtime_mode": os.environ.get(
                "NEXUS_RUNTIME_MODE",
                "unknown",
            ),
        },
        sort_keys=True,
    ).encode("utf-8")


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._respond(
                HTTPStatus.OK,
                _payload(status="healthy", ready=True),
            )
            return

        if self.path == "/ready":
            self._respond(
                HTTPStatus.OK,
                _payload(status="ready", ready=True),
            )
            return

        self._respond(
            HTTPStatus.NOT_FOUND,
            json.dumps(
                {"code": "NOT_FOUND", "message": "not found"},
                sort_keys=True,
            ).encode("utf-8"),
        )

    def _respond(
        self,
        status: HTTPStatus,
        payload: bytes,
    ) -> None:
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        return


def validate_runtime_composition() -> None:
    if SafetyPresentationService.layout_can_suppress_safety():
        raise RuntimeError(
            "mandatory safety presentation unexpectedly suppressible"
        )

    if StartupReconciliationActivationGate is None:
        raise RuntimeError(
            "startup reconciliation gate unavailable"
        )


def main() -> int:
    validate_runtime_composition()

    host = os.environ.get("NEXUS_RUNTIME_HOST", DEFAULT_HOST)
    port = int(
        os.environ.get(
            "NEXUS_RUNTIME_PORT",
            str(DEFAULT_PORT),
        )
    )

    server = ThreadingHTTPServer(
        (host, port),
        RuntimeHandler,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
