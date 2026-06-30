/**
 * Password reset request page. Sends a Supabase recovery email to the supplied address and
 * confirms via toast. In keyless dev mode it explains that reset is unavailable. This page only
 * requests the email; the actual new-password step is handled on Supabase's hosted recovery link.
 */
'use client'
import { supabaseConfigured } from '@/lib/env'
import { getBrowserSupabase } from '@/lib/supabase/client'
import Link from 'next/link'
import { useState } from 'react'
import { toast } from 'sonner'

export default function ResetPasswordPage() {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit() {
    const supabase = getBrowserSupabase()
    if (!supabase) {
      toast.message('Dev mode: password reset is unavailable without Supabase keys.')
      return
    }
    setBusy(true)
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    setBusy(false)
    if (error) {
      toast.error(error.message)
      return
    }
    toast.success('If that email exists, a reset link is on its way.')
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card w-full max-w-sm p-8">
        <h1
          className="mb-1"
          style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 600 }}
        >
          Reset password
        </h1>
        <p className="mb-6 text-sm" style={{ color: 'hsl(var(--muted))' }}>
          We'll email you a recovery link.
        </p>

        {!supabaseConfigured && (
          <div
            className="mb-5 rounded-lg p-3 text-sm"
            style={{ background: 'hsl(var(--accent) / 0.08)', color: 'hsl(var(--accent))' }}
          >
            Dev mode: Supabase keys not set. Password reset is disabled.
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
          <button type="button" className="btn mt-1" onClick={onSubmit} disabled={busy}>
            {busy ? 'Sending…' : 'Send reset link'}
          </button>
        </div>

        <div className="mt-5 text-sm" style={{ color: 'hsl(var(--muted))' }}>
          <Link href="/login">Back to sign in</Link>
        </div>
      </div>
    </div>
  )
}
