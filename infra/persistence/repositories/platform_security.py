"""Tenant-scoped persistence repositories for Phase 10."""
from __future__ import annotations

from datetime import UTC, datetime
import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.models.platform_security import (
    AuditEventModel,
    BillingEventModel,
    EncryptedSecretModel,
    ProductPlanModel,
    ProductPlanVersionModel,
    QuotaUsageModel,
    ResourceOwnershipModel,
    SettingVersionModel,
    WorkspaceMembershipModel,
    WorkspaceModel,
)
from packages.contracts.product_access import (
    BillingEvent,
    PlanVersion,
    ProductPlan,
)
from packages.contracts.security import (
    AuditEvent,
    EncryptedSecretEnvelope,
    ResourceOwnership,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from packages.contracts.settings import SettingDomain, SettingScope, SettingValue  # noqa: E501


def _restore_utc(value: datetime) -> datetime:
    """Restore UTC when a database drops timezone metadata."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value


class PlatformSecurityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_workspace(self, value: Workspace) -> None:
        self._session.add(WorkspaceModel(
            workspace_id=value.workspace_id, name=value.name,
            owner_user_id=value.owner_user_id, created_at=value.created_at,
        ))

    async def put_membership(self, value: WorkspaceMembership) -> None:
        model = await self._session.get(WorkspaceMembershipModel, (value.workspace_id, value.user_id))  # noqa: E501
        if model is None:
            self._session.add(WorkspaceMembershipModel(
                workspace_id=value.workspace_id, user_id=value.user_id,
                role=value.role.value, active=value.active,
            ))
        else:
            model.role = value.role.value
            model.active = value.active

    async def get_membership(self, *, workspace_id: str, user_id: int) -> WorkspaceMembership | None:  # noqa: E501
        model = await self._session.get(WorkspaceMembershipModel, (workspace_id, user_id))  # noqa: E501
        if model is None:
            return None
        return WorkspaceMembership(model.workspace_id, model.user_id, WorkspaceRole(model.role), model.active)  # noqa: E501

    async def put_ownership(self, value: ResourceOwnership) -> None:
        model = await self._session.get(
            ResourceOwnershipModel,
            (value.workspace_id, value.resource_type, value.resource_id),
        )
        if model is None:
            self._session.add(
                ResourceOwnershipModel(
                    workspace_id=value.workspace_id,
                    resource_type=value.resource_type,
                    resource_id=value.resource_id,
                    owner_user_id=value.owner_user_id,
                )
            )
        elif model.owner_user_id != value.owner_user_id:
            raise ValueError("resource ownership conflict")

    async def get_ownership(
        self,
        *,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
    ) -> ResourceOwnership | None:
        model = await self._session.get(
            ResourceOwnershipModel,
            (workspace_id, resource_type, resource_id),
        )
        if model is None:
            return None
        return ResourceOwnership(
            model.workspace_id,
            model.resource_type,
            model.resource_id,
            model.owner_user_id,
        )

    async def append_setting(self, value: SettingValue) -> None:
        existing = await self._session.get(SettingVersionModel, (
            value.workspace_id, value.key, int(value.scope), value.scope_id, value.version,  # noqa: E501
        ))
        if existing is not None:
            if existing.value_json == value.value_json and existing.actor_user_id == value.actor_user_id:  # noqa: E501
                return
            raise ValueError("immutable setting version conflict")
        self._session.add(SettingVersionModel(
            workspace_id=value.workspace_id, key=value.key, scope=int(value.scope),  # noqa: E501
            scope_id=value.scope_id, version=value.version, domain=value.domain.value,  # noqa: E501
            value_json=value.value_json, safety_critical=value.safety_critical,
            actor_user_id=value.actor_user_id, created_at=value.created_at,
        ))

    async def list_settings(self, *, workspace_id: str, key: str) -> tuple[SettingValue, ...]:  # noqa: E501
        result = await self._session.execute(
            select(SettingVersionModel).where(
                SettingVersionModel.workspace_id == workspace_id,
                SettingVersionModel.key == key,
            )
        )
        return tuple(SettingValue(
            workspace_id=m.workspace_id, key=m.key, domain=SettingDomain(m.domain),  # noqa: E501
            scope=SettingScope(m.scope), scope_id=m.scope_id, value_json=m.value_json,  # noqa: E501
            version=m.version, safety_critical=m.safety_critical,
            actor_user_id=m.actor_user_id,
            created_at=_restore_utc(m.created_at),
        ) for m in result.scalars().all())

    async def append_audit(self, value: AuditEvent) -> None:
        existing = await self._session.get(AuditEventModel, (value.workspace_id, value.event_id))  # noqa: E501
        if existing is not None:
            if existing.action == value.action and existing.resource_id == value.resource_id:  # noqa: E501
                return
            raise ValueError("immutable audit event conflict")
        self._session.add(AuditEventModel(
            workspace_id=value.workspace_id, event_id=value.event_id,
            actor_user_id=value.actor_user_id, action=value.action,
            resource_type=value.resource_type, resource_id=value.resource_id,
            old_value_json=value.old_value_json, new_value_json=value.new_value_json,  # noqa: E501
            reason=value.reason, occurred_at=value.occurred_at,
        ))

    async def put_product_plan(self, value: ProductPlan) -> None:
        model = await self._session.get(ProductPlanModel, value.plan_id)
        if model is None:
            self._session.add(
                ProductPlanModel(
                    plan_id=value.plan_id,
                    display_name=value.display_name,
                )
            )
        else:
            model.display_name = value.display_name

    async def append_plan_version(
        self,
        value: PlanVersion,
        *,
        content_hash: str,
    ) -> None:
        entitlements_json = json.dumps(
            sorted(str(item) for item in value.entitlements),
            separators=(",", ":"),
        )
        quotas_json = json.dumps(
            sorted(
                (str(item.quota_key), item.limit)
                for item in value.quotas
            ),
            separators=(",", ":"),
        )
        model = await self._session.get(
            ProductPlanVersionModel,
            (value.plan_id, value.version),
        )
        if model is not None:
            if model.content_hash == content_hash:
                return
            raise ValueError("immutable plan version conflict")
        self._session.add(
            ProductPlanVersionModel(
                plan_id=value.plan_id,
                version=value.version,
                entitlements_json=entitlements_json,
                quotas_json=quotas_json,
                content_hash=content_hash,
                created_at=value.created_at,
            )
        )

    async def seed_quota_usage(
        self,
        *,
        workspace_id: str,
        quota_key: str,
        period_key: str,
        updated_at: datetime,
    ) -> None:
        model = await self._session.get(
            QuotaUsageModel,
            (workspace_id, quota_key, period_key),
        )
        if model is None:
            self._session.add(
                QuotaUsageModel(
                    workspace_id=workspace_id,
                    quota_key=quota_key,
                    period_key=period_key,
                    usage=0,
                    updated_at=updated_at,
                )
            )

    async def reserve_quota(
        self,
        *,
        workspace_id: str,
        quota_key: str,
        period_key: str,
        amount: int,
        limit: int,
        updated_at: datetime,
    ) -> bool:
        if amount <= 0 or limit < 0:
            raise ValueError("amount must be positive and limit non-negative")
        statement = (
            update(QuotaUsageModel)
            .where(
                QuotaUsageModel.workspace_id == workspace_id,
                QuotaUsageModel.quota_key == quota_key,
                QuotaUsageModel.period_key == period_key,
                QuotaUsageModel.usage + amount <= limit,
            )
            .values(
                usage=QuotaUsageModel.usage + amount,
                updated_at=updated_at,
            )
        )
        result = await self._session.execute(statement)
        return bool(getattr(result, "rowcount", 0) == 1)

    async def append_billing_event(self, value: BillingEvent) -> None:
        existing = await self._session.get(BillingEventModel, (value.provider, value.event_id))  # noqa: E501
        if existing is not None:
            if existing.payload_hash == value.payload_hash and existing.workspace_id == value.workspace_id:  # noqa: E501
                return
            raise ValueError("billing event idempotency conflict")
        self._session.add(BillingEventModel(
            provider=value.provider, event_id=value.event_id,
            workspace_id=value.workspace_id, event_type=value.event_type,
            payload_hash=value.payload_hash, occurred_at=value.occurred_at,
        ))

    async def put_secret(self, value: EncryptedSecretEnvelope) -> None:
        model = await self._session.get(EncryptedSecretModel, (
            value.workspace_id, value.resource_id, value.secret_kind.value,
        ))
        if model is None:
            self._session.add(EncryptedSecretModel(
                workspace_id=value.workspace_id, resource_id=value.resource_id,
                secret_kind=value.secret_kind.value, ciphertext=value.ciphertext,  # noqa: E501
                key_version=value.key_version, rotated_at=value.rotated_at,
            ))
        else:
            model.ciphertext = value.ciphertext
            model.key_version = value.key_version
            model.rotated_at = value.rotated_at

    async def get_secret(self, *, workspace_id: str, resource_id: str, secret_kind: str) -> EncryptedSecretEnvelope | None:  # noqa: E501
        model = await self._session.get(EncryptedSecretModel, (workspace_id, resource_id, secret_kind))  # noqa: E501
        if model is None:
            return None
        from packages.contracts.security import SecretKind
        return EncryptedSecretEnvelope(
            workspace_id=model.workspace_id, resource_id=model.resource_id,
            secret_kind=SecretKind(model.secret_kind), ciphertext=model.ciphertext,  # noqa: E501
            key_version=model.key_version,
            rotated_at=_restore_utc(model.rotated_at),
        )
