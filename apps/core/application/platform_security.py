"""Pure application services for Phase 10 tenancy, settings and access."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Iterable

from packages.contracts.product_access import (
    EntitlementOverride,
    FeatureKey,
    PlanVersion,
    QuotaSnapshot,
    Subscription,
    SubscriptionState,
)
from packages.contracts.security import (
    AccessDecision,
    AuditEvent,
    Permission,
    ResourceOwnership,
    SecretConsumer,
    WorkspaceMembership,
    permissions_for_role,
)
from packages.contracts.settings import ResolvedSetting, SettingValue


class AccessControlError(RuntimeError):
    pass


class SafetyAction(StrEnum):
    CANCEL_ORDER = "CANCEL_ORDER"
    CLOSE_POSITION = "CLOSE_POSITION"
    REDUCE_POSITION = "REDUCE_POSITION"
    RECONCILIATION = "RECONCILIATION"
    PROTECTION_MANAGEMENT = "PROTECTION_MANAGEMENT"
    RECOVERY = "RECOVERY"


_RISK_REDUCING = frozenset(SafetyAction)


class AccessControlService:
    def decide(
        self,
        *,
        membership: WorkspaceMembership | None,
        permission: Permission,
        ownership: ResourceOwnership | None = None,
    ) -> AccessDecision:
        if membership is None or not membership.active:
            return AccessDecision("UNKNOWN", 0, permission, False, "no active membership")  # noqa: E501
        if ownership is not None and ownership.workspace_id != membership.workspace_id:  # noqa: E501
            return AccessDecision(membership.workspace_id, membership.user_id, permission, False, "cross-tenant resource")  # noqa: E501
        granted = permission in permissions_for_role(membership.role)
        return AccessDecision(
            membership.workspace_id,
            membership.user_id,
            permission,
            granted,
            "role permission" if granted else "permission denied",
        )


class SecretAccessPolicy:
    @staticmethod
    def require_allowed(consumer: SecretConsumer) -> None:
        if consumer is SecretConsumer.AIEA_WORKER:
            raise AccessControlError("AIEA workers cannot access credentials")
        if consumer not in {
            SecretConsumer.CORE_VENUE_ADAPTER,
            SecretConsumer.CONTROL_PLANE_CREDENTIAL_ADMIN,
        }:
            raise AccessControlError("unknown secret consumer")


class SettingsResolver:
    def resolve(self, *, key: str, candidates: Iterable[SettingValue]) -> ResolvedSetting:  # noqa: E501
        values = [value for value in candidates if value.key == key]
        if not values:
            raise KeyError(key)
        workspaces = {value.workspace_id for value in values}
        if len(workspaces) != 1:
            raise AccessControlError("cross-tenant settings resolution")
        selected = max(values, key=lambda value: (int(value.scope), value.version))  # noqa: E501
        return ResolvedSetting(
            key=selected.key,
            value_json=selected.value_json,
            source_scope=selected.scope,
            source_scope_id=selected.scope_id,
            source_version=selected.version,
        )


class ProductAccessService:
    def entitlement_granted(
        self,
        *,
        subscription: Subscription,
        plan_version: PlanVersion,
        feature_key: FeatureKey,
        overrides: Iterable[EntitlementOverride] = (),
        now: datetime,
    ) -> bool:
        if (
            subscription.plan_id != plan_version.plan_id
            or subscription.plan_version != plan_version.version
        ):
            raise AccessControlError("subscription/plan version mismatch")
        active_override = [
            item for item in overrides
            if item.workspace_id == subscription.workspace_id
            and item.feature_key == feature_key
            and (item.expires_at is None or item.expires_at > now)
        ]
        if active_override:
            return active_override[-1].granted
        if subscription.state not in {SubscriptionState.ACTIVE, SubscriptionState.TRIALING}:  # noqa: E501
            return False
        return feature_key in plan_version.entitlements

    @staticmethod
    def quota_permitted(snapshot: QuotaSnapshot) -> bool:
        return snapshot.limit is None or snapshot.usage < snapshot.limit

    @staticmethod
    def risk_reducing_action_allowed(action: SafetyAction) -> bool:
        return action in _RISK_REDUCING


@dataclass(frozen=True, slots=True)
class SettingChangeEvidence:
    setting: SettingValue
    audit_event: AuditEvent


def setting_change_evidence(
    *,
    old: SettingValue | None,
    new: SettingValue,
    event_id: str,
    reason: str,
) -> SettingChangeEvidence:
    if old is not None:
        if old.workspace_id != new.workspace_id or old.key != new.key:
            raise AccessControlError("setting lineage mismatch")
        if new.version <= old.version:
            raise ValueError("new setting version must advance")
    if new.safety_critical and not reason.strip():
        raise ValueError("safety-critical change requires reason")
    event = AuditEvent(
        event_id=event_id,
        workspace_id=new.workspace_id,
        actor_user_id=new.actor_user_id,
        action="settings.change",
        resource_type="setting",
        resource_id=new.key,
        old_value_json=None if old is None else old.value_json,
        new_value_json=new.value_json,
        reason=reason or "non-safety setting update",
        occurred_at=new.created_at,
    )
    return SettingChangeEvidence(setting=new, audit_event=event)


def immutable_payload_hash(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()
