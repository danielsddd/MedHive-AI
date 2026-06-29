/**
 * TanStack Query hook that loads the current user + role from FastAPI's GET /me. Centralises
 * the "who am I" fetch so pages stay thin and the role drives nav/permission rendering.
 */
'use client'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api-client'

export type Me = { user_id: string; email: string | null; role: string }

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => apiFetch<Me>('/auth/me'),
    retry: false,
  })
}
