// applaunch-web/types/index.ts
/**
 * Shared TypeScript types — mirrors the FastAPI Pydantic schemas.
 */

export type Framework = "react_native" | "expo" | "flutter";

export type BuildStatus =
  | "queued"
  | "building"
  | "signing"
  | "uploading"
  | "done"
  | "failed";

export type BuildTrack = "internal" | "alpha" | "beta" | "production";

export type CredentialType =
  | "android_keystore"
  | "android_service_account"
  | "ios_p8_key"
  | "ios_provisioning";

// ── App ──────────────────────────────────────────────────────────────────────

export interface App {
  id: string;
  user_id: string;
  app_name: string;
  package_name: string;
  framework: Framework;
  description: string | null;
  icon_url: string | null;
  created_at: string;
}

export interface AppCreate {
  app_name: string;
  package_name: string;
  framework: Framework;
  description?: string;
  icon_url?: string;
}

// ── Build ─────────────────────────────────────────────────────────────────────

export interface Build {
  id: string;
  app_id: string;
  status: BuildStatus;
  platform: string;
  version_name: string;
  version_code: number;
  source_s3_key: string | null;
  artifact_s3_key: string | null;
  logs: string | null;
  error_msg: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface BuildLogEvent {
  log_line: string;
  status: BuildStatus;
}

// ── Credentials ───────────────────────────────────────────────────────────────

export interface Credential {
  id: string;
  user_id: string;
  platform: string;
  credential_type: CredentialType;
  metadata: Record<string, string>;
  created_at: string;
}

export interface CredentialReadiness {
  android_keystore: boolean;
  android_service_account: boolean;
  ios_p8_key: boolean;
  ios_provisioning: boolean;
  android_ready: boolean;
  ios_ready: boolean;
}

// ── API ───────────────────────────────────────────────────────────────────────

export interface ApiError {
  error: string;
  code: string;
}
