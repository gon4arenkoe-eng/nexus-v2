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



def test_active_control_plane_reads_workspace_projection() -> None:
    source = Path("apps/web/index.html").read_text(
        encoding="utf-8"
    )

    assert "/api/v2/control-plane/workspaces" in source
    assert "workspaceProjectionToLayout" in source
    assert "loadWorkspaceState" in source
    assert "settingsJson" in source

    assert "item.column" in source
    assert "item.row" in source
    assert "item.width" in source
    assert "item.height" in source

    assert "let activeServerWorkspaceId=null;" in source
    assert "canonicalWorkspaceSelectorMarkup" in source
    assert "data-canonical-workspace" in source
    assert "applyServerWorkspace(" in source
    assert "applyServerWorkspaceById" in source

    # A single canonical workspace remains unambiguous.
    assert "serverWorkspaces.length===1" in source

    # Multiple workspaces must never fall back to the old
    # arbitrary/non-selectable single-workspace guard.
    assert "serverWorkspaces.length!==1" not in source

    # Multi-workspace switching resolves an explicit canonical id
    # from the already tenant/user-scoped read response.
    assert "serverWorkspaces.find(" in source
    assert "activeServerWorkspaceId===id" in source

    assert (
        "Promise.allSettled(["
        in source
    )

    # Existing local preview save remains local-only.
    assert "nexus:v7:workspace" in source

    # This active browser path must not gain HTTP mutation.
    assert "method:'PUT'" not in source
    assert 'method:"PUT"' not in source


def test_control_plane_frontend_targets_versioned_api_boundary() -> None:
    api = (WEB / "src" / "api.ts").read_text(encoding="utf-8")
    assert 'API_BASE = "/api/v2"' in api
    assert "ApiErrorEnvelope" in api
    assert "RealtimeEnvelope" in api
    assert "sqlalchemy" not in api.lower()

def test_canonical_widget_namespace_adapter_preserves_identity() -> None:
    import re
    from pathlib import Path

    from apps.core.application.control_plane_catalog import (
        INITIAL_WIDGET_DEFINITIONS,
    )

    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    start = source.index(
        "const CANONICAL_WIDGET_PRESENTATION=Object.freeze({"
    )
    end = source.index(
        "\n});\n\nfunction workspaceProjectionToLayout",
        start,
    )
    mapping_source = source[start:end]

    mapped_keys = set(
        re.findall(
            r"^\s*'([^']+)':Object\.freeze\(\{",
            mapping_source,
            re.MULTILINE,
        )
    )
    registry_keys = {
        item.manifest.widget_key
        for item in INITIAL_WIDGET_DEFINITIONS
    }

    # The browser adapter must cover the current canonical Registry
    # exactly. New registry values therefore fail this test until an
    # explicit presentation decision is made.
    assert mapped_keys == registry_keys

    assert "CANONICAL_WIDGET_PRESENTATION[item.key]" in source
    assert "if(!presentation)return null;" in source
    assert "entry=>entry.key===presentation.key" in source

    # Presentation identity must never replace canonical identity.
    assert "key:presentation.key" in source
    assert "projectedItem.canonicalKey=item.key;" in source
    assert "projectedItem.canonicalVersion=" in source
    assert "item.widgetVersion" in source

    # The old incompatible canonical==presentation assumption is gone.
    assert "entry=>entry.key===item.key" not in source

    # This compatibility slice is still workspace-read-only.
    assert "method:'PUT'" not in source
    assert "method:'DELETE'" not in source

def test_canonical_workspace_projection_preserves_context_group() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    assert "item.contextGroup!==null" in source
    assert "item.contextGroup!==undefined" in source
    assert "typeof item.contextGroup!=='string'" in source
    assert (
        "projectedItem.contextGroup=item.contextGroup??null;"
        in source
    )

    # Existing editor state transformations preserve arbitrary
    # canonical metadata once it is projected into each widget.
    assert (
        "function cloneLayout(v){return JSON.parse(JSON.stringify(v))}"
        in source
    )
    assert (
        "const w={...src,cfg:{...src.cfg}"
        in source
    )

    # Canonical widget identity remains independent from presentation.
    assert "projectedItem.canonicalKey=item.key;" in source
    assert "projectedItem.canonicalVersion=" in source

    # This prerequisite does not introduce workspace mutation authority.

def test_canonical_workspace_retains_active_layout_as_base_version() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    assert "let activeServerWorkspaceBaseVersion=null;" in source
    assert "const baseVersion=workspace?.activeLayoutVersion;" in source
    assert (
        "if(!Number.isInteger(baseVersion) || baseVersion<1)return false;"
        in source
    )
    assert "activeServerWorkspaceBaseVersion=baseVersion;" in source

    # Fresh server reads and read failures must invalidate stale
    # optimistic-concurrency state before any future save exists.
    assert source.count("activeServerWorkspaceBaseVersion=null;") >= 3

    # This slice is metadata retention only.
    assert "method:'PUT'" not in source
    assert 'method:"PUT"' not in source
    assert "method:'DELETE'" not in source
    assert 'method:"DELETE"' not in source

def test_canonical_workspace_save_payload_is_lossless_and_fail_closed() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    assert "function canonicalWorkspaceSavePayload()" in source

    assert "workspaceId:activeServerWorkspaceId" in source
    assert "baseVersion:activeServerWorkspaceBaseVersion" in source

    assert "key:item.canonicalKey" in source
    assert "widgetVersion:item.canonicalVersion" in source
    assert "column:item.x" in source
    assert "row:item.y" in source
    assert "width:item.w" in source
    assert "height:item.h" in source
    assert "contextGroup:item.contextGroup??null" in source
    assert "settingsJson=JSON.stringify(cfg);" in source

    # Canonical identity may never be reconstructed from presentation key.
    assert "typeof item.canonicalKey!=='string'" in source
    assert "!Number.isInteger(item.canonicalVersion)" in source

    # Server widget version may no longer silently fall back to 1.
    assert "projectedItem.canonicalVersion=item.widgetVersion;" in source
    assert (
        "Number.isInteger(item.widgetVersion)\n"
        "        ?item.widgetVersion\n"
        "        :1;"
    ) not in source

    # Serializer foundation only: no server mutation in this slice.
    assert "method:'PUT'" not in source
    assert 'method:"PUT"' not in source
    assert "method:'DELETE'" not in source
    assert 'method:"DELETE"' not in source

def test_browser_created_widgets_use_canonical_registry_identity() -> None:
    from apps.core.application.control_plane_catalog import (
        INITIAL_WIDGET_DEFINITIONS,
    )

    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    registry_versions = {
        definition.manifest.widget_key: definition.manifest.version
        for definition in INITIAL_WIDGET_DEFINITIONS
    }

    expected = {
        "nav": "portfolio.nav",
        "pnl": "portfolio.pnl",
        "risk": "risk.portfolio",
        "positions": "portfolio.positions",
        "strategies": "strategy.status",
        "intelligence": "intelligence.market_context",
        "grid": "grid.desk",
        "aiea": "aiea.research",
        "reconciliation": "reconciliation.health",
        "orders": "execution.orders_fills",
        "exchanges": "venue.account_health",
        "alerts": "intelligence.news_events",
    }

    for browser_key, canonical_key in expected.items():
        assert canonical_key in registry_versions
        version = registry_versions[canonical_key]

        marker = (
            f"key:'{browser_key}'"
            if browser_key != "positions"
            else "key:'positions'"
        )

        assert marker in source
        assert f"canonicalKey:'{canonical_key}'" in source
        assert f"canonicalVersion:{version}" in source

    assert "canonicalKey:c.canonicalKey" in source
    assert "canonicalVersion:c.canonicalVersion" in source
    assert "contextGroup:null" in source

    assert "typeof c.canonicalKey!=='string'" in source
    assert "!Number.isInteger(c.canonicalVersion)" in source

    # Duplicate keeps the canonical identity by object spread.
    assert "const w={...src,cfg:{...src.cfg}" in source

    # This step still introduces no server-side workspace write.
    assert "method:'PUT'" not in source
    assert 'method:"PUT"' not in source
    assert "method:'DELETE'" not in source
    assert 'method:"DELETE"' not in source

def test_canonical_workspace_save_uses_versioned_presentation_write_boundary() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(encoding="utf-8")

    assert (
        "async function saveCanonicalWorkspace()"
        in source
    )

    assert (
        "async function saveCurrentWorkspace()"
        in source
    )

    assert (
        "'/api/v2/control-plane/workspaces/save'"
        in source
    )

    assert "method:'POST'" in source
    assert "body:JSON.stringify(payload)" in source

    assert "response.status===409" in source
    assert "await loadWorkspaceState();" in source

    assert (
        "applyServerWorkspace(workspace)"
        in source
    )

    assert (
        "if(!projected)return false;"
        in source
    )

    assert (
        "return saveCanonicalWorkspace();"
        in source
    )

    for forbidden in (
        "submit_order(",
        "cancel_order(",
        "VenueAdapter",
        "ExecutionCoordinator",
    ):
        assert forbidden not in source
def test_blank_workspace_create_uses_canonical_presentation_boundary() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    start = source.index(
        "async function createBlankWorkspace()"
    )

    end = source.index(
        "async function saveCanonicalWorkspace()"
    )

    create_source = source[start:end]

    assert (
        "'/api/v2/control-plane/workspaces'"
        in create_source
    )

    assert "method:'POST'" in create_source

    assert (
        "data-create-blank-workspace"
        in source
    )

    assert (
        "bindBeforeBlankWorkspaceCreate"
        in source
    )

    assert (
        "serverWorkspaces.push(workspace)"
        in create_source
    )

    assert (
        "applyServerWorkspace(workspace)"
        in create_source
    )

    for forbidden in (
        "workspaceId",
        "tenant_workspace_id",
        "user_id",
        "submit_order(",
        "cancel_order(",
        "VenueAdapter",
        "ExecutionCoordinator",
    ):
        assert forbidden not in create_source
def test_canonical_workspace_restore_creates_new_version() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    start = source.index(
        "async function "
        "restoreCanonicalWorkspaceVersion()"
    )

    end = source.index(
        "async function saveCurrentWorkspace()",
        start,
    )

    restore_source = source[start:end]

    assert (
        "'/api/v2/control-plane/workspaces/restore'"
        in restore_source
    )

    assert "method:'POST'" in restore_source

    assert (
        "workspaceId:activeServerWorkspaceId"
        in restore_source
    )

    assert (
        "baseVersion,"
        in restore_source
    )

    assert (
        "targetVersion"
        in restore_source
    )

    assert (
        "response.status===409"
        in restore_source
    )

    assert (
        "await loadWorkspaceState();"
        in restore_source
    )

    assert (
        "applyServerWorkspace(workspace)"
        in restore_source
    )

    assert (
        "data-restore-canonical-workspace"
        in source
    )

    for forbidden in (
        "tenant_workspace_id",
        "user_id",
        "submit_order(",
        "cancel_order(",
        "VenueAdapter",
        "ExecutionCoordinator",
    ):
        assert forbidden not in restore_source
def test_curated_template_workspace_creation_uses_canonical_boundary() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "web"
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "async function loadWorkspaceTemplates()"
        in source
    )

    assert (
        "'/api/v2/control-plane/workspace-templates'"
        in source
    )

    start = source.index(
        "async function "
        "createWorkspaceFromTemplate()"
    )

    end = source.index(
        "async function createBlankWorkspace()",
        start,
    )

    create_source = source[start:end]

    assert (
        "'/api/v2/control-plane/"
        "workspaces/from-template'"
        in create_source
    )

    assert "method:'POST'" in create_source

    assert (
        "templateKey:template.key"
        in create_source
    )

    assert (
        "templateVersion:template.version"
        in create_source
    )

    assert (
        "serverWorkspaces.push(workspace)"
        in create_source
    )

    assert (
        "applyServerWorkspace(workspace)"
        in create_source
    )

    assert (
        "data-workspace-template"
        in source
    )

    assert (
        "data-create-template-workspace"
        in source
    )

    for forbidden in (
        "tenant_workspace_id",
        "user_id",
        "submit_order(",
        "cancel_order(",
        "VenueAdapter",
        "ExecutionCoordinator",
    ):
        assert forbidden not in create_source
