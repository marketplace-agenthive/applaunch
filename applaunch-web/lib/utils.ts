// applaunch-web/lib/utils.ts

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { BuildStatus } from "@/types";

/** Merge Tailwind classes safely (shadcn/ui convention). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format an ISO date string for display. */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

/** Map a build status to its Tailwind color class. */
export function statusColor(status: BuildStatus): string {
  const map: Record<BuildStatus, string> = {
    queued: "text-gray-400",
    building: "text-blue-400",
    signing: "text-yellow-400",
    uploading: "text-purple-400",
    done: "text-green-400",
    failed: "text-red-400",
  };
  return map[status] ?? "text-gray-400";
}

/** Map a build status to a badge variant. */
export function statusBadgeVariant(
  status: BuildStatus
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "done") return "default";
  if (status === "failed") return "destructive";
  return "secondary";
}
