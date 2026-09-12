export const API_BASE = "/api/v2";
async function parseJson(response) {
    if (!response.ok) {
        const error = (await response.json());
        throw new Error(`${error.code}: ${error.message}`);
    }
    return (await response.json());
}
export class ControlPlaneApi {
    async listWorkspaces() {
        return parseJson(await fetch(`${API_BASE}/control-plane/workspaces`, {
            credentials: "same-origin",
        }));
    }
    async updatePreferences(value) {
        await parseJson(await fetch(`${API_BASE}/control-plane/preferences`, {
            method: "PUT",
            credentials: "same-origin",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(value),
        }));
    }
}
