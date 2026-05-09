// applaunch-web/lib/supabase.ts
/**
 * Supabase browser client — used in Client Components.
 * For Server Components, use createServerClient from @supabase/ssr.
 */

import { createBrowserClient } from "@supabase/ssr";

export function createSupabaseClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

/** Singleton browser client for use in hooks and client components. */
let _client: ReturnType<typeof createSupabaseClient> | null = null;

export function getSupabaseClient() {
  if (!_client) _client = createSupabaseClient();
  return _client;
}
