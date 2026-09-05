"""Typed, presentation-only workspace composition contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.contracts.product_access import FeatureKey


def _required_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _positive_int(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


class ContextKey(StrEnum):
    INSTRUMENT_ID = "instrument_id"
    VENUE_ID = "venue_id"
    EXCHANGE_ACCOUNT_ID = "exchange_account_id"
    STRATEGY_ID = "strategy_id"
    STRATEGY_VERSION_ID = "strategy_version_id"
    GRID_INSTANCE_ID = "grid_instance_id"
    POSITION_GROUP_ID = "position_group_id"
    AIEA_EXPERIMENT_ID = "aiea_experiment_id"


class SafetyPresentationPolicy(StrEnum):
    STANDARD = "STANDARD"
    MANDATORY = "MANDATORY"


@dataclass(frozen=True, slots=True)
class WidgetSize:
    columns: int
    rows: int

    def __post_init__(self) -> None:
        _positive_int(self.columns, field_name="columns")
        _positive_int(self.rows, field_name="rows")


@dataclass(frozen=True, slots=True)
class WidgetManifest:
    """Versioned registry metadata; it contains no executable UI code."""

    widget_key: str
    version: int
    supported_context_keys: frozenset[ContextKey]
    minimum_size: WidgetSize
    default_size: WidgetSize
    required_feature: FeatureKey | None = None
    required_permission: str | None = None
    safety_policy: SafetyPresentationPolicy = SafetyPresentationPolicy.STANDARD

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "widget_key",
            _required_text(self.widget_key, field_name="widget_key").lower(),
        )
        _positive_int(self.version, field_name="version")
        if not isinstance(self.supported_context_keys, frozenset) or not all(
            isinstance(key, ContextKey) for key in self.supported_context_keys
        ):
            raise ValueError("supported_context_keys must be a frozenset of ContextKey")
        if not isinstance(self.minimum_size, WidgetSize):
            raise ValueError("minimum_size must be a WidgetSize")
        if not isinstance(self.default_size, WidgetSize):
            raise ValueError("default_size must be a WidgetSize")
        if self.default_size.columns < self.minimum_size.columns or self.default_size.rows < self.minimum_size.rows:
            raise ValueError("default_size must satisfy minimum_size")
        if self.required_feature is not None and not isinstance(
            self.required_feature, FeatureKey
        ):
            raise ValueError("required_feature must be a FeatureKey or None")
        if self.required_permission is not None:
            object.__setattr__(
                self,
                "required_permission",
                _required_text(
                    self.required_permission,
                    field_name="required_permission",
                ),
            )
        if not isinstance(self.safety_policy, SafetyPresentationPolicy):
            raise ValueError("safety_policy must be a SafetyPresentationPolicy")


@dataclass(frozen=True, slots=True)
class WidgetPlacement:
    instance_id: str
    widget_key: str
    widget_version: int
    column: int
    row: int
    size: WidgetSize
    context_group: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instance_id", _required_text(self.instance_id, field_name="instance_id"))
        object.__setattr__(self, "widget_key", _required_text(self.widget_key, field_name="widget_key").lower())
        _positive_int(self.widget_version, field_name="widget_version")
        if isinstance(self.column, bool) or not isinstance(self.column, int) or self.column < 0:
            raise ValueError("column must be a non-negative integer")
        if isinstance(self.row, bool) or not isinstance(self.row, int) or self.row < 0:
            raise ValueError("row must be a non-negative integer")
        if not isinstance(self.size, WidgetSize):
            raise ValueError("size must be a WidgetSize")
        if self.context_group is not None:
            object.__setattr__(self, "context_group", _required_text(self.context_group, field_name="context_group"))


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    workspace_id: str
    version: int
    widgets: tuple[WidgetPlacement, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _required_text(self.workspace_id, field_name="workspace_id"))
        _positive_int(self.version, field_name="version")
        if not isinstance(self.widgets, tuple) or not all(
            isinstance(widget, WidgetPlacement) for widget in self.widgets
        ):
            raise ValueError("widgets must be a tuple of WidgetPlacement")
        instance_ids = [widget.instance_id for widget in self.widgets]
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("widgets must have unique instance_id values")


@dataclass(frozen=True, slots=True)
class WidgetContext:
    key: ContextKey
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.key, ContextKey):
            raise ValueError("key must be a ContextKey")
        object.__setattr__(self, "value", _required_text(self.value, field_name="value"))
