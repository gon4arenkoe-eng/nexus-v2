from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infra.persistence.application.control_plane_workspace import (
    WorkspaceSaveConflict,
    WorkspaceSaveNotFound,
    save_existing_workspace,
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

pytest.importorskip("aiosqlite")

NOW = datetime(
    2026,
    9,
    28,
    12,
    0,
    tzinfo=UTC,
)

LATER = datetime(
    2026,
    9,
    28,
    12,
    1,
    tzinfo=UTC,
)


def _widget() -> WidgetInstance:
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


async def _factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            PersistenceBase.metadata.create_all
        )

    return (
        engine,
        async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
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
                widgets=(_widget(),),
                created_at=NOW,
            )
        )

        await session.commit()


def _payload(
    base_version: int,
) -> dict[str, object]:
    return {
        "workspaceId": "desk",
        "baseVersion": base_version,
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


def test_save_existing_workspace_appends_version_and_advances_active_version() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _seed(factory)

            workspace, layout = (
                await save_existing_workspace(
                    session_factory=factory,
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    payload=_payload(1),
                    created_at=LATER,
                )
            )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                original = (
                    await repository.get_layout(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id="desk",
                        version=1,
                    )
                )

                persisted = (
                    await repository.get_layout(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id="desk",
                        version=2,
                    )
                )

                current = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id="desk",
                    )
                )

            return (
                workspace,
                layout,
                original,
                persisted,
                current,
            )

        finally:
            await engine.dispose()

    (
        workspace,
        layout,
        original,
        persisted,
        current,
    ) = asyncio.run(
        scenario()
    )

    assert workspace.active_layout_version == 2
    assert layout.version == 2
    assert layout.source_version == 1

    assert original is not None
    assert original.version == 1

    assert (
        original.widgets[0]
        .placement.column
        == 0
    )

    assert persisted is not None
    assert persisted.version == 2
    assert persisted.source_version == 1

    assert (
        persisted.widgets[0]
        .placement.column
        == 2
    )

    assert (
        persisted.widgets[0].settings_json
        == '{"timeframe":"4H"}'
    )

    assert current is not None

    assert (
        current.active_layout_version
        == 2
    )


def test_save_existing_workspace_rejects_stale_base_version_without_v3() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _seed(factory)

            await save_existing_workspace(
                session_factory=factory,
                tenant_workspace_id="tenant-a",
                user_id=7,
                payload=_payload(1),
                created_at=LATER,
            )

            with pytest.raises(
                WorkspaceSaveConflict
            ):
                await save_existing_workspace(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload=_payload(1),
                    created_at=LATER,
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
                        user_workspace_id="desk",
                    )
                )

                version_three = (
                    await repository.get_layout(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id="desk",
                        version=3,
                    )
                )

            return (
                current,
                version_three,
            )

        finally:
            await engine.dispose()

    current, version_three = asyncio.run(
        scenario()
    )

    assert current is not None

    assert (
        current.active_layout_version
        == 2
    )

    assert version_three is None


def test_save_existing_workspace_is_tenant_user_scoped() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await _seed(factory)

            with pytest.raises(
                WorkspaceSaveNotFound
            ):
                await save_existing_workspace(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=8,
                    payload=_payload(1),
                    created_at=LATER,
                )

            with pytest.raises(
                WorkspaceSaveNotFound
            ):
                await save_existing_workspace(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-b"
                    ),
                    user_id=7,
                    payload=_payload(1),
                    created_at=LATER,
                )

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )
