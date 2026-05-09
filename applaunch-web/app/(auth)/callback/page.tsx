"use client";
// applaunch-web/app/(auth)/callback/page.tsx
// Supabase OAuth callback handler — exchanges the code for a session, then redirects.

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSupabaseClient } from "@/lib/supabase";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const supabase = getSupabaseClient();
    // Supabase SSR handles the code exchange automatically via the middleware.
    // We just need to wait for the session to be set, then redirect.
    supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_IN") {
        router.replace("/apps");
      }
    });
  }, [router]);

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-muted-foreground text-sm">Signing you in…</p>
      </div>
    </main>
  );
}
