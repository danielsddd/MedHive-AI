/**
 * Sidebar navigation rendered from the NAV registry. Filters entries by the current user's
 * role (permission gating) and highlights the active route. Pure presentation — data comes
 * from useMe(); adding a page never touches this file.
 */
'use client'
import { useMe } from '@/hooks/use-me'
import { NAV } from '@/lib/nav-registry'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function Nav() {
  const pathname = usePathname()
  const { data: me } = useMe()
  const role = me?.role ?? null

  const items = NAV.filter((i) => i.permission === null || i.permission === role)

  return (
    <nav className="flex flex-col gap-1">
      {items.map(({ path, label, icon: Icon }) => {
        const active = pathname.startsWith(path)
        return (
          <Link
            key={path}
            href={path}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
            style={{
              background: active ? 'hsl(var(--accent) / 0.1)' : 'transparent',
              color: active ? 'hsl(var(--accent))' : 'hsl(var(--muted))',
              fontWeight: active ? 600 : 500,
            }}
          >
            <Icon size={17} />
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
