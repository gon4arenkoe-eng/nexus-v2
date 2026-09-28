from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import infra.persistence.application.control_plane_workspace as service
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


pytest.importorskip("aiosqlite")


NOW = datetime(
    2026,
    9,
    28,
    14,
    0,
    tzinfo=UTC,
)

LATER = datetime(
    2026,
    9,
    28,
    14,
    1,
    tzinfo=UTC,
)

RESTORED_AT = datetime(
    2026,
    9,
    28,
    14,
    2,
    tzinfo=UTC,
)


async def _factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            PersistenceBase.metadata.create_all
        )

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, factory


def _widget(
    *,
    column: int,
    timeframe: str,
) -> WidgetInstance:
    return WidgetInstance(
        placement=WidgetPlacement(
            instance_id="positions-1",
            widget_key="portfolio.positions",
            widget_version=1,
            column=column,
            row=0,
            size=WidgetSize(4, 3),
            context_group="market",
        ),
        settings_json=(
            '{"timeframe":"'
            + timeframe
            + '"}'
        ),
    )


async def _seed(factory) -> None:
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
                widgets=(
                    _widget(
                        column=0,
                        timeframe="1H",
                    ),
                ),
                created_at=NOW,
            )
        )

        await session.commit()


def _save_payload() -> dict[str, object]:
    return {
        "workspaceId": "desk",
        "baseVersion": 1,
        "widgets": [
            {
                "id": "positions-1",
                "key": "portfolio.positions",
                "widgetVersion": 1,
                "column": 2,
                "row": 0,
                "width": 4,
                "height": 3,
                "contextGroup": "market",
                "settingsJson": (
                    '{"timeframe":"4H"}'
                ),
            }
        ],
    }


async def _prepare_v2(factory) -> None:
    await _seed(factory)

    await service.save_existing_workspace(
        session_factory=factory,
        tenant_workspace_id="tenant-a",
        user_id=7,
        payload=_save_payload(),
        created_at=LATER,
    )


def test_restore_workspace_creates_immutable_v3_from_v1() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _prepare_v2(factory)

            workspace, restored = (
                await service.restore_workspace_layout(
                    session_factory=factory,
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    payload={
                        "workspaceId": "desk",
                        "baseVersion": 2,
                        "targetVersion": 1,
                    },
                    created_at=RESTORED_AT,
                )
            )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                versions = []

                for version in (1, 2, 3):
                    versions.append(
                        await repository.get_layout(
                            tenant_workspace_id=(
                                "tenant-a"
                            ),
                            user_id=7,
                            user_workspace_id=(
                                "desk"
                            ),
                            version=version,
                        )
                    )

                current = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            "desk"
                        ),
                    )
                )

            return (
                workspace,
                restored,
                versions,
                current,
            )

        finally:
            await engine.dispose()

    (
        workspace,
        restored,
        versions,
        current,
    ) = asyncio.run(
        scenario()
    )

    v1, v2, v3 = versions

    assert workspace.active_layout_version == 3
    assert restored.version == 3
    assert restored.source_version == 1

    assert v1 is not None
    assert v2 is not None
    assert v3 is not None

    assert v1.version == 1
    assert v2.version == 2
    assert v3.version == 3

    assert (
        v1.widgets[0].placement.column
        == 0
    )

    assert (
        v2.widgets[0].placement.column
        == 2
    )

    assert (
        v3.widgets[0].placement.column
        == 0
    )

    assert (
        v1.widgets[0].settings_json
        == '{"timeframe":"1H"}'
    )

    assert (
        v2.widgets[0].settings_json
        == '{"timeframe":"4H"}'
    )

    assert (
        v3.widgets[0].settings_json
        == '{"timeframe":"1H"}'
    )

    assert v3.source_version == 1

    assert current is not None
    assert current.active_layout_version == 3


def test_restore_workspace_rejects_stale_base_without_v4() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _prepare_v2(factory)

            await service.restore_workspace_layout(
                session_factory=factory,
                tenant_workspace_id="tenant-a",
                user_id=7,
                payload={
                    "workspaceId": "desk",
                    "baseVersion": 2,
                    "targetVersion": 1,
                },
                created_at=RESTORED_AT,
            )

            with pytest.raises(
                service.WorkspaceRestoreConflict
            ):
                await service.restore_workspace_layout(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "workspaceId": "desk",
                        "baseVersion": 2,
                        "targetVersion": 1,
                    },
                    created_at=RESTORED_AT,
                )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                current = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            "desk"
                        ),
                    )
                )

                v4 = await repository.get_layout(
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    user_workspace_id="desk",
                    version=4,
                )

            return current, v4

        finally:
            await engine.dispose()

    current, v4 = asyncio.run(
        scenario()
    )

    assert current is not None
    assert current.active_layout_version == 3
    assert v4 is None


def test_restore_workspace_requires_older_target() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _prepare_v2(factory)

            with pytest.raises(
                service.WorkspaceRestoreInvalid
            ):
                await service.restore_workspace_layout(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "workspaceId": "desk",
                        "baseVersion": 2,
                        "targetVersion": 2,
                    },
                    created_at=RESTORED_AT,
                )

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )


def test_restore_workspace_is_tenant_user_scoped() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _prepare_v2(factory)

            with pytest.raises(
                service.WorkspaceRestoreNotFound
            ):
                await service.restore_workspace_layout(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=8,
                    payload={
                        "workspaceId": "desk",
                        "baseVersion": 2,
                        "targetVersion": 1,
                    },
                    created_at=RESTORED_AT,
                )

            with pytest.raises(
                service.WorkspaceRestoreNotFound
            ):
                await service.restore_workspace_layout(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-b"
                    ),
                    user_id=7,
                    payload={
                        "workspaceId": "desk",
                        "baseVersion": 2,
                        "targetVersion": 1,
                    },
                    created_at=RESTORED_AT,
                )

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )
