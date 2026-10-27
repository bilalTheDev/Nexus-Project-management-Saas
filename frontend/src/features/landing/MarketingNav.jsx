import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/Button'

const links = [
  { href: '#product', label: 'Product' },
  { href: '#methodology', label: 'Methodology' },
  { href: '#engineering', label: 'Engineering' },
  { href: '#changelog', label: 'Changelog' },
  { href: '#pricing', label: 'Pricing' },
]

export function MarketingNav() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className={`sticky top-0 z-50 border-b transition-colors ${
        scrolled
          ? 'border-border nav-scrolled backdrop-blur-md'
          : 'border-transparent bg-paper/60 backdrop-blur-sm'
      }`}
    >
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" className="focus-ring rounded-md" aria-label="Nexus home">
          <NexusLogo />
        </Link>

        <nav className="hidden items-center gap-7 md:flex" aria-label="Primary">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded text-sm font-semibold text-ink-secondary transition-colors hover:text-ink focus-ring"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <Button to="/login" variant="ghost" className="px-3">
            Sign in
          </Button>
          <Button to="/signup">Get started</Button>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-lg border border-border bg-surface p-2 text-ink focus-ring"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {open ? (
        <div
          id="mobile-nav"
          className="border-t border-border bg-paper/95 px-4 py-4 backdrop-blur md:hidden"
        >
          <nav className="flex flex-col gap-1" aria-label="Mobile">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2.5 text-sm font-semibold text-ink-secondary hover:bg-surface-low hover:text-ink"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2">
            <Button to="/login" variant="secondary" className="w-full">
              Sign in
            </Button>
            <Button to="/signup" className="w-full">
              Get started
            </Button>
          </div>
        </div>
      ) : null}
    </header>
  )
}
