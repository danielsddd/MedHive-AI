/**
 * App-wide client providers: a singleton TanStack Query client for server-state caching and
 * the Sonner <Toaster /> so any component can surface success/error/loading toasts. Wraps the
 * whole tree from the root layout.
 */
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={client}>
      {children}
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}
