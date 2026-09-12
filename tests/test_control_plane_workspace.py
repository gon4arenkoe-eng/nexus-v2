from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.core.application.control_plane import (
    ControlPlaneError,
    PresentationPreferenceService,
    RealtimeScopeGuard,
    SafetyPresentationService,
    WidgetRegistry,
    WorkspaceComposer,
)
from packages.contracts.control_plane import (
    ContextBusUpdate,
    SafetySeverity,
    SafetySignal,
    SafetySignalKind,
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetCategory,
    WidgetDefinition,
    WidgetInstance,
    WorkspaceLayoutVersion,
    WorkspaceTemplate,
)
from packages.contracts.product_access import FeatureKey
from packages.contracts.workspace import (
    ContextKey,
    SafetyPresentationPolicy,
    WidgetManifest,
    WidgetPlacement,
    WidgetSize,
)

NOW = datetime(2026, 9, 12, 20, 0, tzinfo=UTC)


def _definition(
    key: str,
    *,
    contexts: frozenset[ContextKey] = frozenset(),
    feature: FeatureKey | None = None,
    permission: str | None = None,
    safety: SafetyPresentationPolicy = SafetyPresentationPolicy.STANDARD,
) -> WidgetDefinition:
    return WidgetDefinition(
        manifest=WidgetManifest(
            widget_key=key,
            version=1,
            supported_context_keys=contexts,
            minimum_size=WidgetSize(2, 2),
            default_size=WidgetSize(4, 3),
            required_feature=feature,
            required_permission=permission,
            safety_policy=safety,
        ),
        category=WidgetCategory.TRADING,
        title_key=f"widget.{key}.title",
        description_key=f"widget.{key}.description",
    )


def _instance(
    instance_id: str,
    key: str,
    *,
    group: str | None = None,
    column: int = 0,
) -> WidgetInstance:
    return WidgetInstance(
        placement=WidgetPlacement(
            instance_id=instance_id,
            widget_key=key,
            widget_version=1,
            column=column,
            row=0,
            size=WidgetSize(4, 3),
            context_group=group,
        ),
        settings_json='{"timeframe":"1h"}',
    )


def test_supported_locales_cover_approved_languages() -> None:
    assert {item.value for item in SupportedLocale} == {
        "en",
        "ru",
        "de",
        "fr",
        "es",
        "zh-CN",
        "hi",
    }


def test_widget_registry_is_entitlement_and_permission_aware() -> None:
    feature = FeatureKey("workspace.layout.save")
    registry = WidgetRegistry(
        (
            _definition(
                "portfolio.positions",
                feature=feature,
                permission="workspace.read",
            ),
        )
    )
    denied = registry.availability(
        features=frozenset(),
        permissions=frozenset(),
    )
    assert denied[0].discoverable is True
    assert denied[0].usable is False

    allowed = registry.availability(
        features=frozenset({feature}),
        permissions=frozenset({"workspace.read"}),
    )
    assert allowed[0].usable is True


def test_template_access_is_tenant_scoped_and_private_user_scoped() -> None:
    registry = WidgetRegistry((_definition("portfolio.positions"),))
    composer = WorkspaceComposer(registry)
    template = WorkspaceTemplate(
        template_key="private-desk",
        version=1,
        title_key="template.private",
        widgets=(_instance("p1", "portfolio.positions"),),
        owner_workspace_id="tenant-a",
        owner_user_id=7,
        shared=False,
        created_at=NOW,
    )
    with pytest.raises(ControlPlaneError, match="cross-tenant"):
        composer.from_template(
            template=template,
            tenant_workspace_id="tenant-b",
            user_workspace_id="desk",
            user_id=7,
            created_at=NOW,
        )
    with pytest.raises(ControlPlaneError, match="private"):
        composer.from_template(
            template=template,
            tenant_workspace_id="tenant-a",
            user_workspace_id="desk",
            user_id=8,
            created_at=NOW,
        )


def test_layout_versioning_and_restore_are_immutable_lineage() -> None:
    registry = WidgetRegistry((_definition("portfolio.positions"),))
    composer = WorkspaceComposer(registry)
    v1 = WorkspaceLayoutVersion(
        tenant_workspace_id="tenant-a",
        user_workspace_id="desk",
        user_id=7,
        version=1,
        widgets=(_instance("p1", "portfolio.positions"),),
        created_at=NOW,
    )
    v2 = composer.next_version(
        previous=v1,
        widgets=(
            _instance("p1", "portfolio.positions"),
            _instance("p2", "portfolio.positions", column=4),
        ),
        created_at=NOW,
    )
    restored = composer.restore(current=v2, target=v1, created_at=NOW)
    assert v2.version == 2
    assert v2.source_version == 1
    assert restored.version == 3
    assert restored.source_version == 1
    assert restored.widgets == v1.widgets


def test_context_bus_propagates_only_to_compatible_linked_widgets() -> None:
    registry = WidgetRegistry(
        (
            _definition(
                "portfolio.positions",
                contexts=frozenset({ContextKey.INSTRUMENT_ID}),
            ),
            _definition("audit.events"),
        )
    )
    composer = WorkspaceComposer(registry)
    layout = WorkspaceLayoutVersion(
        tenant_workspace_id="tenant-a",
        user_workspace_id="desk",
        user_id=7,
        version=1,
        widgets=(
            _instance("p1", "portfolio.positions", group="market"),
            _instance("p2", "portfolio.positions", group="other", column=4),
            _instance("a1", "audit.events", group="market", column=8),
        ),
        created_at=NOW,
    )
    update = ContextBusUpdate(
        tenant_workspace_id="tenant-a",
        user_workspace_id="desk",
        user_id=7,
        context_group="market",
        key=ContextKey.INSTRUMENT_ID,
        value="BTC-PERP",
        sequence=9,
    )
    deliveries = composer.propagate_context(layout=layout, update=update)
    assert [item.widget_instance_id for item in deliveries] == ["p1"]
    assert deliveries[0].value == "BTC-PERP"


def test_context_bus_rejects_cross_user_or_cross_tenant_update() -> None:
    registry = WidgetRegistry((_definition("portfolio.positions"),))
    composer = WorkspaceComposer(registry)
    layout = WorkspaceLayoutVersion(
        tenant_workspace_id="tenant-a",
        user_workspace_id="desk",
        user_id=7,
        version=1,
        widgets=(_instance("p1", "portfolio.positions"),),
        created_at=NOW,
    )
    update = ContextBusUpdate(
        tenant_workspace_id="tenant-b",
        user_workspace_id="desk",
        user_id=7,
        context_group="market",
        key=ContextKey.INSTRUMENT_ID,
        value="BTC-PERP",
        sequence=1,
    )
    with pytest.raises(ControlPlaneError, match="ownership"):
        composer.propagate_context(layout=layout, update=update)


def test_mandatory_safety_surface_cannot_be_suppressed_by_layout() -> None:
    signals = (
        SafetySignal(
            tenant_workspace_id="tenant-a",
            kind=SafetySignalKind.RISK_LIMIT_BREACH,
            severity=SafetySeverity.CRITICAL,
            message_key="safety.risk",
            observed_at=NOW,
        ),
        SafetySignal(
            tenant_workspace_id="tenant-b",
            kind=SafetySignalKind.MARKET_DATA_UNHEALTHY,
            severity=SafetySeverity.WARNING,
            message_key="safety.market",
            observed_at=NOW,
        ),
    )
    surface = SafetyPresentationService.build_surface(
        tenant_workspace_id="tenant-a",
        signals=signals,
    )
    assert surface.visible is True
    assert surface.maximum_severity is SafetySeverity.CRITICAL
    assert len(surface.signals) == 1
    assert SafetyPresentationService.layout_can_suppress_safety() is False


def test_realtime_scope_guard_denies_cross_tenant_or_cross_user_data() -> None:
    RealtimeScopeGuard.require_scope(
        tenant_workspace_id="tenant-a",
        user_id=7,
        event_tenant_workspace_id="tenant-a",
        event_user_id=7,
    )
    with pytest.raises(ControlPlaneError, match="realtime"):
        RealtimeScopeGuard.require_scope(
            tenant_workspace_id="tenant-a",
            user_id=7,
            event_tenant_workspace_id="tenant-b",
            event_user_id=7,
        )
    with pytest.raises(ControlPlaneError, match="realtime"):
        RealtimeScopeGuard.require_scope(
            tenant_workspace_id="tenant-a",
            user_id=7,
            event_tenant_workspace_id="tenant-a",
            event_user_id=8,
        )


def test_user_locale_and_theme_are_presentation_preferences() -> None:
    workspace = UserWorkspace(
        tenant_workspace_id="tenant-a",
        user_workspace_id="desk",
        user_id=7,
        name="Desk",
        locale=SupportedLocale.ENGLISH,
        theme=ThemePreference.DARK,
        active_layout_version=1,
        created_at=NOW,
        updated_at=NOW,
    )
    updated = PresentationPreferenceService.update_workspace_preferences(
        workspace,
        locale=SupportedLocale.RUSSIAN,
        theme=ThemePreference.LIGHT,
        updated_at=NOW,
    )
    assert updated.locale is SupportedLocale.RUSSIAN
    assert updated.theme is ThemePreference.LIGHT
    assert updated.tenant_workspace_id == workspace.tenant_workspace_id
