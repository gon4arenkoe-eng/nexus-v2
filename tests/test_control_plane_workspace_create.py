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
    WorkspaceLayoutVersion,
)


pytest.importorskip("aiosqlite")


NOW = datetime(
    2026,
    9,
    28,
    13,
    0,
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


def test_create_blank_workspace_persists_owned_v1() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            workspace, layout = (
                await service.create_blank_workspace(
                    session_factory=factory,
                    tenant_workspace_id="tenant-a",
                    user_id=7,
                    payload={
                        "name": "Research",
                        "locale": "ru",
                        "theme": "dark",
                    },
                    created_at=NOW,
                )
            )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                persisted_workspace = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            workspace.user_workspace_id
                        ),
                    )
                )

                persisted_layout = (
                    await repository.get_layout(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            workspace.user_workspace_id
                        ),
                        version=1,
                    )
                )

            return (
                workspace,
                layout,
                persisted_workspace,
                persisted_layout,
            )

        finally:
            await engine.dispose()

    (
        workspace,
        layout,
        persisted_workspace,
        persisted_layout,
    ) = asyncio.run(
        scenario()
    )

    assert (
        workspace.user_workspace_id
        .startswith("ws-")
    )
    assert workspace.name == "Research"
    assert workspace.user_id == 7

    assert (
        workspace.tenant_workspace_id
        == "tenant-a"
    )

    assert (
        workspace.locale
        is SupportedLocale.RUSSIAN
    )

    assert (
        workspace.theme
        is ThemePreference.DARK
    )

    assert (
        workspace.active_layout_version
        == 1
    )

    assert layout.version == 1
    assert layout.source_version is None
    assert layout.widgets == ()

    assert persisted_workspace == workspace
    assert persisted_layout == layout


def test_create_blank_workspace_rejects_cross_user_id_collision(
    monkeypatch,
) -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                existing = UserWorkspace(
                    tenant_workspace_id="tenant-a",
                    user_workspace_id="ws-fixed",
                    user_id=8,
                    name="Peer",
                    locale=(
                        SupportedLocale.RUSSIAN
                    ),
                    theme=ThemePreference.DARK,
                    active_layout_version=1,
                    created_at=NOW,
                    updated_at=NOW,
                )

                await repository.add_user_workspace(
                    existing
                )

                await repository.append_layout(
                    WorkspaceLayoutVersion(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_workspace_id=(
                            "ws-fixed"
                        ),
                        user_id=8,
                        version=1,
                        widgets=(),
                        created_at=NOW,
                    )
                )

                await session.commit()

            monkeypatch.setattr(
                service,
                "_new_workspace_id",
                lambda: "ws-fixed",
            )

            with pytest.raises(
                service.WorkspaceCreateConflict
            ):
                await service.create_blank_workspace(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "name": "Mine",
                        "locale": "ru",
                        "theme": "dark",
                    },
                    created_at=NOW,
                )

            async with factory() as session:
                repository = (
                    ControlPlaneRepository(
                        session
                    )
                )

                owner = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=8,
                        user_workspace_id=(
                            "ws-fixed"
                        ),
                    )
                )

                wrong_user = (
                    await repository
                    .get_user_workspace(
                        tenant_workspace_id=(
                            "tenant-a"
                        ),
                        user_id=7,
                        user_workspace_id=(
                            "ws-fixed"
                        ),
                    )
                )

            return owner, wrong_user

        finally:
            await engine.dispose()

    owner, wrong_user = asyncio.run(
        scenario()
    )

    assert owner is not None
    assert owner.user_id == 8
    assert owner.name == "Peer"

    assert wrong_user is None


def test_create_blank_workspace_rejects_invalid_presentation_values() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            with pytest.raises(
                service.WorkspaceCreateInvalid
            ):
                await service.create_blank_workspace(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "name": "Research",
                        "locale": "__invalid__",
                        "theme": "dark",
                    },
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )
