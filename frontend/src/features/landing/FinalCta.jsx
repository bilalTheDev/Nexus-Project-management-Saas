import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { m, useReducedMotion } from 'motion/react'

export function FinalCta() {
  const reduceMotion = useReducedMotion()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')

  function onSubmit(e) {
    e.preventDefault()
    const q = email.trim()
      ? `?email=${encodeURIComponent(email.trim())}`
      : ''
    navigate(`/signup${q}`)
  }

  return (
    <section className="px-10 py-32" aria-labelledby="final-cta-heading">
      <m.div
        className="relative mx-auto max-w-[1200px] overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-6 py-20 text-center shadow-[var(--shadow-cta)] sm:px-16"
        initial={reduceMotion ? false : { opacity: 0, y: 24 }}
        whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-10%' }}
        transition={{ duration: 0.5 }}
      >
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,var(--glow-emerald-soft),transparent_60%)]"
          aria-hidden
        />
        <div className="relative mx-auto max-w-xl">
          <h2
            id="final-cta-heading"
            className="font-display text-[clamp(2rem,5vw,3.5rem)] leading-[1.05] tracking-[-0.03em] text-[var(--text)]"
          >
            Move your team{' '}
            <em className="italic text-[var(--highlight)]">forward.</em>
          </h2>
          <p className="mt-6 text-[17px] leading-[1.6] text-[var(--text-muted)]">
            Spin up a seeded workspace in under a minute. Keyboard-first boards,
            tenant isolation, and audit trails included.
          </p>

          <form
            onSubmit={onSubmit}
            className="mx-auto mt-8 flex max-w-md flex-col gap-3 sm:flex-row"
          >
            <label className="sr-only" htmlFor="landing-cta-email">
              Work email
            </label>
            <input
              id="landing-cta-email"
              type="email"
              name="email"
              autoComplete="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="min-w-0 flex-1 rounded-[10px] border border-[var(--border)] bg-[var(--bg)] px-4 py-3 text-[15px] text-[var(--text)] placeholder:text-[var(--text-muted)] focus-ring"
            />
            <button
              type="submit"
              className="rounded-[10px] bg-[var(--accent)] px-6 py-3 text-[15px] font-medium text-[var(--on-accent)] focus-ring hover:bg-[var(--accent-hover)]"
            >
              Start free
            </button>
          </form>

          <p className="mt-4 font-mono text-xs text-[var(--text-muted)]">
            No credit card ·{' '}
            <Link to="/login?demo=true" className="underline-offset-2 hover:underline">
              Or explore the live demo
            </Link>
          </p>
        </div>
      </m.div>
    </section>
  )
}
