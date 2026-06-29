/**
 * Account creation page. Registers a new user via the browser Supabase client; on success the
 * user is prompted to confirm their email (Supabase default) and returned to sign-in. In keyless
 * dev mode it explains that registration is disabled and offers a direct path into the app.
 * Errors are shown as toasts using the friendly mapper, never as raw provider strings.
 */
'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { getBrowserSupabase } from '@/lib/supabase/client'
import { supabaseConfigured } from '@/lib/env'

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit() {
    const supabase = getBrowserSupabase()
    if (!supabase) {
      router.push('/home') // keyless dev: skip real registration
      return
    }
    setBusy(true)
    const { error } = await supabase.auth.signUp({ email, password })
    setBusy(false)
    if (error) {
      toast.error(error.message)
      return
    }
    toast.success('Check your email to confirm your account.')
    router.push('/login')
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card w-full max-w-sm p-8">
        <h1
          className="mb-1"
          style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 600 }}
        >
          Create account
        </h1>
        <p className="mb-6 text-sm" style={{ color: 'hsl(var(--muted))' }}>
          MedCollab · TAU 3346
        </p>

        {!supabaseConfigured && (
          <div
            className="mb-5 rounded-lg p-3 text-sm"
            style={{ background: 'hsl(var(--accent) / 0.08)', color: 'hsl(var(--accent))' }}
          >
            Dev mode: Supabase keys not set. Registration is disabled — continue without it.
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
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={!supabaseConfigured}
          />
          <button className="btn mt-1" onClick={onSubmit} disabled={busy}>
            {busy ? 'Creating…' : supabaseConfigured ? 'Create account' : 'Continue in dev mode'}
          </button>
        </div>

        <div className="mt-5 text-sm" style={{ color: 'hsl(var(--muted))' }}>
          Already have an account? <Link href="/login">Sign in</Link>
        </div>
      </div>
    </div>
  )
}
