from __future__ import annotations

import pytest

from packages.contracts.product_access import FeatureKey
from packages.contracts.workspace import (
    ContextKey,
    SafetyPresentationPolicy,
    WidgetContext,
    WidgetManifest,
    WidgetPlacement,
    WidgetSize,
    WorkspaceLayout,
)


def test_widget_manifest_declares_typed_capability_and_context() -> None:
    manifest = WidgetManifest(
        widget_key="portfolio.positions",
        version=1,
        supported_context_keys=frozenset({ContextKey.INSTRUMENT_ID, ContextKey.VENUE_ID}),
        minimum_size=WidgetSize(columns=2, rows=2),
        default_size=WidgetSize(columns=4, rows=3),
        required_feature=FeatureKey("workspace.layout.save"),
        required_permission="workspace.read",
        safety_policy=SafetyPresentationPolicy.MANDATORY,
    )
    assert manifest.required_feature == FeatureKey("workspace.layout.save")


def test_widget_manifest_rejects_default_size_below_minimum() -> None:
    with pytest.raises(ValueError):
        WidgetManifest(
            widget_key="portfolio.positions",
            version=1,
            supported_context_keys=frozenset(),
            minimum_size=WidgetSize(columns=4, rows=3),
            default_size=WidgetSize(columns=2, rows=2),
        )


def test_workspace_layout_requires_unique_widget_instances() -> None:
    widget = WidgetPlacement(
        instance_id="positions-1",
        widget_key="portfolio.positions",
        widget_version=1,
        column=0,
        row=0,
        size=WidgetSize(columns=4, rows=3),
        context_group="desk-a",
    )
    with pytest.raises(ValueError):
        WorkspaceLayout("workspace-1", 1, (widget, widget))


def test_context_is_typed_and_presentation_only() -> None:
    context = WidgetContext(ContextKey.INSTRUMENT_ID, "instrument-1")
    assert context.key is ContextKey.INSTRUMENT_ID
    assert context.value == "instrument-1"


@pytest.mark.parametrize("key", ["instrument_id", 1, None])
def test_context_rejects_untyped_keys(key: object) -> None:
    with pytest.raises(ValueError):
        WidgetContext(key, "instrument-1")  # type: ignore[arg-type]
