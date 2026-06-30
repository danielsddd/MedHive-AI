import { Nav } from '@/components/nav'
/**
 * Protected application shell for every (app)/* route. Renders the persistent sidebar
 * (brand + role-filtered Nav) alongside the routed page content. Auth enforcement happens in
 * middleware.ts; this file is pure layout. Keep it thin — pages own their own logic.
 */
import Link from 'next/link'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside
        className="flex w-60 flex-col gap-6 border-r p-5"
        style={{ background: 'hsl(var(--surface))' }}
      >
        <Link href="/home" className="flex flex-col leading-tight">
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 600 }}>
            MedCollab
          </span>
          <span style={{ color: 'hsl(var(--muted))', fontSize: 12 }}>TAU 3346</span>
        </Link>
        <Nav />
      </aside>
      <main className="flex-1 p-8">
        <div className="mx-auto w-full max-w-5xl">{children}</div>
      </main>
    </div>
  )
}
