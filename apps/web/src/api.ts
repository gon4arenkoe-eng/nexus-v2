import type { Locale, Theme, UserWorkspace } from "./contracts.js";

export const API_BASE = "/api/v2" as const;

export interface ApiErrorEnvelope {
  code: string;
  message: string;
  correlationId: string;
}

export interface RealtimeEnvelope<T> {
  workspaceId: string;
  userId: number;
  channel: string;
  sequence: number;
  schemaVersion: number;
  payload: T;
}

export interface PresentationPreferenceUpdate {
  locale: Locale;
  theme: Theme;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = (await response.json()) as ApiErrorEnvelope;
    throw new Error(`${error.code}: ${error.message}`);
  }
  return (await response.json()) as T;
}

export class ControlPlaneApi {
  async listWorkspaces(): Promise<UserWorkspace[]> {
    return parseJson<UserWorkspace[]>(
      await fetch(`${API_BASE}/control-plane/workspaces`, {
        credentials: "same-origin",
      }),
    );
  }

  async updatePreferences(
    value: PresentationPreferenceUpdate,
  ): Promise<void> {
    await parseJson<unknown>(
      await fetch(`${API_BASE}/control-plane/preferences`, {
        method: "PUT",
        credentials: "same-origin",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(value),
      }),
    );
  }
}
