from __future__ import annotations

import json
from pathlib import Path

WEB = Path("apps/web")


def test_control_plane_web_has_approved_languages_with_same_keys() -> None:
    locales = ("en", "ru", "de", "fr", "es", "zh-CN", "hi")
    catalogs = {
        locale: json.loads(
            (WEB / "locales" / f"{locale}.json").read_text(
                encoding="utf-8"
            )
        )
        for locale in locales
    }
    english_keys = set(catalogs["en"])
    assert english_keys
    for locale, catalog in catalogs.items():
        assert set(catalog) == english_keys, locale
        assert all(
            isinstance(value, str) and value.strip()
            for value in catalog.values()
        )


def test_control_plane_ui_keeps_safety_surface_outside_workspace_grid(
) -> None:
    source = (WEB / "src" / "app.ts").read_text(encoding="utf-8")
    assert "renderSafety()" in source
    assert "${renderSafety()}" in source
    assert "workspace-grid" in source
    assert source.index("${renderSafety()}") < source.index(
        "${renderMainContent(workspace)}"
    )
    assert "layout_can_suppress_safety" not in source


def test_control_plane_ui_supports_customization_and_user_preferences(
) -> None:
    source = (WEB / "src" / "app.ts").read_text(encoding="utf-8")
    for token in (
        'data-action="add-widget"',
        'data-action="new-workspace"',
        'data-action="restore"',
        "dragstart",
        "drop",
        "nexus:locale:user-101",
        "nexus:theme:user-101",
    ):
        assert token in source


def test_control_plane_web_has_no_direct_database_or_execution_authority(
) -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (WEB / "src").glob("*.ts")
    ).lower()
    for forbidden in (
        "sqlalchemy",
        "select * from",
        "insert into",
        "venueadapter",
        "executioncoordinator",
        "submit_order(",
        "cancel_order(",
        "api_key",
        "api_secret",
    ):
        assert forbidden not in combined


def test_control_plane_css_has_responsive_breakpoints_and_themes() -> None:
    css = (WEB / "src" / "styles.css").read_text(encoding="utf-8")
    assert ':root[data-theme="light"]' in css
    assert "@media (max-width: 1100px)" in css
    assert "@media (max-width: 720px)" in css
    assert ".safety-strip" in css


def test_control_plane_frontend_targets_versioned_api_boundary() -> None:
    api = (WEB / "src" / "api.ts").read_text(encoding="utf-8")
    assert 'API_BASE = "/api/v2"' in api
    assert "ApiErrorEnvelope" in api
    assert "RealtimeEnvelope" in api
    assert "sqlalchemy" not in api.lower()
