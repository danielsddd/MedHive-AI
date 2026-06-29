/**
 * Sign-in page. Uses the browser Supabase client to start a session; on success the JWT is
 * picked up automatically by the API client for FastAPI calls. In keyless dev mode (Supabase
 * not configured) it shows a notice and a "continue" button that drops straight into the app,
 * since the backend accepts a dev bearer token. All errors surface as toasts, never raw traces.
 */
'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { getBrowserSupabase } from '@/lib/supabase/client'
import { supabaseConfigured } from '@/lib/env'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit() {
    const supabase = getBrowserSupabase()
    if (!supabase) {
      router.push('/home') // keyless dev: no real auth needed
      return
    }
    setBusy(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setBusy(false)
    if (error) {
      toast.error(error.message)
      return
    }
    router.push('/home')
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card w-full max-w-sm p-8">
        <h1
          className="mb-1"
          style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 600 }}
        >
          Sign in
        </h1>
        <p className="mb-6 text-sm" style={{ color: 'hsl(var(--muted))' }}>
          MedCollab · TAU 3346
        </p>

        {!supabaseConfigured && (
          <div
            className="mb-5 rounded-lg p-3 text-sm"
            style={{ background: 'hsl(var(--accent) / 0.08)', color: 'hsl(var(--accent))' }}
          >
            Dev mode: Supabase keys not set. You can continue without signing in.
          </div>
        )}

        <div className="flex flex-col gap-3">
          <input
            className="field"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={!supabaseConfigured}
          />
          <input
            className="field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={!supabaseConfigured}
          />
          <button className="btn mt-1" onClick={onSubmit} disabled={busy}>
            {busy ? 'Signing in…' : supabaseConfigured ? 'Sign in' : 'Continue in dev mode'}
          </button>
        </div>

        <div className="mt-5 flex justify-between text-sm" style={{ color: 'hsl(var(--muted))' }}>
          <Link href="/register">Create account</Link>
          <Link href="/reset-password">Forgot password?</Link>
        </div>
      </div>
    </div>
  )
}
