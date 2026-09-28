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
)


pytest.importorskip("aiosqlite")


NOW = datetime(
    2026,
    9,
    28,
    15,
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


def test_curated_template_catalog_exposes_expected_templates() -> None:
    templates = (
        service
        .list_curated_workspace_templates(
            created_at=NOW
        )
    )

    keys = {
        template.template_key
        for template in templates
    }

    assert "command-center" in keys
    assert "active-trader" in keys
    assert "grid-desk" in keys
    assert "aiea-researcher" in keys
    assert "risk-operations" in keys
    assert "multi-account-desk" in keys

    # Blank creation already has its own
    # canonical endpoint / evidence slice.
    assert "blank-workspace" not in keys

    for template in templates:
        assert (
            template.owner_workspace_id
            is None
        )

        assert len(template.widgets) > 0


def test_create_workspace_from_curated_template_persists_v1() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            templates = (
                service
                .list_curated_workspace_templates(
                    created_at=NOW
                )
            )

            template = next(
                item
                for item in templates
                if item.template_key
                == "command-center"
            )

            workspace, layout, selected = (
                await service.create_workspace_from_curated_template(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "name": "Command Desk",
                        "locale": "ru",
                        "theme": "dark",
                        "templateKey": (
                            template.template_key
                        ),
                        "templateVersion": (
                            template.version
                        ),
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
                            workspace
                            .user_workspace_id
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
                            workspace
                            .user_workspace_id
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
                            workspace
                            .user_workspace_id
                        ),
                    )
                )

            return (
                template,
                workspace,
                layout,
                selected,
                persisted_workspace,
                persisted_layout,
                wrong_user,
            )

        finally:
            await engine.dispose()

    (
        template,
        workspace,
        layout,
        selected,
        persisted_workspace,
        persisted_layout,
        wrong_user,
    ) = asyncio.run(
        scenario()
    )

    assert workspace.name == "Command Desk"
    assert workspace.user_id == 7

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
    assert layout.widgets == template.widgets

    assert (
        selected.template_key
        == "command-center"
    )

    assert (
        persisted_workspace
        == workspace
    )

    assert (
        persisted_layout
        == layout
    )

    assert wrong_user is None


def test_curated_template_create_rejects_unknown_template() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            with pytest.raises(
                service
                .WorkspaceTemplateCreateNotFound
            ):
                await service.create_workspace_from_curated_template(
                    session_factory=factory,
                    tenant_workspace_id=(
                        "tenant-a"
                    ),
                    user_id=7,
                    payload={
                        "name": "Unknown",
                        "locale": "ru",
                        "theme": "dark",
                        "templateKey": (
                            "does-not-exist"
                        ),
                        "templateVersion": 1,
                    },
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )
