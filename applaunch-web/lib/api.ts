// applaunch-web/lib/api.ts
/**
 * Typed API client for the AppLaunch FastAPI backend.
 * All components import from here — never call fetch() directly in components.
 */

import type {
  App,
  AppCreate,
  Build,
  BuildTrack,
  Credential,
  CredentialReadiness,
} from "@/types";
import { getSupabaseClient } from "./supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Get the current user's JWT from Supabase and return Authorization header. */
async function authHeader(): Promise<Record<string, string>> {
  const supabase = getSupabaseClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new Error("Not authenticated");
  return { Authorization: `Bearer ${session.access_token}` };
}

/** Generic fetch wrapper with error handling. */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await authHeader();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Apps ─────────────────────────────────────────────────────────────────────

export const appsApi = {
  list: () => apiFetch<App[]>("/apps"),

  get: (id: string) => apiFetch<App>(`/apps/${id}`),

  create: (body: AppCreate) =>
    apiFetch<App>("/apps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/apps/${id}`, { method: "DELETE" }),
};

// ── Builds ───────────────────────────────────────────────────────────────────

export const buildsApi = {
  get: (id: string) => apiFetch<Build>(`/builds/${id}`),

  triggerAndroid: (
    appId: string,
    sourceZip: File,
    opts: { versionName: string; versionCode: number; track: BuildTrack }
  ) => {
    const fd = new FormData();
    fd.append("app_id", appId);
    fd.append("version_name", opts.versionName);
    fd.append("version_code", String(opts.versionCode));
    fd.append("track", opts.track);
    fd.append("source_zip", sourceZip);
    return apiFetch<Build>("/builds/android", { method: "POST", body: fd });
  },

  /**
   * Opens an SSE connection and calls `onEvent` for each log line.
   * Returns a cleanup function — call it in useEffect's return.
   */
  streamLogs: async (
    buildId: string,
    onEvent: (line: string, status: string) => void
  ): Promise<() => void> => {
    const supabase = getSupabaseClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token ?? "";
    // Note: EventSource doesn't support custom headers — append token as query param
    // The backend should also accept ?token= for SSE connections
    const es = new EventSource(
      `${API_BASE}/builds/${buildId}/stream?token=${token}`
    );
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      onEvent(data.log_line, data.status);
      if (["done", "failed"].includes(data.status)) es.close();
    };
    return () => es.close();
  },
};

// ── Credentials ───────────────────────────────────────────────────────────────

export const credentialsApi = {
  check: () => apiFetch<CredentialReadiness>("/credentials/check"),

  list: () => apiFetch<Credential[]>("/credentials"),

  uploadKeystore: (
    keystoreFile: File,
    meta: { keyAlias: string; storePassword: string; keyPassword: string }
  ) => {
    const fd = new FormData();
    fd.append("keystore_file", keystoreFile);
    fd.append("key_alias", meta.keyAlias);
    fd.append("store_password", meta.storePassword);
    fd.append("key_password", meta.keyPassword);
    return apiFetch<Credential>("/credentials/android/keystore", {
      method: "POST",
      body: fd,
    });
  },

  uploadServiceAccount: (jsonFile: File) => {
    const fd = new FormData();
    fd.append("service_account_json", jsonFile);
    return apiFetch<Credential>("/credentials/android/service-account", {
      method: "POST",
      body: fd,
    });
  },
};
