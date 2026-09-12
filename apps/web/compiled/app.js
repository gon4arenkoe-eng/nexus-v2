import { loadCatalog, translate } from "./i18n.js";
const navItems = [
    "overview", "portfolio", "positions", "orders", "strategies",
    "strategyVersions", "risk", "reconciliation", "exchanges",
    "intelligence", "news", "aiea", "experiments", "candidates",
    "backtests", "modelHealth", "executionQuality", "history",
    "audit", "notifications", "settings", "admin",
];
const languages = [
    { code: "en", label: "English" },
    { code: "ru", label: "Русский" },
    { code: "de", label: "Deutsch" },
    { code: "fr", label: "Français" },
    { code: "es", label: "Español" },
    { code: "zh-CN", label: "中文（简体）" },
    { code: "hi", label: "हिन्दी" },
];
const widgetLibrary = [
    { id: "nav", key: "portfolio.nav", titleKey: "widget.nav", width: 6, height: 2, contextGroup: null, removable: true },
    { id: "pnl", key: "portfolio.pnl", titleKey: "widget.pnl", width: 6, height: 2, contextGroup: null, removable: true },
    { id: "risk", key: "risk.utilization", titleKey: "widget.risk", width: 6, height: 2, contextGroup: null, removable: true },
    { id: "system", key: "system.health", titleKey: "widget.system", width: 6, height: 2, contextGroup: null, removable: true },
    { id: "market", key: "market.context", titleKey: "widget.market", width: 14, height: 6, contextGroup: "market-a", removable: true },
    { id: "positions", key: "portfolio.positions", titleKey: "widget.positions", width: 10, height: 6, contextGroup: "market-a", removable: true },
    { id: "strategies", key: "strategy.status", titleKey: "widget.strategies", width: 8, height: 5, contextGroup: null, removable: true },
    { id: "intelligence", key: "intelligence.context", titleKey: "widget.intelligence", width: 8, height: 5, contextGroup: "market-a", removable: true },
    { id: "events", key: "audit.events", titleKey: "widget.events", width: 8, height: 5, contextGroup: null, removable: true },
    { id: "grid", key: "grid.desk", titleKey: "widget.grid", width: 12, height: 6, contextGroup: "market-a", removable: true },
    { id: "aiea", key: "aiea.research", titleKey: "widget.aiea", width: 12, height: 6, contextGroup: "market-a", removable: true },
];
function cloneWidget(key, suffix) {
    const source = widgetLibrary.find((item) => item.key === key);
    if (!source)
        throw new Error(`Unknown widget ${key}`);
    return { ...source, id: `${source.id}-${suffix}` };
}
const templates = {
    command: [
        ...widgetLibrary.slice(0, 9).map((item, index) => ({ ...item, id: `${item.id}-${index}` })),
    ],
    grid: [cloneWidget("grid.desk", "1"), cloneWidget("portfolio.positions", "1"), cloneWidget("risk.utilization", "1"), cloneWidget("audit.events", "1")],
    research: [cloneWidget("aiea.research", "1"), cloneWidget("intelligence.context", "1"), cloneWidget("market.context", "1"), cloneWidget("audit.events", "1")],
    blank: [],
};
const savedLocale = localStorage.getItem("nexus:locale:user-101");
const savedTheme = localStorage.getItem("nexus:theme:user-101");
const state = {
    locale: savedLocale && languages.some((item) => item.code === savedLocale) ? savedLocale : "en",
    theme: savedTheme === "light" ? "light" : "dark",
    editing: false,
    activeWorkspaceId: "command-center",
    activeSection: "overview",
    instrument: "BTC-PERP",
    workspaces: [
        { id: "command-center", name: "Command Center", widgets: templates.command?.map((item) => ({ ...item })) ?? [] },
        { id: "grid-desk", name: "Grid Desk", widgets: templates.grid?.map((item) => ({ ...item })) ?? [] },
    ],
    safetySignals: [
        { id: "recon", severity: "warning", titleKey: "safety.reconciliation", detailKey: "safety.reconciliation.detail" },
    ],
};
let catalog = {};
let draggedWidgetId = null;
function currentWorkspace() {
    const workspace = state.workspaces.find((item) => item.id === state.activeWorkspaceId);
    if (!workspace)
        throw new Error("Active workspace missing");
    return workspace;
}
function t(key) {
    return translate(catalog, key);
}
function widgetMetric(key) {
    const values = {
        "portfolio.nav": "$1,284,450",
        "portfolio.pnl": "+$18,245",
        "risk.utilization": "48%",
        "system.health": "7 / 8",
    };
    return values[key] ?? "";
}
function widgetBody(widget) {
    if (widget.key === "market.context") {
        return `<div class="chart"><span class="chart-line"></span><div class="chart-caption">${state.instrument} · 65,840.50 · +1.24%</div></div>`;
    }
    if (widget.key === "portfolio.positions") {
        return `<div class="table"><div><b>${state.instrument}</b><span>+2.84%</span></div><div><b>ETH-PERP</b><span>-0.42%</span></div><div><b>SOL-PERP</b><span>+1.67%</span></div></div>`;
    }
    if (widget.key === "strategy.status") {
        return `<div class="table"><div><b>Trend BTC</b><span class="ok">ACTIVE</span></div><div><b>Grid BTC</b><span class="ok">ACTIVE</span></div><div><b>MR ETH</b><span>SHADOW</span></div></div>`;
    }
    if (widget.key === "intelligence.context") {
        return `<div class="intel"><p>${t("intel.regime")}: <b>TRENDING</b></p><p>${t("intel.volatility")}: MEDIUM</p><p>${t("intel.eventRisk")}: LOW</p></div>`;
    }
    if (widget.key === "audit.events") {
        return `<div class="events"><p>22:21 · Order filled · BTC-PERP</p><p>22:18 · Risk check passed</p><p>22:15 · Market context CURRENT</p></div>`;
    }
    if (widget.key === "grid.desk") {
        return `<div class="grid-visual"><div>Range 63,500 — 68,200</div><div>Inventory 0.42 BTC</div><div>Reserved $28,400</div><div>Cycle PnL +$412</div></div>`;
    }
    if (widget.key === "aiea.research") {
        return `<div class="aiea-flow"><span>Hypothesis</span><span>Candidate</span><span>OOS</span><span>Shadow</span></div>`;
    }
    const metric = widgetMetric(widget.key);
    return `<div class="metric">${metric}</div><div class="muted">${t(`${widget.titleKey}.detail`)}</div>`;
}
function renderSafety() {
    if (state.safetySignals.length === 0)
        return "";
    return `<section class="safety-strip" aria-live="assertive">
    <strong>⚠ ${t(state.safetySignals[0]?.titleKey ?? "safety.reconciliation")}</strong>
    <span>${t(state.safetySignals[0]?.detailKey ?? "safety.reconciliation.detail")}</span>
    <button data-action="safety-evidence">${t("action.viewEvidence")}</button>
  </section>`;
}
function renderWidget(widget) {
    const edit = state.editing ? `<div class="widget-edit">
      <button data-action="shrink" data-widget="${widget.id}" aria-label="shrink">−</button>
      <button data-action="grow" data-widget="${widget.id}" aria-label="grow">＋</button>
      ${widget.removable ? `<button data-action="remove" data-widget="${widget.id}" aria-label="remove">×</button>` : ""}
    </div>` : "";
    return `<article class="widget" draggable="${state.editing}" data-widget-id="${widget.id}" style="grid-column: span ${widget.width}; min-height:${widget.height * 36}px">
    <header><span>${t(widget.titleKey)}</span><span class="status-dot">● CURRENT</span>${edit}</header>
    ${widgetBody(widget)}
  </article>`;
}
function renderSectionSurface(section) {
    const surfaces = {
        portfolio: `<div class="surface-grid"><section><h2>${t("nav.portfolio")}</h2><div class="metric">$1,284,450</div><p class="muted">Gross 48% · Net 22% · DD 2.8%</p></section><section><h2>Allocation</h2><div class="bar"><i style="width:42%"></i></div><p>BTC 42% · ETH 31% · SOL 12%</p></section></div>`,
        positions: `<div class="surface-card"><h2>${t("nav.positions")}</h2><div class="table"><div><b>BTC-PERP</b><span>0.42 · +$4,240</span></div><div><b>ETH-PERP</b><span>-1.80 · -$320</span></div><div><b>SOL-PERP</b><span>420 · +$910</span></div></div></div>`,
        orders: `<div class="surface-card"><h2>${t("nav.orders")}</h2><div class="table"><div><b>BTC-PERP BUY</b><span>FILLED</span></div><div><b>ETH-PERP SELL</b><span>OPEN</span></div><div><b>SOL-PERP BUY</b><span>CANCELLED</span></div></div></div>`,
        strategies: `<div class="surface-card"><h2>${t("nav.strategies")}</h2><div class="table"><div><b>Trend BTC</b><span class="ok">ACTIVE</span></div><div><b>Grid BTC</b><span class="ok">ACTIVE</span></div><div><b>MR ETH</b><span>SHADOW</span></div></div></div>`,
        strategyVersions: `<div class="surface-card"><h2>${t("nav.strategyVersions")}</h2><p>trend-btc v12 · champion</p><p>trend-btc v13 · challenger / shadow</p></div>`,
        risk: `<div class="surface-grid"><section><h2>${t("nav.risk")}</h2><div class="metric">48%</div><p>Portfolio risk utilization</p></section><section><h2>Limits</h2><p>Gross exposure 48 / 75%</p><p>Drawdown 2.8 / 8%</p><p>Correlation cluster 61 / 80%</p></section></div>`,
        reconciliation: `<div class="surface-card incident"><h2>${t("nav.reconciliation")}</h2><p><b>BTC-PERP POSITION_QUANTITY_DRIFT</b></p><p>Local 0.42 BTC · Venue 0.37 BTC</p><button>${t("action.viewEvidence")}</button></div>`,
        exchanges: `<div class="surface-card"><h2>${t("nav.exchanges")}</h2><div class="table"><div><b>Binance / Primary</b><span class="ok">CURRENT</span></div><div><b>Bybit / Research</b><span>DISABLED</span></div></div></div>`,
        intelligence: `<div class="surface-grid"><section><h2>${t("nav.intelligence")}</h2><p>Regime <b>TRENDING</b></p><p>Volatility MEDIUM</p><p>Liquidity HIGH</p></section><section><h2>Funding / OI</h2><p>Funding +0.010%</p><p>OI +4.2%</p></section></div>`,
        news: `<div class="surface-card"><h2>${t("nav.news")}</h2><p>22:10 · Macro event risk LOW</p><p>21:42 · BTC liquidity improved</p></div>`,
        aiea: `<div class="surface-card"><h2>${t("nav.aiea")}</h2><div class="aiea-flow"><span>Evidence</span><span>Hypothesis</span><span>Candidate</span><span>Falsification</span><span>OOS</span><span>Shadow</span></div></div>`,
        experiments: `<div class="surface-card"><h2>${t("nav.experiments")}</h2><p>EXP-2048 · WALK_FORWARD · PASS</p><p>EXP-2049 · FALSIFICATION · RUNNING</p></div>`,
        candidates: `<div class="surface-card"><h2>${t("nav.candidates")}</h2><p>trend-btc-v13 · SHADOW READY</p><p>Promotion authority: SHADOW-ONLY</p></div>`,
        backtests: `<div class="surface-card"><h2>${t("nav.backtests")}</h2><p>OOS Sharpe 1.42 · WF stability 0.81 · Costs INCLUDED</p></div>`,
        modelHealth: `<div class="surface-card"><h2>${t("nav.modelHealth")}</h2><p>Data freshness CURRENT</p><p>Drift NORMAL</p><p>Champion/challenger delta +3.8%</p></div>`,
        executionQuality: `<div class="surface-card"><h2>${t("nav.executionQuality")}</h2><p>Median slippage 1.8 bps</p><p>Reject rate 0.2%</p><p>Unknown outcomes 0</p></div>`,
        history: `<div class="surface-card"><h2>${t("nav.history")}</h2><p>Realized PnL +$18,245 · Strategy attribution available</p></div>`,
        audit: `<div class="surface-card"><h2>${t("nav.audit")}</h2><p>22:28 settings.change · user 101</p><p>22:21 execution.fill · BTC-PERP</p></div>`,
        notifications: `<div class="surface-card"><h2>${t("nav.notifications")}</h2><p>Risk warnings ON</p><p>Reconciliation alerts ON</p><p>AIEA shadow alerts ON</p></div>`,
        settings: `<div class="surface-grid"><section><h2>${t("nav.settings")}</h2><p>Language: ${languages.find((item) => item.code === state.locale)?.label ?? state.locale}</p><p>Theme: ${state.theme}</p></section><section><h2>Safety settings</h2><p>Safety-critical changes require audit evidence.</p></section></div>`,
        admin: `<div class="surface-card"><h2>${t("nav.admin")}</h2><div class="table"><div><b>Owner</b><span>OWNER</span></div><div><b>Trader 2</b><span>TRADER</span></div><div><b>Observer</b><span>VIEWER</span></div></div></div>`,
    };
    return surfaces[section] ?? `<div class="surface-card"><h2>${t(`nav.${section}`)}</h2><p>${t("surface.ready")}</p></div>`;
}
function renderMainContent(workspace) {
    if (state.activeSection !== "overview") {
        return `<section class="page-head"><div><h1>${t(`nav.${state.activeSection}`)}</h1><p>${t("surface.subtitle")}</p></div><div class="summary">${t("label.updated")}: 22:37:14</div></section><section class="surface-wrap">${renderSectionSurface(state.activeSection)}</section>`;
    }
    return `<section class="page-head"><div><h1>${workspace.name}</h1><p>${t("subtitle.command")}</p></div><div class="summary">${t("label.updated")}: 22:37:14</div></section>
        ${state.editing ? `<section class="composer-bar"><button data-action="new-workspace">＋ ${t("action.newWorkspace")}</button><button data-action="add-widget">＋ ${t("action.addWidget")}</button><button data-action="restore">↶ ${t("action.restore")}</button><span>${t("composer.hint")}</span></section>` : ""}
        <section class="workspace-grid">${workspace.widgets.map(renderWidget).join("")}</section>`;
}
function render() {
    document.documentElement.dataset.theme = state.theme;
    const app = document.querySelector("#app");
    if (!app)
        throw new Error("#app missing");
    const workspace = currentWorkspace();
    app.innerHTML = `
    <div class="shell">
      <aside class="rail">
        <div class="brand">N</div>
        ${navItems.map((key) => `<button data-section="${key}" class="${state.activeSection === key ? "active" : ""}" title="${t(`nav.${key}`)}">${t(`nav.${key}`).slice(0, 2)}</button>`).join("")}
      </aside>
      <main class="main">
        <header class="topbar">
          <div><b>NEXUS V2</b><span class="badge">Control Plane</span></div>
          <div class="context-controls">
            <select id="workspace-select">${state.workspaces.map((item) => `<option value="${item.id}" ${item.id === workspace.id ? "selected" : ""}>${item.name}</option>`).join("")}</select>
            <select id="instrument-select"><option>BTC-PERP</option><option>ETH-PERP</option><option>SOL-PERP</option></select>
            <span class="current">● CURRENT</span>
            <button id="edit-toggle">${state.editing ? t("action.done") : t("action.customize")}</button>
            <button id="theme-toggle">${state.theme === "dark" ? "☀" : "◐"}</button>
            <select id="locale-select">${languages.map((item) => `<option value="${item.code}" ${item.code === state.locale ? "selected" : ""}>${item.label}</option>`).join("")}</select>
          </div>
        </header>
        ${renderSafety()}
        ${renderMainContent(workspace)}
      </main>
    </div>`;
    bindEvents();
}
function moveWidget(sourceId, targetId) {
    const widgets = currentWorkspace().widgets;
    const sourceIndex = widgets.findIndex((item) => item.id === sourceId);
    const targetIndex = widgets.findIndex((item) => item.id === targetId);
    if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex)
        return;
    const [moved] = widgets.splice(sourceIndex, 1);
    if (!moved)
        return;
    widgets.splice(targetIndex, 0, moved);
}
function bindEvents() {
    document.querySelectorAll("[data-section]").forEach((element) => {
        element.addEventListener("click", () => {
            state.activeSection = element.dataset.section ?? "overview";
            state.editing = false;
            render();
        });
    });
    document.querySelector("#locale-select")?.addEventListener("change", async (event) => {
        state.locale = event.target.value;
        localStorage.setItem("nexus:locale:user-101", state.locale);
        catalog = await loadCatalog(state.locale);
        render();
    });
    document.querySelector("#theme-toggle")?.addEventListener("click", () => {
        state.theme = state.theme === "dark" ? "light" : "dark";
        localStorage.setItem("nexus:theme:user-101", state.theme);
        render();
    });
    document.querySelector("#edit-toggle")?.addEventListener("click", () => {
        state.editing = !state.editing;
        render();
    });
    document.querySelector("#workspace-select")?.addEventListener("change", (event) => {
        state.activeWorkspaceId = event.target.value;
        render();
    });
    document.querySelector("#instrument-select")?.addEventListener("change", (event) => {
        state.instrument = event.target.value;
        render();
    });
    document.querySelectorAll("[data-action]").forEach((element) => {
        element.addEventListener("click", () => {
            const action = element.dataset.action;
            const widgetId = element.dataset.widget;
            const widgets = currentWorkspace().widgets;
            const widget = widgets.find((item) => item.id === widgetId);
            if (action === "remove" && widgetId)
                currentWorkspace().widgets = widgets.filter((item) => item.id !== widgetId);
            if (action === "grow" && widget)
                widget.width = Math.min(24, widget.width + 2);
            if (action === "shrink" && widget)
                widget.width = Math.max(4, widget.width - 2);
            if (action === "add-widget") {
                const available = widgetLibrary.find((candidate) => !widgets.some((item) => item.key === candidate.key));
                if (available)
                    widgets.push({ ...available, id: `${available.id}-${Date.now()}` });
            }
            if (action === "new-workspace") {
                const id = `workspace-${Date.now()}`;
                state.workspaces.push({ id, name: `${t("workspace.new")} ${state.workspaces.length + 1}`, widgets: [] });
                state.activeWorkspaceId = id;
            }
            if (action === "restore")
                currentWorkspace().widgets = templates.command?.map((item) => ({ ...item })) ?? [];
            render();
        });
    });
    document.querySelectorAll(".widget").forEach((element) => {
        element.addEventListener("dragstart", () => { draggedWidgetId = element.dataset.widgetId ?? null; });
        element.addEventListener("dragover", (event) => event.preventDefault());
        element.addEventListener("drop", (event) => {
            event.preventDefault();
            const target = element.dataset.widgetId;
            if (draggedWidgetId && target)
                moveWidget(draggedWidgetId, target);
            draggedWidgetId = null;
            render();
        });
    });
}
async function start() {
    catalog = await loadCatalog(state.locale);
    render();
}
void start();
