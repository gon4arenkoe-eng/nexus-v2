export type Locale = "en" | "ru" | "de" | "fr" | "es" | "zh-CN" | "hi";
export type Theme = "dark" | "light";
export type SafetySeverity = "warning" | "critical";

export interface LanguageOption {
  code: Locale;
  label: string;
}

export interface SafetySignal {
  id: string;
  severity: SafetySeverity;
  titleKey: string;
  detailKey: string;
}

export interface WidgetInstance {
  id: string;
  key: string;
  titleKey: string;
  width: number;
  height: number;
  contextGroup: string | null;
  removable: boolean;
}

export interface UserWorkspace {
  id: string;
  name: string;
  widgets: WidgetInstance[];
}

export interface WorkspaceReadWidget {
  id: string;
  key: string;
  widgetVersion: number;
  column: number;
  row: number;
  width: number;
  height: number;
  contextGroup: string | null;
  settingsJson: string;
}

export interface WorkspaceReadProjection {
  id: string;
  name: string;
  locale: Locale;
  theme: Theme;
  activeLayoutVersion: number;
  widgets: WorkspaceReadWidget[];
}

export interface DashboardState {
  locale: Locale;
  theme: Theme;
  editing: boolean;
  activeWorkspaceId: string;
  activeSection: string;
  instrument: string;
  workspaces: UserWorkspace[];
  safetySignals: SafetySignal[];
}

export type TranslationCatalog = Record<string, string>;


export interface OperationalPosition {
  symbol: string;
  side: string;
  quantity: string;
  average_entry_price: string | null;
  status: string;
  venue_id: string;
  account_value: number;
}

export interface OperationalOrder {
  order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  requested_quantity: string;
  filled_quantity: string;
  average_fill_price: string | null;
  limit_price: string | null;
  status: string;
  venue_id: string;
  account_value: number;
  updated_at: string;
}

export interface OperationalFill {
  fill_id: string;
  order_id: string;
  symbol: string;
  side: string;
  quantity: string;
  price: string;
  fee: string;
  fee_currency: string | null;
  venue_id: string;
  account_value: number;
  executed_at: string;
}

export interface OperationalReconciliationDiscrepancy {
  discrepancy_id: string;
  kind: string;
  subject: string;
  symbol: string | null;
  local_value: string | null;
  venue_value: string | null;
  venue_id: string | null;
  observed_at: string;
}

export interface OperationalPortfolioSummary {
  observation_state: string;
  equity: string;
  daily_pnl: string;
  daily_pnl_ratio: string;
  drawdown_ratio: string;
  gross_exposure: string;
  net_exposure: string;
  margin_used: string;
  leverage: string;
  margin_utilization: string;
  observed_at: string;
}

export interface OperationalRiskSummary {
  observation_state: string;
  trading_state: string;
  headline_utilization: string;
  gross_exposure_utilization: string;
  net_exposure_utilization: string;
  leverage_utilization: string;
  margin_limit_utilization: string;
  daily_drawdown_utilization: string;
  rolling_drawdown_utilization: string;
  observed_at: string;
}

export interface OperationalPortfolioHistoryPoint {
  observed_at: string;
  equity: string;
}

export interface ControlPlaneOverview {
  workspace_id: string;
  user_id: number;
  positions: OperationalPosition[];
  orders: OperationalOrder[];
  fills: OperationalFill[];
  open_position_count: number;
  open_order_count: number;
  reconciliation_discrepancy_count: number | null;
  reconciliation_discrepancies: OperationalReconciliationDiscrepancy[];
  reconciliation_state: string;
  reconciliation_last_sync: string | null;
  portfolio_state: "UNAVAILABLE" | string;
  risk_state: "UNAVAILABLE" | string;
  portfolio: OperationalPortfolioSummary | null;
  risk: OperationalRiskSummary | null;
  portfolio_history: OperationalPortfolioHistoryPoint[];
}
