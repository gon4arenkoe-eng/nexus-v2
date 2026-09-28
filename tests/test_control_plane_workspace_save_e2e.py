from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infra.persistence.base import PersistenceBase
from infra.persistence.repositories.control_plane import (
    ControlPlaneRepository,
)
from packages.contracts.control_plane import (
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetInstance,
    WorkspaceLayoutVersion,
)
from packages.contracts.workspace import (
    WidgetPlacement,
    WidgetSize,
)
import scripts.control_plane_readonly_runtime as runtime


pytest.importorskip("aiosqlite")


NOW = datetime(
    2026,
    9,
    28,
    12,
    0,
    tzinfo=UTC,
)


def _seed_widget() -> WidgetInstance:
    return WidgetInstance(
        placement=WidgetPlacement(
            instance_id="positions-1",
            widget_key="portfolio.positions",
            widget_version=1,
            column=0,
            row=0,
            size=WidgetSize(4, 3),
            context_group="market",
        ),
        settings_json='{"timeframe":"1H"}',
    )


async def _prepare_database(
    database_url: str,
) -> None:
    engine = create_async_engine(
        database_url,
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                PersistenceBase.metadata.create_all
            )

        factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with factory() as session:
            repository = ControlPlaneRepository(
                session
            )

            await repository.put_user_workspace(
                UserWorkspace(
                    tenant_workspace_id="tenant-a",
                    user_workspace_id="desk",
                    user_id=7,
                    name="Desk",
                    locale=SupportedLocale.RUSSIAN,
                    theme=ThemePreference.DARK,
                    active_layout_version=1,
                    created_at=NOW,
                    updated_at=NOW,
                )
            )

            await repository.append_layout(
                WorkspaceLayoutVersion(
                    tenant_workspace_id="tenant-a",
                    user_workspace_id="desk",
                    user_id=7,
                    version=1,
                    widgets=(_seed_widget(),),
                    created_at=NOW,
                )
            )

            await session.commit()

    finally:
        await engine.dispose()


async def _read_database(
    database_url: str,
):
    engine = create_async_engine(
        database_url,
    )

    try:
        factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with factory() as session:
            repository = ControlPlaneRepository(
                session
            )

            workspace = (
                await repository.get_user_workspace(
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    user_workspace_id="desk",
                )
            )

            version_one = (
                await repository.get_layout(
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    user_workspace_id="desk",
                    version=1,
                )
            )

            version_two = (
                await repository.get_layout(
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    user_workspace_id="desk",
                    version=2,
                )
            )

            version_three = (
                await repository.get_layout(
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    user_workspace_id="desk",
                    version=3,
                )
            )

            return (
                workspace,
                version_one,
                version_two,
                version_three,
            )

    finally:
        await engine.dispose()


def _http_json(
    *,
    host: str,
    port: int,
    method: str,
    path: str,
    payload: object | None = None,
) -> tuple[int, object]:
    connection = HTTPConnection(
        host,
        port,
        timeout=5,
    )

    try:
        body = None
        headers: dict[str, str] = {}

        if payload is not None:
            body = json.dumps(payload)
            headers["content-type"] = (
                "application/json"
            )

        connection.request(
            method,
            path,
            body=body,
            headers=headers,
        )

        response = connection.getresponse()
        raw = response.read()

        value = (
            json.loads(raw)
            if raw
            else None
        )

        return response.status, value

    finally:
        connection.close()


def test_workspace_save_roundtrip_through_real_http_runtime_and_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = (
        tmp_path
        / "control-plane-save-e2e.sqlite3"
    )

    database_url = (
        "sqlite+aiosqlite:///"
        + db_path.as_posix()
    )

    asyncio.run(
        _prepare_database(database_url)
    )

    monkeypatch.setenv(
        "NEXUS_V2_DATABASE_URL",
        database_url,
    )
    monkeypatch.setenv(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID",
        "tenant-a",
    )
    monkeypatch.setenv(
        "NEXUS_CONTROL_PLANE_USER_ID",
        "7",
    )

    web_source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "/api/v2/control-plane/workspaces/save"
        in web_source
    )
    assert "method:'POST'" in web_source
    assert "canonicalWorkspaceSavePayload()" in web_source

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

        before_status, before = _http_json(
            host=host,
            port=port,
            method="GET",
            path="/api/v2/control-plane/workspaces",
        )

        assert before_status == 200
        assert isinstance(before, list)
        assert len(before) == 1

        assert before[0]["id"] == "desk"
        assert (
            before[0]["activeLayoutVersion"]
            == 1
        )

        assert (
            before[0]["widgets"][0]["column"]
            == 0
        )

        save_payload = {
            "workspaceId": "desk",
            "baseVersion": 1,
            "widgets": [
                {
                    "id": "positions-1",
                    "key": "portfolio.positions",
                    "widgetVersion": 1,
                    "column": 2,
                    "row": 1,
                    "width": 4,
                    "height": 3,
                    "contextGroup": "market",
                    "settingsJson": (
                        '{"timeframe":"4H"}'
                    ),
                }
            ],
        }

        save_status, saved = _http_json(
            host=host,
            port=port,
            method="POST",
            path=(
                "/api/v2/control-plane/"
                "workspaces/save"
            ),
            payload=save_payload,
        )

        assert save_status == 200
        assert isinstance(saved, dict)

        assert saved["id"] == "desk"
        assert (
            saved["activeLayoutVersion"]
            == 2
        )

        assert (
            saved["widgets"][0]["column"]
            == 2
        )
        assert (
            saved["widgets"][0]["row"]
            == 1
        )
        assert (
            saved["widgets"][0]["settingsJson"]
            == '{"timeframe":"4H"}'
        )

        reload_status, reloaded = _http_json(
            host=host,
            port=port,
            method="GET",
            path="/api/v2/control-plane/workspaces",
        )

        assert reload_status == 200
        assert isinstance(reloaded, list)
        assert len(reloaded) == 1

        assert (
            reloaded[0]["activeLayoutVersion"]
            == 2
        )

        assert (
            reloaded[0]["widgets"][0]["column"]
            == 2
        )
        assert (
            reloaded[0]["widgets"][0]["row"]
            == 1
        )
        assert (
            reloaded[0]["widgets"][0]["settingsJson"]
            == '{"timeframe":"4H"}'
        )

        stale_status, stale = _http_json(
            host=host,
            port=port,
            method="POST",
            path=(
                "/api/v2/control-plane/"
                "workspaces/save"
            ),
            payload=save_payload,
        )

        assert stale_status == 409
        assert isinstance(stale, dict)
        assert (
            stale["code"]
            == "WORKSPACE_VERSION_CONFLICT"
        )

        final_status, final_reload = _http_json(
            host=host,
            port=port,
            method="GET",
            path="/api/v2/control-plane/workspaces",
        )

        assert final_status == 200

        assert (
            final_reload[0]["activeLayoutVersion"]
            == 2
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (
        workspace,
        version_one,
        version_two,
        version_three,
    ) = asyncio.run(
        _read_database(database_url)
    )

    assert workspace is not None
    assert (
        workspace.active_layout_version
        == 2
    )

    assert version_one is not None
    assert version_one.version == 1
    assert (
        version_one.widgets[0]
        .placement.column
        == 0
    )
    assert (
        version_one.widgets[0].settings_json
        == '{"timeframe":"1H"}'
    )

    assert version_two is not None
    assert version_two.version == 2
    assert version_two.source_version == 1

    assert (
        version_two.widgets[0]
        .placement.column
        == 2
    )
    assert (
        version_two.widgets[0]
        .placement.row
        == 1
    )
    assert (
        version_two.widgets[0].settings_json
        == '{"timeframe":"4H"}'
    )

    assert version_three is None
def test_blank_workspace_create_roundtrip_through_real_http_runtime_and_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = (
        tmp_path
        / "control-plane-create-e2e.sqlite3"
    )

    database_url = (
        "sqlite+aiosqlite:///"
        + db_path.as_posix()
    )

    asyncio.run(
        _prepare_database(
            database_url
        )
    )

    monkeypatch.setenv(
        "NEXUS_V2_DATABASE_URL",
        database_url,
    )

    monkeypatch.setenv(
        "NEXUS_CONTROL_PLANE_WORKSPACE_ID",
        "tenant-a",
    )

    monkeypatch.setenv(
        "NEXUS_CONTROL_PLANE_USER_ID",
        "7",
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

        create_status, created = _http_json(
            host=host,
            port=port,
            method="POST",
            path=(
                "/api/v2/control-plane/"
                "workspaces"
            ),
            payload={
                "name": "Research",
                "locale": "ru",
                "theme": "dark",
            },
        )

        assert create_status == 201
        assert isinstance(created, dict)

        created_id = created["id"]

        assert isinstance(created_id, str)

        assert created_id.startswith(
            "ws-"
        )

        assert created["name"] == "Research"

        assert (
            created["activeLayoutVersion"]
            == 1
        )

        assert created["widgets"] == []

        reload_status, reloaded = _http_json(
            host=host,
            port=port,
            method="GET",
            path=(
                "/api/v2/control-plane/"
                "workspaces"
            ),
        )

        assert reload_status == 200
        assert isinstance(reloaded, list)

        by_id = {
            item["id"]: item
            for item in reloaded
        }

        assert "desk" in by_id
        assert created_id in by_id

        assert (
            by_id[created_id]["name"]
            == "Research"
        )

        assert (
            by_id[created_id][
                "activeLayoutVersion"
            ]
            == 1
        )

        assert (
            by_id[created_id]["widgets"]
            == []
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    async def read_created():
        engine = create_async_engine(
            database_url
        )

        try:
            factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                workspace = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            created_id
                        ),
                    )
                )

                layout = (
                    await repository.get_layout(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            created_id
                        ),
                        version=1,
                    )
                )

                wrong_user = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=8,
                        user_workspace_id=(
                            created_id
                        ),
                    )
                )

                return (
                    workspace,
                    layout,
                    wrong_user,
                )

        finally:
            await engine.dispose()

    (
        workspace,
        layout,
        wrong_user,
    ) = asyncio.run(
        read_created()
    )

    assert workspace is not None
    assert workspace.name == "Research"
    assert workspace.user_id == 7

    assert (
        workspace.active_layout_version
        == 1
    )

    assert layout is not None
    assert layout.version == 1
    assert layout.source_version is None
    assert layout.widgets == ()

    assert wrong_user is None
