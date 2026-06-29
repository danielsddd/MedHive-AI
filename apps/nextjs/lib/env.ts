/**
 * Public frontend environment access + configuration flags. Reads only NEXT_PUBLIC_* values
 * (the only ones safe to ship to the browser). `supabaseConfigured` lets the app degrade
 * gracefully to a keyless dev mode: when Supabase is not set up, auth guards are skipped so
 * the UI still renders. The service-role key is never referenced here.
 */
export const env = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '',
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000',
}

export const supabaseConfigured = Boolean(env.supabaseUrl && env.supabaseAnonKey)
