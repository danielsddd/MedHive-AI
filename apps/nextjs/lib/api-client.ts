/**
 * Typed fetch wrapper for the ONE backend surface (FastAPI). Attaches the Supabase JWT as a
 * Bearer token, points at NEXT_PUBLIC_API_BASE_URL, and normalises errors into the stable
 * {code,message} shape so callers can pass code straight to errorToMessage(). No business
 * logic lives here — it only transports requests to FastAPI.
 */
import { env } from '@/lib/env'
import { getBrowserSupabase } from '@/lib/supabase/client'

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

async function authHeader(): Promise<Record<string, string>> {
  const supabase = getBrowserSupabase()
  if (!supabase) return { Authorization: 'Bearer dev' } // keyless dev mode
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = { 'Content-Type': 'application/json', ...(await authHeader()), ...init.headers }
  const res = await fetch(`${env.apiBaseUrl}${path}`, { ...init, headers })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const code = body?.code ?? 'internal_error'
    throw new ApiError(code, body?.message ?? 'Request failed', res.status)
  }
  return body as T
}
