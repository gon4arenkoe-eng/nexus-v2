from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.core.application.platform_security import SettingsResolver, setting_change_evidence  # noqa: E501
from infra.persistence.base import PersistenceBase
from infra.persistence.repositories.platform_security import PlatformSecurityRepository  # noqa: E501
from packages.contracts.product_access import BillingEvent
from packages.contracts.security import (
    EncryptedSecretEnvelope,
    SecretKind,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from packages.contracts.settings import SettingDomain, SettingScope, SettingValue  # noqa: E501

NOW = datetime(2026, 9, 12, 18, 0, tzinfo=UTC)


def test_tenant_membership_survives_fresh_session_and_does_not_cross() -> None:
    async def scenario() -> tuple[object, object]:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            await repo.add_workspace(Workspace("ws-a", "A", 1, NOW))
            await repo.put_membership(WorkspaceMembership("ws-a", 7, WorkspaceRole.TRADER))  # noqa: E501
            await session.commit()
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            own = await repo.get_membership(workspace_id="ws-a", user_id=7)
            other = await repo.get_membership(workspace_id="ws-b", user_id=7)
        await engine.dispose()
        return own, other

    own, other = asyncio.run(scenario())
    assert own is not None
    assert other is None


def test_versioned_settings_and_audit_survive_fresh_session() -> None:
    async def scenario() -> str:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        value = SettingValue(
            "ws-a", "risk.max_notional", SettingDomain.PORTFOLIO_RISK,
            SettingScope.WORKSPACE, "ws-a", "100", 1, True, 7, NOW,
        )
        evidence = setting_change_evidence(old=None, new=value, event_id="audit-1", reason="initial safe limit")  # noqa: E501
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            await repo.append_setting(evidence.setting)
            await repo.append_audit(evidence.audit_event)
            await session.commit()
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            values = await repo.list_settings(workspace_id="ws-a", key="risk.max_notional")  # noqa: E501
            resolved = SettingsResolver().resolve(key="risk.max_notional", candidates=values)  # noqa: E501
        await engine.dispose()
        return resolved.value_json

    assert asyncio.run(scenario()) == "100"


def test_billing_event_is_idempotent_but_conflict_fails() -> None:
    async def scenario() -> bool:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        event = BillingEvent("stripe", "evt-1", "ws-a", "invoice.paid", "hash-a", NOW)  # noqa: E501
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            await repo.append_billing_event(event)
            await repo.append_billing_event(event)
            await session.commit()
        failed = False
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            try:
                await repo.append_billing_event(BillingEvent("stripe", "evt-1", "ws-a", "invoice.paid", "hash-b", NOW))  # noqa: E501
            except ValueError:
                failed = True
        await engine.dispose()
        return failed

    assert asyncio.run(scenario())


def test_encrypted_secret_survives_rotation_without_plaintext_repr() -> None:
    async def scenario() -> EncryptedSecretEnvelope:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            await repo.put_secret(EncryptedSecretEnvelope(
                "ws-a", "account-1", SecretKind.EXCHANGE_API_SECRET,
                "cipher-v1", "kms-v1", NOW,
            ))
            await repo.put_secret(EncryptedSecretEnvelope(
                "ws-a", "account-1", SecretKind.EXCHANGE_API_SECRET,
                "cipher-v2", "kms-v2", NOW,
            ))
            await session.commit()
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            value = await repo.get_secret(
                workspace_id="ws-a", resource_id="account-1",
                secret_kind=SecretKind.EXCHANGE_API_SECRET.value,
            )
        await engine.dispose()
        assert value is not None
        return value

    value = asyncio.run(scenario())
    assert value.key_version == "kms-v2"
    assert "cipher-v2" not in repr(value)


def test_plan_version_is_immutable_and_quota_reservation_is_bounded() -> None:
    from apps.core.application.platform_security import immutable_payload_hash
    from packages.contracts.product_access import (
        FeatureKey,
        PlanVersion,
        ProductPlan,
        QuotaDefinition,
    )

    async def scenario() -> tuple[bool, bool, bool]:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        plan = ProductPlan("pro", "Pro")
        version = PlanVersion(
            plan_id="pro",
            version=1,
            entitlements=frozenset({FeatureKey("grid.instance.create")}),
            quotas=(
                QuotaDefinition(FeatureKey("workspace.member.create"), 2),
            ),
            created_at=NOW,
        )
        payload_hash = immutable_payload_hash("pro:1:grid.instance.create:2")
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            await repo.put_product_plan(plan)
            await repo.append_plan_version(
                version,
                content_hash=payload_hash,
            )
            await repo.append_plan_version(
                version,
                content_hash=payload_hash,
            )
            await repo.seed_quota_usage(
                workspace_id="ws-a",
                quota_key="workspace.member.create",
                period_key="2026-09",
                updated_at=NOW,
            )
            await session.commit()
        async with factory() as session:
            repo = PlatformSecurityRepository(session)
            first = await repo.reserve_quota(
                workspace_id="ws-a",
                quota_key="workspace.member.create",
                period_key="2026-09",
                amount=1,
                limit=2,
                updated_at=NOW,
            )
            second = await repo.reserve_quota(
                workspace_id="ws-a",
                quota_key="workspace.member.create",
                period_key="2026-09",
                amount=1,
                limit=2,
                updated_at=NOW,
            )
            denied = await repo.reserve_quota(
                workspace_id="ws-a",
                quota_key="workspace.member.create",
                period_key="2026-09",
                amount=1,
                limit=2,
                updated_at=NOW,
            )
            await session.commit()
        await engine.dispose()
        return first, second, denied

    assert asyncio.run(scenario()) == (True, True, False)
