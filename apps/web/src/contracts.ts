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
