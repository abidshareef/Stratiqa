import { useAuthStore } from "./store";
import type {
  AgentAskResponse,
  AgentDetail,
  AgentRoster,
  AuthResult,
  BusinessBlueprintOut,
  CommitMapping,
  CommitResult,
  CustomerOverview,
  DiscoveryResult,
  FounderInterview,
  GovernanceOverview,
  GraphOut,
  MonitoringOverview,
  ProductOverview,
  UploadDetail,
  UploadOut,
} from "./types";

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

export async function register(input: {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}): Promise<AuthResult> {
  const result = await apiFetch<AuthResult>("/auth/register", {
    method: "POST",
    auth: false,
    body: input,
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

// --- Business Discovery ------------------------------------------------------

export async function runDiscovery(
  input: FounderInterview,
): Promise<DiscoveryResult> {
  return apiFetch<DiscoveryResult>("/discovery/run", {
    method: "POST",
    body: input,
  });
}

/** Returns the org's latest blueprint, or null if discovery hasn't run yet. */
export async function getBlueprint(): Promise<BusinessBlueprintOut | null> {
  try {
    return await apiFetch<BusinessBlueprintOut>("/discovery/blueprint");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// --- Knowledge Graph ---------------------------------------------------------

export async function getGraph(): Promise<GraphOut> {
  return apiFetch<GraphOut>("/knowledge-graph");
}

export async function rebuildGraph(): Promise<GraphOut> {
  return apiFetch<GraphOut>("/knowledge-graph/rebuild", { method: "POST" });
}

// --- AI Agents ---------------------------------------------------------------

export async function getAgents(): Promise<AgentRoster> {
  return apiFetch<AgentRoster>("/agents");
}

export async function getAgent(agentType: string): Promise<AgentDetail> {
  return apiFetch<AgentDetail>(`/agents/${agentType}`);
}

export async function askAgent(
  agentType: string,
  query: string,
): Promise<AgentAskResponse> {
  return apiFetch<AgentAskResponse>(`/agents/${agentType}/ask`, {
    method: "POST",
    body: { query },
  });
}

// --- Customer Intelligence ---------------------------------------------------

export async function getCustomers(): Promise<CustomerOverview> {
  return apiFetch<CustomerOverview>("/customers");
}

// --- Product Intelligence ----------------------------------------------------

export async function getProducts(): Promise<ProductOverview> {
  return apiFetch<ProductOverview>("/products");
}

// --- Alerts & Monitoring -----------------------------------------------------

export async function getAlerts(): Promise<MonitoringOverview> {
  return apiFetch<MonitoringOverview>("/alerts");
}

// --- Audit & Governance ------------------------------------------------------

export async function getGovernance(): Promise<GovernanceOverview> {
  return apiFetch<GovernanceOverview>("/governance");
}

// --- Data ingestion (file uploads) -------------------------------------------

/**
 * Upload a business file. Uses multipart/form-data, so it bypasses the
 * JSON-only `apiFetch` — the browser sets the multipart boundary itself.
 */
export async function uploadFile(file: File): Promise<UploadDetail> {
  const { accessToken, organization } = useAuthStore.getState();
  const headers: Record<string, string> = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  if (organization) headers["X-Organization-Id"] = organization.id;

  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/uploads`, {
    method: "POST",
    headers,
    body: form,
  });

  if (res.status === 401) {
    useAuthStore.getState().clear();
    throw new ApiError(401, "Session expired. Please sign in again.");
  }
  if (!res.ok) {
    let detail = `Upload failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) {
        detail =
          typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as UploadDetail;
}

export async function listUploads(): Promise<UploadOut[]> {
  return apiFetch<UploadOut[]>("/uploads");
}

export async function commitUpload(
  id: string,
  mapping: CommitMapping,
): Promise<CommitResult> {
  return apiFetch<CommitResult>(`/uploads/${id}/commit`, {
    method: "POST",
    body: mapping,
  });
}

export async function deleteUpload(id: string): Promise<void> {
  await apiFetch(`/uploads/${id}`, { method: "DELETE" });
}
