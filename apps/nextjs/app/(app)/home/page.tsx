/**
 * Authenticated landing/dashboard page. Greets the current user (from useMe) and surfaces a
 * lightweight backend status panel so a first-time developer can confirm the FastAPI <-> DB
 * <-> embedding wiring is live before building features. Real feature cards land in later phases.
 */
'use client'
import { useMe } from '@/hooks/use-me'
import { apiFetch } from '@/lib/api-client'
import { useQuery } from '@tanstack/react-query'

type Health = {
  db: string
  redis: string
  embedding_service: string
  gateway: string
}

function StatusDot({ state }: { state?: string }) {
  const up = state === 'up'
  return (
    <span
      className="inline-block h-2.5 w-2.5 rounded-full"
      style={{ background: up ? 'hsl(var(--accent))' : 'hsl(0 60% 55%)' }}
      aria-label={up ? 'up' : 'down'}
    />
  )
}

export default function HomePage() {
  const { data: me } = useMe()
  const { data: health } = useQuery({
    queryKey: ['healthz'],
    queryFn: () => apiFetch<Health>('/healthz'),
    retry: false,
  })

  const rows: Array<[string, string | undefined]> = [
    ['Database (pgvector)', health?.db],
    ['Redis (ARQ queue)', health?.redis],
    ['Embedding service', health?.embedding_service],
    ['LLM gateway', health?.gateway],
  ]

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 600 }}>
          Welcome{me?.email ? `, ${me.email}` : ''}
        </h1>
        <p style={{ color: 'hsl(var(--muted))' }}>
          Role: <strong>{me?.role ?? '—'}</strong> · Phase 0 foundations are live.
        </p>
      </header>

      <section className="card p-6">
        <h2 className="mb-4 text-lg font-semibold">System status</h2>
        <ul className="flex flex-col gap-3">
          {rows.map(([label, state]) => (
            <li key={label} className="flex items-center justify-between">
              <span style={{ color: 'hsl(var(--muted))' }}>{label}</span>
              <span className="flex items-center gap-2 text-sm">
                <StatusDot state={state} />
                {state ?? 'checking…'}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card p-6">
        <h2 className="mb-2 text-lg font-semibold">Next steps</h2>
        <p style={{ color: 'hsl(var(--muted))' }}>
          Profile ingestion, matching, grants, and ideas arrive in Phases 1–5. The foundations here
          (auth glue, error contract, embedding + LLM gateways, RLS) are ready to build on.
        </p>
      </section>
    </div>
  )
}
