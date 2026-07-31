import { createClient } from '@supabase/supabase-js';

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// ── Guard: missing env vars would cause createClient() to throw at module
// load time (before React mounts) → blank white screen with no error.
// We fall back to placeholder strings so the module loads safely.
// Auth calls will fail gracefully and ProtectedRoute will redirect to /login.
const _url  = supabaseUrl     || 'https://placeholder.supabase.co';
const _key  = supabaseAnonKey || 'placeholder-anon-key';

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    '[SupplyShield] ⚠️  Missing Supabase environment variables.\n' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your Vercel ' +
    'project → Settings → Environment Variables, then redeploy.'
  );
}

/**
 * Supabase client singleton.
 * Configured to use sessionStorage so the auth session
 * persists within the browser tab but clears when it is closed.
 */
export const supabase = createClient(_url, _key, {
  auth: {
    storage: typeof window !== 'undefined' ? window.sessionStorage : undefined,
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/** True when the app was booted without Supabase credentials. */
export const isMissingSupabaseConfig = !supabaseUrl || !supabaseAnonKey;
