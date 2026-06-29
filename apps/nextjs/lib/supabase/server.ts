/**
 * Server-side Supabase client for Server Components / route handlers. Bridges Supabase auth
 * cookies to Next's cookie store using the getAll/setAll contract. Returns null in keyless
 * dev mode. Never uses the service-role key — that lives only in the FastAPI backend.
 */
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { env, supabaseConfigured } from '@/lib/env'

export function getServerSupabase() {
  if (!supabaseConfigured) return null
  const cookieStore = cookies()
  return createServerClient(env.supabaseUrl, env.supabaseAnonKey, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: (toSet) => {
        try {
          for (const { name, value, options } of toSet) cookieStore.set(name, value, options)
        } catch {
          // Called from a Server Component render — safe to ignore; middleware refreshes.
        }
      },
    },
  })
}
