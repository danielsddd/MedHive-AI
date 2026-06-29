/**
 * Browser-side Supabase client (auth only). Returns a configured client when keys are
 * present, or null in keyless dev mode so callers can branch without crashing. Used by the
 * login/register pages to start a session; the resulting JWT is forwarded to FastAPI.
 */
'use client'
import { createBrowserClient } from '@supabase/ssr'
import { env, supabaseConfigured } from '@/lib/env'

export function getBrowserSupabase() {
  if (!supabaseConfigured) return null
  return createBrowserClient(env.supabaseUrl, env.supabaseAnonKey)
}
