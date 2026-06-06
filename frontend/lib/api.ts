import { useAuthStore } from "./store";
import type { AuthResult } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface FetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Skip attaching the bearer token (e.g. for login). */
  auth?: boolean;
}

/**
 * Thin typed fetch wrapper. Attaches the bearer token and the active
 * organization header, and normalizes errors into ApiError.
 */
export async function apiFetch<T>(
  path: string,
  { body, auth = true, headers, ...init }: FetchOptions = {},
): Promise<T> {
  const { accessToken, organization } = useAuthStore.getState();

  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  };
  if (auth && accessToken) {
    finalHeaders["Authorization"] = `Bearer ${accessToken}`;
  }
  if (auth && organization) {
    finalHeaders["X-Organization-Id"] = organization.id;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: finalHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (res.status === 401) {
    // Session expired or invalid — drop it so the guard redirects to login.
    useAuthStore.getState().clear();
    throw new ApiError(401, "Session expired. Please sign in again.");
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) {
        detail =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// --- Auth actions ------------------------------------------------------------

export async function login(email: string, password: string): Promise<AuthResult> {
  const result = await apiFetch<AuthResult>("/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
  useAuthStore.getState().setSession({
    user: result.user,
    organization: result.organization,
    accessToken: result.tokens.access_token,
    refreshToken: result.tokens.refresh_token,
  });
  return result;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } catch {
    /* best-effort; clear locally regardless */
  }
  useAuthStore.getState().clear();
}
