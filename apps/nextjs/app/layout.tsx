import { Providers } from '@/components/providers'
/**
 * Root layout. Loads the display (Fraunces) + body (IBM Plex Sans) fonts via next/font and
 * exposes them as CSS variables, mounts global styles, and wraps the tree in app-wide
 * providers (TanStack Query + Sonner toasts). Applies to every route, public and protected.
 */
import type { Metadata } from 'next'
import { Fraunces, IBM_Plex_Sans } from 'next/font/google'
import './globals.css'

const display = Fraunces({ subsets: ['latin'], variable: '--font-display', display: 'swap' })
const sans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'MedCollab — TAU 3346',
  description: 'AI platform for medical research collaboration.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
