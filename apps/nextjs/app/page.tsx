/**
 * Root index route. Immediately redirects to /home, which lives under the protected (app)
 * group; middleware decides whether the visitor needs to authenticate first. Keeps a single
 * canonical entry point so the bare domain never 404s.
 */
import { redirect } from 'next/navigation'

export default function IndexPage() {
  redirect('/home')
}
