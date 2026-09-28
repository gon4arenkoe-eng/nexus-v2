"""Read-only Control Plane runtime backed by canonical V2 persistence.

This is an off-production review/runtime composition root. Identity is supplied
by server-side configuration because the production HTTP authentication/JWT
boundary is not yet integrated. Only GET endpoints are exposed here.
"""

from __future__ import annotations

from datetime import UTC, datetime

from infra.persistence.application.control_plane_workspace import (
    load_widget_availability,
)

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from infra.persistence.application.control_plane_workspace import (
    WorkspaceCreateConflict,
    WorkspaceCreateInvalid,
    WorkspaceRestoreConflict,
    WorkspaceRestoreInvalid,
    WorkspaceRestoreNotFound,
    WorkspaceRestoreStateError,
    WorkspaceSaveConflict,
    WorkspaceSaveInvalid,
    WorkspaceSaveNotFound,
    WorkspaceSaveStateError,
    create_blank_workspace,
    restore_workspace_layout,
    save_existing_workspace,
    WorkspaceTemplateCreateConflict,
    WorkspaceTemplateCreateInvalid,
    WorkspaceTemplateCreateNotFound,
    WorkspaceTemplateCreateStateError,
    create_workspace_from_curated_template,
    list_curated_workspace_templates,
)
from infra.persistence.application.control_plane_workspace import (
    WorkspaceContextInvalid,
    WorkspaceContextNotFound,
    WorkspaceContextStateError,
    publish_workspace_context,
)
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




async def _create_blank_workspace_payload(
    payload: object,
) -> dict[str, Any]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )

    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )

    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID "
            "must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )

    factory = create_session_factory(
        engine
    )

    try:
        workspace, layout = (
            await create_blank_workspace(
                session_factory=factory,
                tenant_workspace_id=(
                    tenant_workspace_id
                ),
                user_id=user_id,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )

        return _workspace_projection(
            workspace,
            layout,
        )

    finally:
        await engine.dispose()



async def _restore_workspace_payload(
    payload: object,
) -> dict[str, Any]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )

    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )

    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID "
            "must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )

    factory = create_session_factory(
        engine
    )

    try:
        workspace, layout = (
            await restore_workspace_layout(
                session_factory=factory,
                tenant_workspace_id=(
                    tenant_workspace_id
                ),
                user_id=user_id,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )

        return _workspace_projection(
            workspace,
            layout,
        )

    finally:
        await engine.dispose()



def _workspace_template_projection(
    template: Any,
) -> dict[str, Any]:
    return {
        "key": template.template_key,
        "version": template.version,
        "titleKey": template.title_key,
        "widgetCount": len(
            template.widgets
        ),
    }


async def _workspace_templates_payload(
) -> list[dict[str, Any]]:
    now = datetime.now(UTC)

    return [
        _workspace_template_projection(
            template
        )
        for template in (
            list_curated_workspace_templates(
                created_at=now
            )
        )
    ]


async def _create_workspace_from_template_payload(
    payload: object,
) -> dict[str, Any]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )

    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )

    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID "
            "must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )

    factory = create_session_factory(
        engine
    )

    try:
        workspace, layout, _template = (
            await create_workspace_from_curated_template(
                session_factory=factory,
                tenant_workspace_id=(
                    tenant_workspace_id
                ),
                user_id=user_id,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )

        return _workspace_projection(
            workspace,
            layout,
        )

    finally:
        await engine.dispose()


async def _save_workspace_payload(
    payload: object,
) -> dict[str, Any]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )
    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )
    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )
    factory = create_session_factory(engine)

    try:
        workspace, layout = (
            await save_existing_workspace(
                session_factory=factory,
                tenant_workspace_id=tenant_workspace_id,
                user_id=user_id,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )

        return _workspace_projection(
            workspace,
            layout,
        )
    finally:
        await engine.dispose()


async def _publish_context_payload(
    payload: object,
) -> tuple[dict[str, object], ...]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )

    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )

    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID "
            "must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )

    factory = create_session_factory(
        engine
    )

    try:
        return await publish_workspace_context(
            session_factory=factory,
            tenant_workspace_id=tenant_workspace_id,
            user_id=user_id,
            payload=payload,
        )
    finally:
        await engine.dispose()


async def _load_widget_availability_payload(
) -> dict[str, object]:
    database_url = _required_env(
        "NEXUS_V2_DATABASE_URL"
    )

    tenant_workspace_id = _required_env(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID"
    )

    user_id = int(
        _required_env(
            "NEXUS_CONTROL_PLANE_USER_ID"
        )
    )

    if user_id <= 0:
        raise RuntimeError(
            "NEXUS_CONTROL_PLANE_USER_ID "
            "must be positive"
        )

    engine = create_persistence_engine(
        database_url
    )

    factory = create_session_factory(
        engine
    )

    try:
        return await load_widget_availability(
            session_factory=factory,
            tenant_workspace_id=(
                tenant_workspace_id
            ),
            user_id=user_id,
            now=datetime.now(UTC),
        )
    finally:
        await engine.dispose()


class ControlPlaneHandler(BaseHTTPRequestHandler):
    server_version = "NEXUS-V2-Control-Plane"


    def do_POST(self) -> None:
        path = urlsplit(self.path).path

        if path == "/api/v2/control-plane/context":
            self._publish_context()
            return


        if path == "/api/v2/control-plane/workspaces/from-template":
            self._create_workspace_from_template()
            return


        if path == "/api/v2/control-plane/workspaces":
            self._create_workspace()
            return


        if path == "/api/v2/control-plane/workspaces/restore":
            self._restore_workspace()
            return


        if (
            path
            == "/api/v2/control-plane/workspaces/save"
        ):
            self._save_workspace()
            return

        self._json(
            HTTPStatus.NOT_FOUND,
            {
                "code": "NOT_FOUND",
                "message": "endpoint not found",
            },
        )

    def _publish_context(self) -> None:
        try:
            request = self._read_json_body()

        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "invalid context request"
                    ),
                },
            )
            return

        try:
            deliveries = asyncio.run(
                _publish_context_payload(
                    request
                )
            )

        except WorkspaceContextInvalid:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_CONTEXT_UPDATE",
                    "message": (
                        "context update is invalid"
                    ),
                },
            )
            return

        except WorkspaceContextNotFound:
            self._json(
                HTTPStatus.NOT_FOUND,
                {
                    "code": "WORKSPACE_NOT_FOUND",
                    "message": "workspace unavailable",
                },
            )
            return

        except WorkspaceContextStateError:
            self._json(
                HTTPStatus.CONFLICT,
                {
                    "code": "WORKSPACE_STATE_CONFLICT",
                    "message": (
                        "active workspace layout "
                        "is unavailable"
                    ),
                },
            )
            return

        except (
            RuntimeError,
            ValueError,
        ):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": "CONTROL_PLANE_UNAVAILABLE",
                    "message": (
                        "context service unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.OK,
            {
                "deliveries": list(
                    deliveries
                )
            },
        )


    def _widget_availability(self) -> None:
        try:
            payload = asyncio.run(
                _load_widget_availability_payload()
            )

        except (
            RuntimeError,
            ValueError,
        ):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "CONTROL_PLANE_UNAVAILABLE"
                    ),
                    "message": (
                        "widget availability "
                        "service unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.OK,
            payload,
        )


    def do_GET(self) -> None:
        path = urlsplit(self.path).path

        if path == "/api/v2/control-plane/workspace-templates":
            self._workspace_templates()
            return
        if path == "/api/v2/control-plane/widget-availability":
            self._widget_availability()
            return

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
                    "authority": "PRESENTATION_WRITE_ONLY",
                    "production_authority": False,
                },
            )
            return
        self._static(path)



    def _read_json_body(
        self,
    ) -> dict[str, Any]:
        raw_length = self.headers.get(
            "content-length",
            "",
        ).strip()

        if not raw_length:
            raise ValueError(
                "content-length is required"
            )

        length = int(raw_length)

        if length < 1 or length > 1_000_000:
            raise ValueError(
                "invalid request size"
            )

        raw = self.rfile.read(length)

        value = json.loads(
            raw.decode("utf-8")
        )

        if not isinstance(value, dict):
            raise ValueError(
                "JSON body must be an object"
            )

        return value



    def _workspace_templates(self) -> None:
        try:
            payload = asyncio.run(
                _workspace_templates_payload()
            )

        except (
            WorkspaceTemplateCreateStateError,
            RuntimeError,
            ValueError,
        ):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "WORKSPACE_TEMPLATE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace template catalog "
                        "unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.OK,
            payload,
        )


    def _create_workspace_from_template(
        self,
    ) -> None:
        try:
            request = self._read_json_body()

        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "invalid template workspace "
                        "create request"
                    ),
                },
            )
            return

        try:
            payload = asyncio.run(
                _create_workspace_from_template_payload(
                    request
                )
            )

        except WorkspaceTemplateCreateInvalid:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": (
                        "INVALID_WORKSPACE_TEMPLATE_CREATE"
                    ),
                    "message": (
                        "template workspace create "
                        "request is invalid"
                    ),
                },
            )
            return

        except WorkspaceTemplateCreateNotFound:
            self._json(
                HTTPStatus.NOT_FOUND,
                {
                    "code": (
                        "WORKSPACE_TEMPLATE_NOT_FOUND"
                    ),
                    "message": (
                        "curated workspace template "
                        "unavailable"
                    ),
                },
            )
            return

        except WorkspaceTemplateCreateConflict:
            self._json(
                HTTPStatus.CONFLICT,
                {
                    "code": (
                        "WORKSPACE_CREATE_CONFLICT"
                    ),
                    "message": (
                        "workspace identity conflict"
                    ),
                },
            )
            return

        except WorkspaceTemplateCreateStateError:
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "WORKSPACE_TEMPLATE_STATE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace template state "
                        "unavailable"
                    ),
                },
            )
            return

        except (
            RuntimeError,
            ValueError,
        ):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "CONTROL_PLANE_UNAVAILABLE"
                    ),
                    "message": (
                        "template workspace creation "
                        "unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.CREATED,
            payload,
        )


    def _create_workspace(self) -> None:
        try:
            request = self._read_json_body()

        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "invalid workspace "
                        "create request"
                    ),
                },
            )
            return

        try:
            payload = asyncio.run(
                _create_blank_workspace_payload(
                    request
                )
            )

        except WorkspaceCreateInvalid:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": (
                        "INVALID_WORKSPACE_CREATE"
                    ),
                    "message": (
                        "workspace create "
                        "request is invalid"
                    ),
                },
            )
            return

        except WorkspaceCreateConflict:
            self._json(
                HTTPStatus.CONFLICT,
                {
                    "code": (
                        "WORKSPACE_CREATE_CONFLICT"
                    ),
                    "message": (
                        "workspace identity conflict"
                    ),
                },
            )
            return

        except (RuntimeError, ValueError):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "CONTROL_PLANE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace creation "
                        "unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.CREATED,
            payload,
        )



    def _restore_workspace(self) -> None:
        try:
            request = self._read_json_body()

        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "invalid workspace "
                        "restore request"
                    ),
                },
            )
            return

        try:
            payload = asyncio.run(
                _restore_workspace_payload(
                    request
                )
            )

        except WorkspaceRestoreInvalid:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": (
                        "INVALID_WORKSPACE_RESTORE"
                    ),
                    "message": (
                        "workspace restore "
                        "request is invalid"
                    ),
                },
            )
            return

        except WorkspaceRestoreNotFound:
            self._json(
                HTTPStatus.NOT_FOUND,
                {
                    "code": (
                        "WORKSPACE_RESTORE_NOT_FOUND"
                    ),
                    "message": (
                        "workspace or restore "
                        "target unavailable"
                    ),
                },
            )
            return

        except WorkspaceRestoreConflict:
            self._json(
                HTTPStatus.CONFLICT,
                {
                    "code": (
                        "WORKSPACE_VERSION_CONFLICT"
                    ),
                    "message": (
                        "workspace version changed"
                    ),
                },
            )
            return

        except WorkspaceRestoreStateError:
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "WORKSPACE_STATE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace state unavailable"
                    ),
                },
            )
            return

        except (RuntimeError, ValueError):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "CONTROL_PLANE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace restore unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.OK,
            payload,
        )


    def _save_workspace(self) -> None:
        try:
            request = self._read_json_body()
        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "invalid workspace save request"
                    ),
                },
            )
            return

        try:
            payload = asyncio.run(
                _save_workspace_payload(request)
            )

        except WorkspaceSaveInvalid:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "code": (
                        "INVALID_WORKSPACE_LAYOUT"
                    ),
                    "message": (
                        "workspace layout is invalid"
                    ),
                },
            )
            return

        except WorkspaceSaveNotFound:
            self._json(
                HTTPStatus.NOT_FOUND,
                {
                    "code": "WORKSPACE_NOT_FOUND",
                    "message": (
                        "workspace unavailable"
                    ),
                },
            )
            return

        except WorkspaceSaveConflict:
            self._json(
                HTTPStatus.CONFLICT,
                {
                    "code": (
                        "WORKSPACE_VERSION_CONFLICT"
                    ),
                    "message": (
                        "workspace version changed"
                    ),
                },
            )
            return

        except WorkspaceSaveStateError:
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "WORKSPACE_STATE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace state unavailable"
                    ),
                },
            )
            return

        except (RuntimeError, ValueError):
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "code": (
                        "CONTROL_PLANE_UNAVAILABLE"
                    ),
                    "message": (
                        "workspace persistence unavailable"
                    ),
                },
            )
            return

        self._json(
            HTTPStatus.OK,
            payload,
        )


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
