"""Read-only Control Plane runtime backed by canonical V2 persistence.

This is an off-production review/runtime composition root. Identity is supplied
by server-side configuration because the production HTTP authentication/JWT
boundary is not yet integrated. Only GET endpoints are exposed here.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from infra.persistence.repositories.control_plane import ControlPlaneRepository
from infra.persistence.repositories.control_plane_read import ControlPlaneReadRepository
from infra.persistence.session import create_persistence_engine, create_session_factory

WEB_ROOT = Path(__file__).resolve().parents[1] / "apps" / "web"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18082


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


async def _load_overview() -> dict[str, Any]:
    database_url = _required_env("NEXUS_V2_DATABASE_URL")
    workspace_id = _required_env("NEXUS_CONTROL_PLANE_WORKSPACE_ID")
    user_id = int(_required_env("NEXUS_CONTROL_PLANE_USER_ID"))
    if user_id <= 0:
        raise RuntimeError("NEXUS_CONTROL_PLANE_USER_ID must be positive")

    engine = create_persistence_engine(database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            value = await ControlPlaneReadRepository(session).overview(
                workspace_id=workspace_id,
                user_id=user_id,
            )
            return asdict(value)
    finally:
        await engine.dispose()


def _workspace_projection(workspace: Any, layout: Any) -> dict[str, Any]:
    widgets: list[dict[str, Any]] = []

    for item in layout.widgets:
        placement = item.placement
        widgets.append(
            {
                "id": placement.instance_id,
                "key": placement.widget_key,
                "widgetVersion": placement.widget_version,
                "column": placement.column,
                "row": placement.row,
                "width": placement.size.columns,
                "height": placement.size.rows,
                "contextGroup": placement.context_group,
                "settingsJson": item.settings_json,
            }
        )

    return {
        "id": workspace.user_workspace_id,
        "name": workspace.name,
        "locale": workspace.locale.value,
        "theme": workspace.theme.value,
        "activeLayoutVersion": workspace.active_layout_version,
        "widgets": widgets,
    }


async def _load_workspaces() -> list[dict[str, Any]]:
    database_url = _required_env("NEXUS_V2_DATABASE_URL")
    tenant_workspace_id = _required_env("NEXUS_CONTROL_PLANE_WORKSPACE_ID")
    user_id = int(_required_env("NEXUS_CONTROL_PLANE_USER_ID"))

    if user_id <= 0:
        raise RuntimeError("NEXUS_CONTROL_PLANE_USER_ID must be positive")

    engine = create_persistence_engine(database_url)
    factory = create_session_factory(engine)

    try:
        async with factory() as session:
            repository = ControlPlaneRepository(session)

            workspaces = await repository.list_user_workspaces(
                tenant_workspace_id=tenant_workspace_id,
                user_id=user_id,
            )

            result: list[dict[str, Any]] = []

            for workspace in workspaces:
                layout = await repository.get_layout(
                    tenant_workspace_id=tenant_workspace_id,
                    user_id=user_id,
                    user_workspace_id=workspace.user_workspace_id,
                    version=workspace.active_layout_version,
                )

                if layout is None:
                    raise RuntimeError(
                        "active workspace layout unavailable"
                    )

                result.append(_workspace_projection(workspace, layout))

            return result
    finally:
        await engine.dispose()


class ControlPlaneHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-Control-Plane"

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/v2/control-plane/overview":
            self._overview()
            return
        if path == "/api/v2/control-plane/workspaces":
            self._workspaces()
            return
        if path == "/health":
            self._json(
                HTTPStatus.OK,
                {
                    "service": "nexus-v2-control-plane",
                    "status": "healthy",
                    "authority": "READ_ONLY",
                    "production_authority": False,
                },
            )
            return
        self._static(path)


    def _workspaces(self) -> None:
        try:
            payload = asyncio.run(_load_workspaces())
        except PermissionError:
            self._json(
                HTTPStatus.FORBIDDEN,
                {"code": "FORBIDDEN", "message": "workspace access denied"},
            )
            return
        except (RuntimeError, ValueError):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": "CONTROL_PLANE_UNAVAILABLE",
                    "message": "workspace read model unavailable",
                },
            )
            return

        self._json(HTTPStatus.OK, payload)

    def _overview(self) -> None:
        try:
            payload = asyncio.run(_load_overview())
        except PermissionError:
            self._json(
                HTTPStatus.FORBIDDEN,
                {"code": "FORBIDDEN", "message": "workspace access denied"},
            )
            return
        except (RuntimeError, ValueError):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": "CONTROL_PLANE_UNAVAILABLE",
                    "message": "read model unavailable",
                },
            )
            return
        self._json(HTTPStatus.OK, payload)

    def _static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        try:
            candidate.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self._json(
                HTTPStatus.NOT_FOUND,
                {"code": "NOT_FOUND", "message": "not found"},
            )
            return
        if not candidate.is_file():
            self._json(
                HTTPStatus.NOT_FOUND,
                {"code": "NOT_FOUND", "message": "not found"},
            )
            return
        payload = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", content_type)
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: HTTPStatus, value: object) -> None:
        payload = json.dumps(
            value,
            default=_json_default,
            sort_keys=True,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    _required_env("NEXUS_V2_DATABASE_URL")
    _required_env("NEXUS_CONTROL_PLANE_WORKSPACE_ID")
    _required_env("NEXUS_CONTROL_PLANE_USER_ID")
    host = os.environ.get("NEXUS_CONTROL_PLANE_HOST", DEFAULT_HOST)
    port = int(os.environ.get("NEXUS_CONTROL_PLANE_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), ControlPlaneHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
