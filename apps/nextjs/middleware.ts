/**
 * Session guard for all (app)/* routes. Refreshes the Supabase session cookie and redirects
 * unauthenticated users to /login. In keyless dev mode (Supabase not configured) it lets
 * every request through so the UI is runnable before auth is wired. Public auth routes are
 * always allowed.
 */
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/register', '/reset-password']

export async function middleware(req: NextRequest) {
  const res = NextResponse.next({ request: req })
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const { pathname } = req.nextUrl

  if (!url || !key) return res // keyless dev mode: no auth enforcement
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) return res

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => req.cookies.getAll(),
      setAll: (toSet) => {
        for (const { name, value, options } of toSet) res.cookies.set(name, value, options)
      },
    },
  })

  const { data } = await supabase.auth.getUser()
  if (!data.user) {
    const redirect = req.nextUrl.clone()
    redirect.pathname = '/login'
    return NextResponse.redirect(redirect)
  }
  return res
}

export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.).*)'] }
