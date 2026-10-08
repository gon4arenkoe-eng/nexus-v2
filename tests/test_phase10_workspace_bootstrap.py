from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import infra.persistence.application.platform_security as service
from infra.persistence.base import PersistenceBase
from infra.persistence.models.platform_security import AuditEventModel
from infra.persistence.repositories.platform_security import (
    PlatformSecurityRepository,
)
from packages.contracts.security import (
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)


pytest.importorskip("aiosqlite")

NOW = datetime(2026, 10, 8, 8, 0, tzinfo=UTC)


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


def test_workspace_bootstrap_creates_owner_and_audit() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            result = await service.bootstrap_workspace(
                session_factory=factory,
                workspace_id="tenant-main",
                workspace_name="GreeNGo",
                owner_user_id=2,
                reason="initial tenant provisioning",
                created_at=NOW,
            )

            async with factory() as session:
                repository = PlatformSecurityRepository(session)

                workspace = await repository.get_workspace(
                    workspace_id="tenant-main"
                )
                membership = await repository.get_membership(
                    workspace_id="tenant-main",
                    user_id=2,
                )
                audit = await session.get(
                    AuditEventModel,
                    (
                        "tenant-main",
                        "workspace-bootstrap:tenant-main",
                    ),
                )

            return result, workspace, membership, audit

        finally:
            await engine.dispose()

    result, workspace, membership, audit = asyncio.run(
        scenario()
    )

    assert workspace is not None
    assert workspace.owner_user_id == 2
    assert workspace.name == "GreeNGo"

    assert membership is not None
    assert membership.user_id == 2
    assert membership.role is WorkspaceRole.OWNER
    assert membership.active is True

    assert result == (workspace, membership)

    assert audit is not None
    assert audit.actor_user_id == 2
    assert audit.action == "workspace.bootstrap"
    assert audit.resource_type == "workspace"
    assert audit.resource_id == "tenant-main"


def test_workspace_bootstrap_is_idempotent() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            first = await service.bootstrap_workspace(
                session_factory=factory,
                workspace_id="tenant-main",
                workspace_name="GreeNGo",
                owner_user_id=2,
                reason="initial tenant provisioning",
                created_at=NOW,
            )

            second = await service.bootstrap_workspace(
                session_factory=factory,
                workspace_id="tenant-main",
                workspace_name="GreeNGo",
                owner_user_id=2,
                reason="initial tenant provisioning",
                created_at=NOW,
            )

            return first, second

        finally:
            await engine.dispose()

    first, second = asyncio.run(scenario())

    assert first == second


def test_workspace_bootstrap_rejects_owner_conflict() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await service.bootstrap_workspace(
                session_factory=factory,
                workspace_id="tenant-main",
                workspace_name="GreeNGo",
                owner_user_id=2,
                reason="initial tenant provisioning",
                created_at=NOW,
            )

            with pytest.raises(
                service.WorkspaceBootstrapConflict
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=3,
                    reason="conflicting tenant provisioning",
                    created_at=NOW,
                )

            async with factory() as session:
                repository = PlatformSecurityRepository(session)
                workspace = await repository.get_workspace(
                    workspace_id="tenant-main"
                )

            return workspace

        finally:
            await engine.dispose()

    workspace = asyncio.run(scenario())

    assert workspace is not None
    assert workspace.owner_user_id == 2


def test_workspace_bootstrap_rejects_non_owner_membership() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            async with factory() as session:
                repository = PlatformSecurityRepository(session)

                await repository.add_workspace(
                    Workspace(
                        "tenant-main",
                        "GreeNGo",
                        2,
                        NOW,
                    )
                )
                await repository.put_membership(
                    WorkspaceMembership(
                        "tenant-main",
                        2,
                        WorkspaceRole.TRADER,
                        True,
                    )
                )

                await session.commit()

            with pytest.raises(
                service.WorkspaceBootstrapConflict
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=2,
                    reason="initial tenant provisioning",
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_workspace_bootstrap_rejects_inactive_owner_membership() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            async with factory() as session:
                repository = PlatformSecurityRepository(session)

                await repository.add_workspace(
                    Workspace(
                        "tenant-main",
                        "GreeNGo",
                        2,
                        NOW,
                    )
                )
                await repository.put_membership(
                    WorkspaceMembership(
                        "tenant-main",
                        2,
                        WorkspaceRole.OWNER,
                        False,
                    )
                )
                await session.commit()

            with pytest.raises(
                service.WorkspaceBootstrapConflict
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=2,
                    reason="initial tenant provisioning",
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_workspace_bootstrap_rejects_workspace_without_owner_membership() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            async with factory() as session:
                repository = PlatformSecurityRepository(session)
                await repository.add_workspace(
                    Workspace(
                        "tenant-main",
                        "GreeNGo",
                        2,
                        NOW,
                    )
                )
                await session.commit()

            with pytest.raises(
                service.WorkspaceBootstrapConflict
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=2,
                    reason="initial tenant provisioning",
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_workspace_bootstrap_rejects_membership_without_workspace() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            async with factory() as session:
                repository = PlatformSecurityRepository(session)
                await repository.put_membership(
                    WorkspaceMembership(
                        "tenant-main",
                        2,
                        WorkspaceRole.OWNER,
                        True,
                    )
                )
                await session.commit()

            with pytest.raises(
                service.WorkspaceBootstrapConflict
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=2,
                    reason="initial tenant provisioning",
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_workspace_bootstrap_rejects_invalid_owner_user_id() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            with pytest.raises(ValueError):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=0,
                    reason="invalid tenant provisioning",
                    created_at=NOW,
                )

        finally:
            await engine.dispose()

    asyncio.run(scenario())


def test_workspace_bootstrap_rolls_back_partial_state(
    monkeypatch,
) -> None:
    async def scenario():
        engine, factory = await _factory()

        original_put_membership = (
            PlatformSecurityRepository.put_membership
        )

        async def fail_after_workspace(
            self,
            value,
        ):
            raise RuntimeError("injected membership failure")

        monkeypatch.setattr(
            PlatformSecurityRepository,
            "put_membership",
            fail_after_workspace,
        )

        try:
            with pytest.raises(
                RuntimeError,
                match="injected membership failure",
            ):
                await service.bootstrap_workspace(
                    session_factory=factory,
                    workspace_id="tenant-main",
                    workspace_name="GreeNGo",
                    owner_user_id=2,
                    reason="initial tenant provisioning",
                    created_at=NOW,
                )

            async with factory() as session:
                repository = PlatformSecurityRepository(session)

                workspace = await repository.get_workspace(
                    workspace_id="tenant-main"
                )
                membership = await repository.get_membership(
                    workspace_id="tenant-main",
                    user_id=2,
                )
                audit = await session.get(
                    AuditEventModel,
                    (
                        "tenant-main",
                        "workspace-bootstrap:tenant-main",
                    ),
                )

            return workspace, membership, audit

        finally:
            monkeypatch.setattr(
                PlatformSecurityRepository,
                "put_membership",
                original_put_membership,
            )
            await engine.dispose()

    workspace, membership, audit = asyncio.run(
        scenario()
    )

    assert workspace is None
    assert membership is None
    assert audit is None


def test_workspace_bootstrap_does_not_grant_peer_user_access() -> None:
    async def scenario():
        engine, factory = await _factory()

        try:
            await service.bootstrap_workspace(
                session_factory=factory,
                workspace_id="tenant-main",
                workspace_name="GreeNGo",
                owner_user_id=2,
                reason="initial tenant provisioning",
                created_at=NOW,
            )

            async with factory() as session:
                repository = PlatformSecurityRepository(session)

                owner = await repository.get_membership(
                    workspace_id="tenant-main",
                    user_id=2,
                )
                peer = await repository.get_membership(
                    workspace_id="tenant-main",
                    user_id=3,
                )

            return owner, peer

        finally:
            await engine.dispose()

    owner, peer = asyncio.run(scenario())

    assert owner is not None
    assert owner.role is WorkspaceRole.OWNER
    assert peer is None
