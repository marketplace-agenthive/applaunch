"use client";
// applaunch-web/app/(dashboard)/apps/page.tsx — App list

import useSWR from "swr";
import Link from "next/link";
import { appsApi } from "@/lib/api";
import type { App } from "@/types";
import { formatDate } from "@/lib/utils";
import { Plus, Smartphone } from "lucide-react";

export default function AppsPage() {
  const { data: apps, isLoading, error } = useSWR<App[]>("/apps", () => appsApi.list());

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Your Apps</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage and deploy your mobile apps
          </p>
        </div>
        <Link
          href="/apps/new"
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-xl transition-colors text-sm"
        >
          <Plus className="w-4 h-4" /> New App
        </Link>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-36 rounded-xl border border-border bg-secondary/30 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load apps. Please refresh.
        </div>
      )}

      {apps && apps.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <Smartphone className="w-12 h-12 text-muted-foreground" />
          <div>
            <p className="font-semibold">No apps yet</p>
            <p className="text-muted-foreground text-sm mt-1">
              Create your first app to get started
            </p>
          </div>
          <Link href="/apps/new" className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors">
            Create App
          </Link>
        </div>
      )}

      {apps && apps.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {apps.map((app) => (
            <Link
              key={app.id}
              href={`/apps/${app.id}`}
              className="rounded-xl border border-border p-5 hover:border-green-500/40 hover:bg-secondary/30 transition-all space-y-3"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center text-lg">
                  📱
                </div>
                <div className="min-w-0">
                  <p className="font-semibold truncate">{app.app_name}</p>
                  <p className="text-xs text-muted-foreground truncate">{app.package_name}</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="capitalize">{app.framework.replace("_", " ")}</span>
                <span>{formatDate(app.created_at)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
