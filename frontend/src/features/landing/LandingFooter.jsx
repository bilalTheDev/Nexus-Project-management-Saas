import { Link } from 'react-router-dom'
import { NexusLogo } from '@/components/NexusLogo'

const COLUMNS = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#capabilities' },
      { label: 'Integrations', href: '#workflow' },
      { label: 'Enterprise', href: '#security' },
      { label: 'Changelog', href: '#docs' },
    ],
  },
  {
    title: 'Developers',
    links: [
      { label: 'Documentation', href: '#docs' },
      { label: 'API Reference', href: '#docs' },
      { label: 'SDKs & Libraries', href: '#docs' },
      { label: 'Community Hub', href: '#docs' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#' },
      { label: 'Careers', href: '#' },
      { label: 'Press Kit', href: '#' },
      { label: 'Contact', href: '#' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#' },
      { label: 'Terms of Service', href: '#' },
      { label: 'Security Whitepaper', href: '#security' },
      { label: 'Compliance & SOC 2', href: '#security' },
    ],
  },
]

export function LandingFooter() {
  return (
    <footer id="docs" className="scroll-mt-24 border-t border-[var(--border)]">
      <div className="mx-auto max-w-[1280px] px-8 py-8">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="font-display text-[17px] text-[var(--text)]">
                {col.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[15px] leading-[18px] text-[var(--text-muted)] hover:text-[var(--text)] focus-ring rounded"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t border-[var(--border)] pt-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="inline-flex items-center gap-2 rounded-full bg-[var(--surface-2)] px-4 py-2">
            <span className="relative flex size-2">
              <span className="absolute inset-0 animate-ping rounded-full bg-[var(--accent-text)] opacity-40" />
              <span className="relative size-2 rounded-full bg-[var(--accent-text)]" />
            </span>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              All systems operational
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/" className="focus-ring rounded-md">
              <NexusLogo
                markClassName="size-6"
                className="gap-2"
                wordmarkClassName="text-lg text-[var(--text)]"
              />
            </Link>
            <p className="font-mono text-xs text-[var(--text-muted)]">
              © 2026 Nexus Labs
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
