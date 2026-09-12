# NEXUS V2 Phase 11 — Control Plane / Workspace Composer Benchmark

## Decision

Phase 11 uses a NEXUS-owned typed workspace model and a dependency-light
TypeScript SPA. The browser is presentation-only. Canonical workspace ownership,
layout versioning, authorization, entitlement and persistence remain backend
responsibilities.

## References studied

### OpenBB Workspace

Reference: https://docs.openbb.co/workspace/analysts/widgets/overview

Useful pattern: widgets expose structured metadata/parameters and linked
parameters can synchronize multiple dashboard widgets. NEXUS adopts typed
WidgetDefinitions and ContextKey groups, but does not adopt OpenBB runtime code.

### TradingView multi-chart synchronization

Reference:
https://www.tradingview.com/support/solutions/43000629992-how-to-sync-the-charts-of-my-layout/

Useful pattern: selected chart groups can synchronize symbol/interval/context
without forcing every panel to share every setting. NEXUS adopts typed context
groups; context propagation is presentation/query scope only and has no trading
authority.

### Grafana dashboard JSON/grid model

Reference:
https://grafana.com/docs/grafana-cloud/learn-and-build/visualizations/dashboards/build-dashboards/view-dashboard-json-model/

Useful pattern: explicit grid coordinates and monotonically versioned dashboard
state. NEXUS adopts deterministic grid placement and immutable layout versions,
with tenant/user ownership and recovery semantics.

## NEXUS-specific additions

NEXUS intentionally goes beyond generic dashboard products in safety behavior:

- mandatory safety state is rendered outside the customizable workspace canvas;
- active reconciliation/risk/execution/venue safety state cannot be hidden by a
  user layout;
- widget discovery may be entitlement-aware, but backend permission remains
  authoritative;
- workspace context propagation cannot submit/cancel orders or mutate trading
  state;
- layouts/templates/realtime scope are tenant/user isolated;
- frontend code has no direct database dependency;
- locale/theme are presentation preferences and do not alter canonical backend
  identifiers.

## Approved locale foundation

- English (`en`)
- Russian (`ru`)
- German (`de`)
- French (`fr`)
- Spanish (`es`)
- Simplified Chinese (`zh-CN`)
- Hindi (`hi`)

English is the fallback catalog. All locale files carry the same translation-key
set. Canonical API/domain enum values are not localized.

## Frontend technology decision

For the Phase 11 foundation NEXUS uses native TypeScript ES modules + DOM/CSS
Grid rather than introducing React/Vite dependencies immediately. This keeps the
supply chain small while preserving strict frontend typing and responsive UI.
The choice does not prevent a later renderer/framework migration because the
canonical workspace contracts live outside the frontend.

## Production authority

Unchanged:

- AI promotion: SHADOW-ONLY
- AI direct exchange access: BLOCKED
- Restricted Live: DISABLED
- Full Live: DISABLED
