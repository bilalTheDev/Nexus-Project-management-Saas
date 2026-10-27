import { Link } from 'react-router-dom'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggle } from '@/components/ThemeToggle'

export function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="relative min-h-screen bg-page text-ink">
      <div
        className="pointer-events-none absolute inset-0 hero-atmosphere opacity-80"
        aria-hidden="true"
      />
      <div className="relative mx-auto flex min-h-screen max-w-lg flex-col px-4 py-8 sm:px-6">
        <div className="mb-8 flex items-center justify-between">
          <Link to="/" className="focus-ring rounded-md">
            <NexusLogo />
          </Link>
          <ThemeToggle />
        </div>

        <div className="my-auto w-full rounded-2xl border border-border bg-surface p-6 shadow-panel sm:p-8">
          <h1 className="font-display text-3xl tracking-tight text-ink">{title}</h1>
          {subtitle ? (
            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
              {subtitle}
            </p>
          ) : null}
          <div className="mt-8">{children}</div>
          {footer ? <div className="mt-6 text-center text-sm text-ink-secondary">{footer}</div> : null}
        </div>
      </div>
    </div>
  )
}
