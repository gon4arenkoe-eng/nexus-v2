"""Typed Control Plane presentation, workspace and realtime contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum

from packages.contracts.primitives import normalize_utc_datetime
from packages.contracts.workspace import (
    ContextKey,
    WidgetManifest,
    WidgetPlacement,
)


def _text(value: str, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty")
    return normalized


def _positive_int(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


class SupportedLocale(StrEnum):
    ENGLISH = "en"
    RUSSIAN = "ru"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    CHINESE_SIMPLIFIED = "zh-CN"
    HINDI = "hi"


class ThemePreference(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class WidgetCategory(StrEnum):
    OVERVIEW = "overview"
    TRADING = "trading"
    GRID = "grid"
    RISK = "risk"
    OPERATIONS = "operations"
    INTELLIGENCE = "intelligence"
    AIEA = "aiea"
    ADMIN = "admin"


class SafetySeverity(IntEnum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3


class SafetySignalKind(StrEnum):
    RECONCILIATION_UNHEALTHY = "reconciliation.unhealthy"
    MARKET_DATA_UNHEALTHY = "market_data.unhealthy"
    TRADING_DISABLED = "trading.disabled"
    KILL_SWITCH_ACTIVE = "kill_switch.active"
    RISK_LIMIT_BREACH = "risk.limit_breach"
    EXECUTION_OUTCOME_UNKNOWN = "execution.outcome_unknown"
    PROTECTION_FAILURE = "protection.failure"
    VENUE_CONNECTIVITY_FAILURE = "venue.connectivity_failure"


@dataclass(frozen=True, slots=True)
class WidgetDefinition:
    manifest: WidgetManifest
    category: WidgetCategory
    title_key: str
    description_key: str
    realtime_channel: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, WidgetManifest):
            raise ValueError("manifest must be WidgetManifest")
        if not isinstance(self.category, WidgetCategory):
            raise ValueError("category must be WidgetCategory")
        object.__setattr__(
            self,
            "title_key",
            _text(self.title_key, name="title_key"),
        )
        object.__setattr__(
            self,
            "description_key",
            _text(self.description_key, name="description_key"),
        )
        if self.realtime_channel is not None:
            object.__setattr__(
                self,
                "realtime_channel",
                _text(self.realtime_channel, name="realtime_channel"),
            )


@dataclass(frozen=True, slots=True)
class WidgetInstance:
    placement: WidgetPlacement
    settings_json: str = "{}"

    def __post_init__(self) -> None:
        if not isinstance(self.placement, WidgetPlacement):
            raise ValueError("placement must be WidgetPlacement")
        object.__setattr__(
            self,
            "settings_json",
            _text(self.settings_json, name="settings_json"),
        )


@dataclass(frozen=True, slots=True)
class UserWorkspace:
    tenant_workspace_id: str
    user_workspace_id: str
    user_id: int
    name: str
    locale: SupportedLocale
    theme: ThemePreference
    active_layout_version: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for name in ("tenant_workspace_id", "user_workspace_id", "name"):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        _positive_int(self.user_id, name="user_id")
        if not isinstance(self.locale, SupportedLocale):
            raise ValueError("locale must be SupportedLocale")
        if not isinstance(self.theme, ThemePreference):
            raise ValueError("theme must be ThemePreference")
        _positive_int(self.active_layout_version, name="active_layout_version")
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(self.created_at, field_name="created_at"),
        )
        object.__setattr__(
            self,
            "updated_at",
            normalize_utc_datetime(self.updated_at, field_name="updated_at"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceLayoutVersion:
    tenant_workspace_id: str
    user_workspace_id: str
    user_id: int
    version: int
    widgets: tuple[WidgetInstance, ...]
    created_at: datetime
    source_version: int | None = None

    def __post_init__(self) -> None:
        for name in ("tenant_workspace_id", "user_workspace_id"):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        _positive_int(self.user_id, name="user_id")
        _positive_int(self.version, name="version")
        if not isinstance(self.widgets, tuple) or not all(
            isinstance(item, WidgetInstance) for item in self.widgets
        ):
            raise ValueError("widgets must be tuple[WidgetInstance, ...]")
        instance_ids = [item.placement.instance_id for item in self.widgets]
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("widget instance ids must be unique")
        for item in self.widgets:
            placement = item.placement
            if placement.column + placement.size.columns > 24:
                raise ValueError("widget placement exceeds 24-column canvas")
        if self.source_version is not None:
            _positive_int(self.source_version, name="source_version")
            if self.source_version >= self.version:
                raise ValueError("source_version must precede version")
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(self.created_at, field_name="created_at"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceTemplate:
    template_key: str
    version: int
    title_key: str
    widgets: tuple[WidgetInstance, ...]
    created_at: datetime
    owner_workspace_id: str | None = None
    owner_user_id: int | None = None
    shared: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "template_key",
            _text(self.template_key, name="template_key").lower(),
        )
        _positive_int(self.version, name="version")
        object.__setattr__(
            self,
            "title_key",
            _text(self.title_key, name="title_key"),
        )
        if not isinstance(self.widgets, tuple) or not all(
            isinstance(item, WidgetInstance) for item in self.widgets
        ):
            raise ValueError("widgets must be tuple[WidgetInstance, ...]")
        if self.owner_workspace_id is not None:
            object.__setattr__(
                self,
                "owner_workspace_id",
                _text(self.owner_workspace_id, name="owner_workspace_id"),
            )
            if self.owner_user_id is None:
                raise ValueError("tenant template requires owner_user_id")
        elif self.owner_user_id is not None:
            raise ValueError("curated template cannot have owner_user_id")
        if self.owner_user_id is not None:
            _positive_int(self.owner_user_id, name="owner_user_id")
        if not isinstance(self.shared, bool):
            raise ValueError("shared must be bool")
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(self.created_at, field_name="created_at"),
        )


@dataclass(frozen=True, slots=True)
class WidgetAvailability:
    widget_key: str
    widget_version: int
    discoverable: bool
    usable: bool
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "widget_key",
            _text(self.widget_key, name="widget_key").lower(),
        )
        _positive_int(self.widget_version, name="widget_version")
        if (
            not isinstance(self.discoverable, bool)
            or not isinstance(self.usable, bool)
        ):
            raise ValueError("discoverable and usable must be bool")
        if self.usable and not self.discoverable:
            raise ValueError("usable widget must be discoverable")
        object.__setattr__(self, "reason", _text(self.reason, name="reason"))


@dataclass(frozen=True, slots=True)
class ContextBusUpdate:
    tenant_workspace_id: str
    user_workspace_id: str
    user_id: int
    context_group: str
    key: ContextKey
    value: str
    sequence: int

    def __post_init__(self) -> None:
        for name in (
            "tenant_workspace_id",
            "user_workspace_id",
            "context_group",
            "value",
        ):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        _positive_int(self.user_id, name="user_id")
        if not isinstance(self.key, ContextKey):
            raise ValueError("key must be ContextKey")
        _positive_int(self.sequence, name="sequence")


@dataclass(frozen=True, slots=True)
class ContextDelivery:
    widget_instance_id: str
    key: ContextKey
    value: str
    sequence: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "widget_instance_id",
            _text(self.widget_instance_id, name="widget_instance_id"),
        )
        if not isinstance(self.key, ContextKey):
            raise ValueError("key must be ContextKey")
        object.__setattr__(self, "value", _text(self.value, name="value"))
        _positive_int(self.sequence, name="sequence")


@dataclass(frozen=True, slots=True)
class SafetySignal:
    tenant_workspace_id: str
    kind: SafetySignalKind
    severity: SafetySeverity
    message_key: str
    observed_at: datetime
    active: bool = True
    resource_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_workspace_id",
            _text(self.tenant_workspace_id, name="tenant_workspace_id"),
        )
        if not isinstance(self.kind, SafetySignalKind):
            raise ValueError("kind must be SafetySignalKind")
        if not isinstance(self.severity, SafetySeverity):
            raise ValueError("severity must be SafetySeverity")
        object.__setattr__(
            self,
            "message_key",
            _text(self.message_key, name="message_key"),
        )
        if not isinstance(self.active, bool):
            raise ValueError("active must be bool")
        if self.resource_id is not None:
            object.__setattr__(
                self,
                "resource_id",
                _text(self.resource_id, name="resource_id"),
            )
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(self.observed_at, field_name="observed_at"),
        )


@dataclass(frozen=True, slots=True)
class MandatorySafetySurface:
    tenant_workspace_id: str
    signals: tuple[SafetySignal, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_workspace_id",
            _text(self.tenant_workspace_id, name="tenant_workspace_id"),
        )
        if not isinstance(self.signals, tuple) or not all(
            isinstance(item, SafetySignal) for item in self.signals
        ):
            raise ValueError("signals must be tuple[SafetySignal, ...]")
        if any(
            item.tenant_workspace_id != self.tenant_workspace_id
            for item in self.signals
        ):
            raise ValueError("safety signal tenant mismatch")
        if any(not item.active for item in self.signals):
            raise ValueError(
                "mandatory safety surface contains inactive signal"
            )

    @property
    def visible(self) -> bool:
        return bool(self.signals)

    @property
    def maximum_severity(self) -> SafetySeverity | None:
        if not self.signals:
            return None
        return max(item.severity for item in self.signals)


@dataclass(frozen=True, slots=True)
class RealtimeWidgetEvent:
    tenant_workspace_id: str
    user_id: int
    channel: str
    sequence: int
    schema_version: int
    payload_json: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_workspace_id",
            _text(self.tenant_workspace_id, name="tenant_workspace_id"),
        )
        _positive_int(self.user_id, name="user_id")
        object.__setattr__(
            self,
            "channel",
            _text(self.channel, name="channel"),
        )
        _positive_int(self.sequence, name="sequence")
        _positive_int(self.schema_version, name="schema_version")
        object.__setattr__(
            self,
            "payload_json",
            _text(self.payload_json, name="payload_json"),
        )
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(self.occurred_at, field_name="occurred_at"),
        )
