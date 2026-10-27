import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'

export function BottomCta() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    const params = email.trim()
      ? `?email=${encodeURIComponent(email.trim())}`
      : ''
    navigate(`/signup${params}`)
  }

  return (
    <section
      id="pricing"
      className="scroll-mt-20 border-b border-border bg-paper"
    >
      <div className="mx-auto max-w-3xl px-4 py-20 text-center sm:px-6 sm:py-28">
        <h2 className="font-display text-3xl leading-tight tracking-tight text-ink sm:text-5xl">
          Ready for a calmer, more deliberate workspace?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-ink-secondary">
          Create a workspace in minutes. Explore the seeded demo, or start fresh
          with your own projects and Kanban board.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mx-auto mt-8 flex max-w-lg flex-col gap-2 rounded-xl border border-border bg-surface p-2 shadow-sm sm:flex-row sm:items-center"
        >
          <label htmlFor="cta-email" className="sr-only">
            Work email
          </label>
          <input
            id="cta-email"
            type="email"
            name="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="min-w-0 flex-1 rounded-lg border-0 bg-transparent px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          />
          <Button type="submit" className="w-full shrink-0 sm:w-auto">
            Create Workspace
          </Button>
        </form>

        <p className="mt-4 font-mono text-[11px] tracking-wide text-ink-muted">
          Free forever for small teams · $0 to get started · No credit card
        </p>
      </div>
    </section>
  )
}
