from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infra.persistence.base import PersistenceBase
from infra.persistence.repositories.control_plane import ControlPlaneRepository
from packages.contracts.control_plane import (
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetInstance,
    WorkspaceLayoutVersion,
    WorkspaceTemplate,
)
from packages.contracts.workspace import WidgetPlacement, WidgetSize

pytest.importorskip("aiosqlite")

NOW = datetime(2026, 9, 12, 20, 0, tzinfo=UTC)


def _widget(instance_id: str) -> WidgetInstance:
    return WidgetInstance(
        placement=WidgetPlacement(
            instance_id=instance_id,
            widget_key="portfolio.positions",
            widget_version=1,
            column=0,
            row=0,
            size=WidgetSize(4, 3),
            context_group="market",
        ),
        settings_json='{"columns":["symbol","pnl"]}',
    )


async def _factory() -> tuple[object, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(PersistenceBase.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_user_workspace_and_layout_survive_fresh_session() -> None:
    async def scenario() -> tuple[
        UserWorkspace | None,
        WorkspaceLayoutVersion | None,
    ]:
        engine, factory = await _factory()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            await repo.put_user_workspace(
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
            await repo.append_layout(
                WorkspaceLayoutVersion(
                    tenant_workspace_id="tenant-a",
                    user_workspace_id="desk",
                    user_id=7,
                    version=1,
                    widgets=(_widget("positions-1"),),
                    created_at=NOW,
                )
            )
            await session.commit()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            workspace = await repo.get_user_workspace(
                tenant_workspace_id="tenant-a",
                user_id=7,
                user_workspace_id="desk",
            )
            layout = await repo.get_layout(
                tenant_workspace_id="tenant-a",
                user_id=7,
                user_workspace_id="desk",
                version=1,
            )
        await engine.dispose()
        return workspace, layout

    workspace, layout = asyncio.run(scenario())
    assert workspace is not None
    assert workspace.locale is SupportedLocale.RUSSIAN
    assert workspace.created_at.tzinfo is not None
    assert layout is not None
    assert layout.widgets[0].placement.instance_id == "positions-1"
    assert layout.created_at.tzinfo is not None


def test_cross_user_and_cross_tenant_layout_reads_fail_closed() -> None:
    async def scenario() -> tuple[object, object]:
        engine, factory = await _factory()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            await repo.append_layout(
                WorkspaceLayoutVersion(
                    tenant_workspace_id="tenant-a",
                    user_workspace_id="desk",
                    user_id=7,
                    version=1,
                    widgets=(_widget("positions-1"),),
                    created_at=NOW,
                )
            )
            await session.commit()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            wrong_user = await repo.get_layout(
                tenant_workspace_id="tenant-a",
                user_id=8,
                user_workspace_id="desk",
                version=1,
            )
            wrong_tenant = await repo.get_layout(
                tenant_workspace_id="tenant-b",
                user_id=7,
                user_workspace_id="desk",
                version=1,
            )
        await engine.dispose()
        return wrong_user, wrong_tenant

    assert asyncio.run(scenario()) == (None, None)


def test_template_visibility_is_tenant_and_owner_scoped() -> None:
    async def scenario() -> tuple[
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, ...],
    ]:
        engine, factory = await _factory()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            for template in (
                WorkspaceTemplate(
                    "command-center",
                    1,
                    "template.command",
                    (_widget("a"),),
                    NOW,
                ),
                WorkspaceTemplate(
                    "team-a",
                    1,
                    "template.team",
                    (_widget("b"),),
                    NOW,
                    owner_workspace_id="tenant-a",
                    owner_user_id=7,
                    shared=True,
                ),
                WorkspaceTemplate(
                    "private-a",
                    1,
                    "template.private",
                    (_widget("c"),),
                    NOW,
                    owner_workspace_id="tenant-a",
                    owner_user_id=7,
                    shared=False,
                ),
            ):
                await repo.append_template(template)
            await session.commit()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            owner = await repo.list_templates(
                tenant_workspace_id="tenant-a",
                user_id=7,
            )
            peer = await repo.list_templates(
                tenant_workspace_id="tenant-a",
                user_id=8,
            )
            other = await repo.list_templates(
                tenant_workspace_id="tenant-b",
                user_id=7,
            )
        await engine.dispose()
        return (
            tuple(item.template_key for item in owner),
            tuple(item.template_key for item in peer),
            tuple(item.template_key for item in other),
        )

    owner, peer, other = asyncio.run(scenario())
    assert owner == ("command-center", "private-a", "team-a")
    assert peer == ("command-center", "team-a")
    assert other == ("command-center",)


def test_user_locale_preference_survives_fresh_session() -> None:
    async def scenario() -> tuple[
        SupportedLocale,
        ThemePreference,
        datetime,
    ] | None:
        engine, factory = await _factory()
        async with factory() as session:
            repo = ControlPlaneRepository(session)
            await repo.put_user_preferences(
                user_id=7,
                locale=SupportedLocale.CHINESE_SIMPLIFIED,
                theme=ThemePreference.LIGHT,
                updated_at=NOW,
            )
            await session.commit()
        async with factory() as session:
            value = await ControlPlaneRepository(
                session
            ).get_user_preferences(user_id=7)
        await engine.dispose()
        return value

    result = asyncio.run(scenario())
    assert result is not None
    assert result[0] is SupportedLocale.CHINESE_SIMPLIFIED
    assert result[1] is ThemePreference.LIGHT
    assert result[2].tzinfo is not None
