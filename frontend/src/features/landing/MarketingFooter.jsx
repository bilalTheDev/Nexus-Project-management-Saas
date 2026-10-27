import { Link } from 'react-router-dom'
import { NexusLogo } from '@/components/NexusLogo'

const COPYRIGHT_YEAR = 2026

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#product' },
      { label: 'Methodology', href: '#methodology' },
      { label: 'Pricing', href: '#pricing' },
      { label: 'Changelog', href: '#changelog' },
    ],
  },
  {
    title: 'Engineering',
    links: [
      { label: 'API', href: '#engineering' },
      { label: 'Architecture', href: '#engineering' },
      { label: 'Security', href: '#engineering' },
      { label: 'Status', href: '#changelog' },
    ],
  },
  {
    title: 'Organization',
    links: [
      { label: 'About', href: '#' },
      { label: 'Sign in', href: '/login' },
      { label: 'Sign up', href: '/signup' },
      { label: 'Privacy', href: '#' },
    ],
  },
]

export function MarketingFooter() {
  return (
    <footer id="changelog" className="scroll-mt-20 bg-surface-low">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 md:grid-cols-[1.2fr_repeat(3,1fr)]">
          <div>
            <NexusLogo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink-secondary">
              Project management for focused teams. Clear ownership, fluid
              execution, and zero ambient panic.
            </p>
            <div className="mt-5 flex items-center gap-3 text-ink-secondary">
              <a
                href="https://github.com"
                className="rounded p-1 transition-colors hover:text-ink focus-ring"
                aria-label="GitHub"
              >
                <SocialGithub />
              </a>
              <a
                href="https://twitter.com"
                className="rounded p-1 transition-colors hover:text-ink focus-ring"
                aria-label="X / Twitter"
              >
                <SocialX />
              </a>
              <a
                href="https://linkedin.com"
                className="rounded p-1 transition-colors hover:text-ink focus-ring"
                aria-label="LinkedIn"
              >
                <SocialLinkedIn />
              </a>
            </div>
          </div>

          {columns.map((column) => (
            <div key={column.title}>
              <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-muted">
                {column.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith('/') ? (
                      <Link
                        to={link.href}
                        className="text-sm text-ink-secondary transition-colors hover:text-ink"
                      >
                        {link.label}
                      </Link>
                    ) : (
                      <a
                        href={link.href}
                        className="text-sm text-ink-secondary transition-colors hover:text-ink"
                      >
                        {link.label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-ink-muted">
            © {COPYRIGHT_YEAR} Nexus. Built for portfolio demonstration.
          </p>
          <p className="inline-flex items-center gap-2 font-mono text-[11px] text-ink-secondary">
            <span className="size-1.5 rounded-full bg-status-done" />
            All systems operational
          </p>
        </div>
      </div>
    </footer>
  )
}

function SocialGithub() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.52 2.87 8.35 6.84 9.7.5.1.68-.22.68-.48 0-.24-.01-.87-.01-1.7-2.78.62-3.37-1.37-3.37-1.37-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.31.1-2.73 0 0 .84-.27 2.75 1.05A9.3 9.3 0 0 1 12 6.84c.85 0 1.71.12 2.51.35 1.9-1.32 2.74-1.05 2.74-1.05.55 1.42.2 2.47.1 2.73.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.8-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .26.18.58.69.48A10.27 10.27 0 0 0 22 12.26C22 6.58 17.52 2 12 2Z" />
    </svg>
  )
}

function SocialX() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M18.9 2H22l-6.78 7.75L23.2 22h-6.5l-5.1-6.66L5.7 22H2.6l7.25-8.29L.8 2h6.66l4.6 6.1L18.9 2Zm-1.14 18h1.8L6.35 3.9H4.42L17.76 20Z" />
    </svg>
  )
}

function SocialLinkedIn() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.24 8.25h4.52V24H.24V8.25zM8.34 8.25h4.33v2.14h.06c.6-1.14 2.08-2.34 4.28-2.34 4.58 0 5.43 3.01 5.43 6.93V24h-4.52v-7.9c0-1.88-.03-4.3-2.62-4.3-2.63 0-3.03 2.05-3.03 4.16V24H8.34V8.25z" />
    </svg>
  )
}
