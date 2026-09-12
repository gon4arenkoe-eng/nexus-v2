from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from apps.core.application.platform_security import (
    AccessControlError,
    AccessControlService,
    ProductAccessService,
    SafetyAction,
    SecretAccessPolicy,
    SettingsResolver,
    setting_change_evidence,
)
from packages.contracts.product_access import (
    EntitlementOverride,
    FeatureKey,
    PlanVersion,
    ProductPlan,
    QuotaDefinition,
    QuotaSnapshot,
    Subscription,
    SubscriptionState,
)
from packages.contracts.security import (
    BackgroundJobScope,
    EncryptedSecretEnvelope,
    Permission,
    RealtimeEventScope,
    ResourceOwnership,
    SecretConsumer,
    SecretKind,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
    permissions_for_role,
)
from packages.contracts.settings import SettingDomain, SettingScope, SettingValue  # noqa: E501

NOW = datetime(2026, 9, 12, 18, 0, tzinfo=UTC)


def membership(role: WorkspaceRole, *, workspace: str = "ws-a", user: int = 7) -> WorkspaceMembership:  # noqa: E501
    return WorkspaceMembership(workspace, user, role)


def setting(scope: SettingScope, version: int, value: str, *, workspace: str = "ws-a", safety: bool = False) -> SettingValue:  # noqa: E501
    return SettingValue(
        workspace_id=workspace,
        key="risk.max_notional",
        domain=SettingDomain.PORTFOLIO_RISK,
        scope=scope,
        scope_id=scope.name.lower(),
        value_json=value,
        version=version,
        safety_critical=safety,
        actor_user_id=7,
        created_at=NOW,
    )


def test_workspace_requires_positive_owner() -> None:
    with pytest.raises(ValueError):
        Workspace("ws", "Desk", 0, NOW)


def test_role_matrix_owner_has_all_permissions() -> None:
    assert permissions_for_role(WorkspaceRole.OWNER) == frozenset(Permission)


def test_viewer_is_read_only() -> None:
    assert permissions_for_role(WorkspaceRole.VIEWER) == {Permission.WORKSPACE_READ}  # noqa: E501


def test_trader_cannot_manage_credentials_or_live_permissions() -> None:
    permissions = permissions_for_role(WorkspaceRole.TRADER)
    assert Permission.CREDENTIAL_MANAGE not in permissions
    assert Permission.LIVE_PERMISSION_CHANGE not in permissions
    assert Permission.RISK_LIMIT_CHANGE not in permissions


def test_admin_cannot_change_live_permission_or_approve_aiea_promotion() -> None:  # noqa: E501
    permissions = permissions_for_role(WorkspaceRole.ADMIN)
    assert Permission.LIVE_PERMISSION_CHANGE not in permissions
    assert Permission.AIEA_PROMOTION_APPROVE not in permissions


def test_owner_can_change_live_permissions_but_safety_still_separate() -> None:
    assert Permission.LIVE_PERMISSION_CHANGE in permissions_for_role(WorkspaceRole.OWNER)  # noqa: E501


def test_cross_tenant_resource_fails_closed_even_for_owner() -> None:
    decision = AccessControlService().decide(
        membership=membership(WorkspaceRole.OWNER),
        permission=Permission.WORKSPACE_READ,
        ownership=ResourceOwnership("ws-b", "grid", "grid-1"),
    )
    assert decision.granted is False
    assert decision.reason == "cross-tenant resource"


def test_inactive_membership_fails_closed() -> None:
    decision = AccessControlService().decide(
        membership=WorkspaceMembership("ws-a", 7, WorkspaceRole.OWNER, active=False),  # noqa: E501
        permission=Permission.WORKSPACE_READ,
    )
    assert decision.granted is False


def test_role_permission_grants_expected_action() -> None:
    decision = AccessControlService().decide(
        membership=membership(WorkspaceRole.TRADER),
        permission=Permission.STRATEGY_ACTIVATE,
    )
    assert decision.granted is True


def test_settings_precedence_uses_highest_scope() -> None:
    resolved = SettingsResolver().resolve(
        key="risk.max_notional",
        candidates=(
            setting(SettingScope.SYSTEM_DEFAULT, 1, "100"),
            setting(SettingScope.WORKSPACE, 1, "90"),
            setting(SettingScope.RISK_PROFILE, 2, "70"),
            setting(SettingScope.SESSION_OVERRIDE, 1, "50"),
        ),
    )
    assert resolved.value_json == "50"
    assert resolved.source_scope is SettingScope.SESSION_OVERRIDE


def test_settings_same_scope_uses_latest_version() -> None:
    resolved = SettingsResolver().resolve(
        key="risk.max_notional",
        candidates=(
            setting(SettingScope.WORKSPACE, 1, "90"),
            setting(SettingScope.WORKSPACE, 2, "80"),
        ),
    )
    assert resolved.value_json == "80"
    assert resolved.source_version == 2


def test_settings_resolution_rejects_cross_tenant_mix() -> None:
    with pytest.raises(AccessControlError):
        SettingsResolver().resolve(
            key="risk.max_notional",
            candidates=(
                setting(SettingScope.WORKSPACE, 1, "90", workspace="ws-a"),
                setting(SettingScope.SESSION_OVERRIDE, 1, "50", workspace="ws-b"),  # noqa: E501
            ),
        )


def test_safety_critical_setting_change_requires_reason() -> None:
    with pytest.raises(ValueError):
        setting_change_evidence(
            old=None,
            new=setting(SettingScope.WORKSPACE, 1, "80", safety=True),
            event_id="event-1",
            reason="",
        )


def test_setting_change_emits_old_new_actor_audit() -> None:
    old = setting(SettingScope.WORKSPACE, 1, "90", safety=True)
    new = setting(SettingScope.WORKSPACE, 2, "80", safety=True)
    evidence = setting_change_evidence(
        old=old,
        new=new,
        event_id="event-1",
        reason="approved risk tightening",
    )
    assert evidence.audit_event.old_value_json == "90"
    assert evidence.audit_event.new_value_json == "80"
    assert evidence.audit_event.actor_user_id == 7


def test_setting_version_must_advance() -> None:
    with pytest.raises(ValueError):
        setting_change_evidence(
            old=setting(SettingScope.WORKSPACE, 2, "90"),
            new=setting(SettingScope.WORKSPACE, 2, "80"),
            event_id="event-1",
            reason="change",
        )


def test_secret_repr_never_contains_ciphertext() -> None:
    secret = EncryptedSecretEnvelope(
        workspace_id="ws-a",
        resource_id="account-1",
        secret_kind=SecretKind.EXCHANGE_API_SECRET,
        ciphertext="super-secret-ciphertext",
        key_version="kms-v2",
        rotated_at=NOW,
    )
    assert "super-secret-ciphertext" not in repr(secret)
    assert "<redacted>" in repr(secret)


def test_secret_rotation_version_is_explicit() -> None:
    secret = EncryptedSecretEnvelope(
        "ws-a", "account-1", SecretKind.EXCHANGE_API_KEY,
        "cipher", "kms-v3", NOW,
    )
    assert secret.key_version == "kms-v3"


def test_background_job_is_tenant_and_user_scoped() -> None:
    scope = BackgroundJobScope("ws-a", 7, "job-1")
    assert (scope.workspace_id, scope.user_id) == ("ws-a", 7)


def test_realtime_event_is_tenant_and_user_scoped() -> None:
    scope = RealtimeEventScope("ws-a", 7, "orders")
    assert scope.workspace_id == "ws-a"


def test_plan_name_is_commercial_only() -> None:
    assert ProductPlan("pro-2026", "Pro").display_name == "Pro"


def test_plan_version_is_immutable_feature_bundle() -> None:
    version = PlanVersion(
        plan_id="pro-2026",
        version=2,
        entitlements=frozenset({FeatureKey("grid.instance.create")}),
        quotas=(QuotaDefinition(FeatureKey("workspace.member.create"), 5),),
        created_at=NOW,
    )
    assert FeatureKey("grid.instance.create") in version.entitlements


def test_active_subscription_grants_entitlement() -> None:
    plan = PlanVersion(
        "pro", 1,
        frozenset({FeatureKey("grid.instance.create")}),
        (), NOW,
    )
    sub = Subscription("sub-1", "ws-a", "pro", 1, SubscriptionState.ACTIVE, NOW)  # noqa: E501
    assert ProductAccessService().entitlement_granted(
        subscription=sub,
        plan_version=plan,
        feature_key=FeatureKey("grid.instance.create"),
        now=NOW,
    )


def test_expired_subscription_denies_new_premium_action() -> None:
    plan = PlanVersion("pro", 1, frozenset({FeatureKey("grid.instance.create")}), (), NOW)  # noqa: E501
    sub = Subscription("sub-1", "ws-a", "pro", 1, SubscriptionState.EXPIRED, NOW)  # noqa: E501
    assert not ProductAccessService().entitlement_granted(
        subscription=sub, plan_version=plan,
        feature_key=FeatureKey("grid.instance.create"), now=NOW,
    )


def test_entitlement_override_is_tenant_scoped() -> None:
    plan = PlanVersion("basic", 1, frozenset(), (), NOW)
    sub = Subscription("sub-1", "ws-a", "basic", 1, SubscriptionState.ACTIVE, NOW)  # noqa: E501
    override = EntitlementOverride(
        "ov-1", "ws-a", FeatureKey("aiea.experiment.run"), True,
        1, "beta", NOW, NOW + timedelta(days=1),
    )
    assert ProductAccessService().entitlement_granted(
        subscription=sub, plan_version=plan,
        feature_key=FeatureKey("aiea.experiment.run"),
        overrides=(override,), now=NOW,
    )


def test_expired_override_does_not_grant() -> None:
    plan = PlanVersion("basic", 1, frozenset(), (), NOW)
    sub = Subscription("sub-1", "ws-a", "basic", 1, SubscriptionState.ACTIVE, NOW)  # noqa: E501
    override = EntitlementOverride(
        "ov-1", "ws-a", FeatureKey("aiea.experiment.run"), True,
        1, "beta", NOW - timedelta(days=2), NOW - timedelta(days=1),
    )
    assert not ProductAccessService().entitlement_granted(
        subscription=sub, plan_version=plan,
        feature_key=FeatureKey("aiea.experiment.run"),
        overrides=(override,), now=NOW,
    )


def test_plan_version_mismatch_fails_closed() -> None:
    plan = PlanVersion("pro", 2, frozenset(), (), NOW)
    sub = Subscription("sub-1", "ws-a", "pro", 1, SubscriptionState.ACTIVE, NOW)  # noqa: E501
    with pytest.raises(AccessControlError):
        ProductAccessService().entitlement_granted(
            subscription=sub, plan_version=plan,
            feature_key=FeatureKey("grid.instance.create"), now=NOW,
        )


def test_quota_snapshot_enforces_limit() -> None:
    service = ProductAccessService()
    assert service.quota_permitted(QuotaSnapshot("ws-a", FeatureKey("workspace.member.create"), 4, 5, "2026-09"))  # noqa: E501
    assert not service.quota_permitted(QuotaSnapshot("ws-a", FeatureKey("workspace.member.create"), 5, 5, "2026-09"))  # noqa: E501


def test_unlimited_quota_is_permitted() -> None:
    assert ProductAccessService.quota_permitted(
        QuotaSnapshot("ws-a", FeatureKey("aiea.experiment.run"), 1000, None, "2026-09")  # noqa: E501
    )


@pytest.mark.parametrize("action", list(SafetyAction))
def test_billing_can_never_disable_risk_reducing_action(action: SafetyAction) -> None:  # noqa: E501
    assert ProductAccessService.risk_reducing_action_allowed(action)


def test_aiea_worker_cannot_access_exchange_credentials() -> None:
    with pytest.raises(AccessControlError):
        SecretAccessPolicy.require_allowed(SecretConsumer.AIEA_WORKER)


def test_core_venue_adapter_can_use_secret_boundary() -> None:
    SecretAccessPolicy.require_allowed(SecretConsumer.CORE_VENUE_ADAPTER)
