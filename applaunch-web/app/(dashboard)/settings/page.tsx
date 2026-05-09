"use client";
// applaunch-web/app/(dashboard)/settings/page.tsx — Credential management

import useSWR from "swr";
import { credentialsApi } from "@/lib/api";
import type { CredentialReadiness } from "@/types";
import { CheckCircle, XCircle } from "lucide-react";

function CredentialRow({ label, ready }: { label: string; ready: boolean }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <span className="text-sm font-medium">{label}</span>
      {ready ? (
        <span className="flex items-center gap-1.5 text-green-500 text-sm">
          <CheckCircle className="w-4 h-4" /> Connected
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-muted-foreground text-sm">
          <XCircle className="w-4 h-4" /> Not uploaded
        </span>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { data, isLoading } = useSWR<CredentialReadiness>(
    "/credentials/check",
    () => credentialsApi.check()
  );

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage your signing credentials and account settings
        </p>
      </div>

      <div className="rounded-xl border border-border p-5 space-y-1">
        <h2 className="font-semibold mb-3">Android Credentials</h2>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-8 rounded bg-secondary/50 animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <CredentialRow label="Android Keystore (.jks)" ready={data?.android_keystore ?? false} />
            <CredentialRow label="Play Console Service Account" ready={data?.android_service_account ?? false} />
          </>
        )}
        <div className="pt-4">
          <a
            href="/onboarding"
            className="text-sm text-green-500 hover:underline"
          >
            → Update credentials
          </a>
        </div>
      </div>
    </div>
  );
}
