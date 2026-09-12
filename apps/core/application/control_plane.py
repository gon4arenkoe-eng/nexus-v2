"""Presentation-only Control Plane workspace application services."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Iterable

from packages.contracts.control_plane import (
    ContextBusUpdate,
    ContextDelivery,
    MandatorySafetySurface,
    SafetySignal,
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetAvailability,
    WidgetDefinition,
    WidgetInstance,
    WorkspaceLayoutVersion,
    WorkspaceTemplate,
)
from packages.contracts.product_access import FeatureKey
from packages.contracts.workspace import SafetyPresentationPolicy


class ControlPlaneError(RuntimeError):
    """Fail-closed Control Plane application error."""


class WidgetRegistry:
    def __init__(self, definitions: Iterable[WidgetDefinition]) -> None:
        registry: dict[tuple[str, int], WidgetDefinition] = {}
        for definition in definitions:
            if not isinstance(definition, WidgetDefinition):
                raise ValueError("registry requires WidgetDefinition values")
            key = (definition.manifest.widget_key, definition.manifest.version)
            if key in registry:
                raise ValueError("duplicate widget definition")
            registry[key] = definition
        self._definitions = registry

    def get(self, widget_key: str, version: int) -> WidgetDefinition:
        try:
            return self._definitions[(widget_key.strip().lower(), version)]
        except KeyError as exc:
            raise ControlPlaneError(
                "widget definition is not registered"
            ) from exc

    def availability(
        self,
        *,
        features: frozenset[FeatureKey],
        permissions: frozenset[str],
    ) -> tuple[WidgetAvailability, ...]:
        result: list[WidgetAvailability] = []
        for key in sorted(self._definitions):
            definition = self._definitions[key]
            manifest = definition.manifest
            feature_granted = (
                manifest.required_feature is None
                or manifest.required_feature in features
            )
            permission_granted = (
                manifest.required_permission is None
                or manifest.required_permission in permissions
            )
            usable = feature_granted and permission_granted
            reason = "available"
            if not feature_granted:
                reason = "feature entitlement required"
            elif not permission_granted:
                reason = "role permission required"
            result.append(
                WidgetAvailability(
                    widget_key=manifest.widget_key,
                    widget_version=manifest.version,
                    discoverable=True,
                    usable=usable,
                    reason=reason,
                )
            )
        return tuple(result)


class WorkspaceComposer:
    def __init__(self, registry: WidgetRegistry) -> None:
        if not isinstance(registry, WidgetRegistry):
            raise ValueError("registry must be WidgetRegistry")
        self._registry = registry

    def validate_layout(self, layout: WorkspaceLayoutVersion) -> None:
        if not isinstance(layout, WorkspaceLayoutVersion):
            raise ValueError("layout must be WorkspaceLayoutVersion")
        for item in layout.widgets:
            definition = self._registry.get(
                item.placement.widget_key,
                item.placement.widget_version,
            )
            minimum = definition.manifest.minimum_size
            actual = item.placement.size
            if actual.columns < minimum.columns or actual.rows < minimum.rows:
                raise ControlPlaneError(
                    "widget size is below registry minimum"
                )

    def from_template(
        self,
        *,
        template: WorkspaceTemplate,
        tenant_workspace_id: str,
        user_workspace_id: str,
        user_id: int,
        created_at: datetime,
    ) -> WorkspaceLayoutVersion:
        if template.owner_workspace_id is not None:
            if template.owner_workspace_id != tenant_workspace_id:
                raise ControlPlaneError("cross-tenant template access denied")
            if not template.shared and template.owner_user_id != user_id:
                raise ControlPlaneError("private template access denied")
        layout = WorkspaceLayoutVersion(
            tenant_workspace_id=tenant_workspace_id,
            user_workspace_id=user_workspace_id,
            user_id=user_id,
            version=1,
            widgets=template.widgets,
            created_at=created_at,
        )
        self.validate_layout(layout)
        return layout

    def next_version(
        self,
        *,
        previous: WorkspaceLayoutVersion,
        widgets: tuple[WidgetInstance, ...],
        created_at: datetime,
    ) -> WorkspaceLayoutVersion:
        layout = WorkspaceLayoutVersion(
            tenant_workspace_id=previous.tenant_workspace_id,
            user_workspace_id=previous.user_workspace_id,
            user_id=previous.user_id,
            version=previous.version + 1,
            widgets=widgets,
            source_version=previous.version,
            created_at=created_at,
        )
        self.validate_layout(layout)
        return layout

    def restore(
        self,
        *,
        current: WorkspaceLayoutVersion,
        target: WorkspaceLayoutVersion,
        created_at: datetime,
    ) -> WorkspaceLayoutVersion:
        if (
            current.tenant_workspace_id != target.tenant_workspace_id
            or current.user_workspace_id != target.user_workspace_id
            or current.user_id != target.user_id
        ):
            raise ControlPlaneError("layout restore ownership mismatch")
        restored = WorkspaceLayoutVersion(
            tenant_workspace_id=current.tenant_workspace_id,
            user_workspace_id=current.user_workspace_id,
            user_id=current.user_id,
            version=current.version + 1,
            widgets=target.widgets,
            source_version=target.version,
            created_at=created_at,
        )
        self.validate_layout(restored)
        return restored

    def propagate_context(
        self,
        *,
        layout: WorkspaceLayoutVersion,
        update: ContextBusUpdate,
    ) -> tuple[ContextDelivery, ...]:
        if (
            layout.tenant_workspace_id != update.tenant_workspace_id
            or layout.user_workspace_id != update.user_workspace_id
            or layout.user_id != update.user_id
        ):
            raise ControlPlaneError("context update ownership mismatch")
        deliveries: list[ContextDelivery] = []
        for item in layout.widgets:
            placement = item.placement
            if placement.context_group != update.context_group:
                continue
            definition = self._registry.get(
                placement.widget_key,
                placement.widget_version,
            )
            if update.key not in definition.manifest.supported_context_keys:
                continue
            deliveries.append(
                ContextDelivery(
                    widget_instance_id=placement.instance_id,
                    key=update.key,
                    value=update.value,
                    sequence=update.sequence,
                )
            )
        return tuple(deliveries)


class SafetyPresentationService:
    @staticmethod
    def build_surface(
        *,
        tenant_workspace_id: str,
        signals: Iterable[SafetySignal],
    ) -> MandatorySafetySurface:
        active = tuple(
            sorted(
                (
                    item
                    for item in signals
                    if item.active
                    and item.tenant_workspace_id == tenant_workspace_id
                ),
                key=lambda item: (-int(item.severity), item.kind.value),
            )
        )
        return MandatorySafetySurface(
            tenant_workspace_id=tenant_workspace_id,
            signals=active,
        )

    @staticmethod
    def layout_can_suppress_safety() -> bool:
        return False


class PresentationPreferenceService:
    @staticmethod
    def update_workspace_preferences(
        workspace: UserWorkspace,
        *,
        locale: SupportedLocale | None = None,
        theme: ThemePreference | None = None,
        updated_at: datetime,
    ) -> UserWorkspace:
        return replace(
            workspace,
            locale=workspace.locale if locale is None else locale,
            theme=workspace.theme if theme is None else theme,
            updated_at=updated_at,
        )


def mandatory_widget_keys(
    definitions: Iterable[WidgetDefinition],
) -> frozenset[str]:
    return frozenset(
        item.manifest.widget_key
        for item in definitions
        if item.manifest.safety_policy is SafetyPresentationPolicy.MANDATORY
    )


class RealtimeScopeGuard:
    @staticmethod
    def require_scope(
        *,
        tenant_workspace_id: str,
        user_id: int,
        event_tenant_workspace_id: str,
        event_user_id: int,
    ) -> None:
        if (
            tenant_workspace_id != event_tenant_workspace_id
            or user_id != event_user_id
        ):
            raise ControlPlaneError("cross-tenant realtime event denied")
