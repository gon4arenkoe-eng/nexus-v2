"""Phase 10 tenancy, settings, product access and secret persistence."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class WorkspaceModel(PersistenceBase):
    __tablename__ = "workspaces"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501


class WorkspaceMembershipModel(PersistenceBase):
    __tablename__ = "workspace_memberships"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ResourceOwnershipModel(PersistenceBase):
    __tablename__ = "resource_ownership"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(80), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # noqa: E501


class SettingVersionModel(PersistenceBase):
    __tablename__ = "setting_versions"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    scope: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    safety_critical: Mapped[bool] = mapped_column(Boolean, nullable=False)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501


class AuditEventModel(PersistenceBase):
    __tablename__ = "audit_events"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(200), nullable=False)
    old_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501


class ProductPlanModel(PersistenceBase):
    __tablename__ = "product_plans"
    plan_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)


class ProductPlanVersionModel(PersistenceBase):
    __tablename__ = "product_plan_versions"
    plan_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    entitlements_json: Mapped[str] = mapped_column(Text, nullable=False)
    quotas_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class QuotaUsageModel(PersistenceBase):
    __tablename__ = "quota_usage"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    quota_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    period_key: Mapped[str] = mapped_column(String(120), primary_key=True)
    usage: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SubscriptionModel(PersistenceBase):
    __tablename__ = "workspace_subscriptions"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)  # noqa: E501
    plan_id: Mapped[str] = mapped_column(String(120), nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501


class EntitlementOverrideModel(PersistenceBase):
    __tablename__ = "entitlement_overrides"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    override_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    feature_key: Mapped[str] = mapped_column(String(200), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # noqa: E501


class BillingEventModel(PersistenceBase):
    __tablename__ = "billing_events"
    provider: Mapped[str] = mapped_column(String(80), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501


class EncryptedSecretModel(PersistenceBase):
    __tablename__ = "encrypted_secrets"
    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    secret_kind: Mapped[str] = mapped_column(String(64), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[str] = mapped_column(String(80), nullable=False)
    rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501
