const API_BASE =
  process.env.API_BASE_URL ??
  (process.env.API_BASE_HOSTPORT ? `http://${process.env.API_BASE_HOSTPORT}/api/v1` : "http://127.0.0.1:8000/api/v1");

function authHeaders(): Record<string, string> {
  const role = process.env.API_AUTH_ROLE ?? "admin";
  const token =
    process.env.API_AUTH_TOKEN ??
    (role === "editor"
      ? process.env.API_AUTH_EDITOR_TOKEN ?? "dev-editor-token"
      : role === "operator"
        ? process.env.API_AUTH_OPERATOR_TOKEN ?? "dev-operator-token"
        : process.env.API_AUTH_ADMIN_TOKEN ?? "dev-admin-token");

  return {
    "x-auth-role": role,
    "x-auth-token": token,
  };
}

export async function fetchApiJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      headers: authHeaders(),
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function postApiJson<T>(path: string, payload?: unknown): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: payload === undefined ? undefined : JSON.stringify(payload),
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
