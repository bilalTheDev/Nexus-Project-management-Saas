import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { m } from 'motion/react'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggleButton } from './ThemeToggleButton'

const links = [
  { href: '#product', label: 'Product' },
  { href: '#workflow', label: 'Workflow' },
  { href: '#security', label: 'Security' },
  { href: '#docs', label: 'Docs' },
]

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <m.header
      className="sticky top-0 z-50"
      initial={false}
      animate={{
        backgroundColor: scrolled ? 'var(--nav-glass)' : 'transparent',
        borderBottomColor: scrolled ? 'var(--border)' : 'transparent',
        backdropFilter: scrolled ? 'blur(24px)' : 'blur(0px)',
      }}
      style={{ borderBottomWidth: 1, borderBottomStyle: 'solid' }}
    >
      <div className="mx-auto flex h-20 max-w-[1280px] items-center justify-between px-8">
        <Link
          to="/"
          className="focus-ring rounded-md"
          aria-label="Nexus home"
        >
          <NexusLogo
            markClassName="size-8"
            className="gap-2"
            wordmarkClassName="text-2xl tracking-[-0.025em] text-[var(--text)]"
          />
        </Link>

        <nav
          className="hidden items-center gap-8 lg:flex"
          aria-label="Primary"
        >
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded text-[15px] leading-[22px] text-[var(--text-muted)] focus-ring hover:text-[var(--text)]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggleButton />
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-[15px] leading-[22px] text-[var(--text-muted)] focus-ring hover:text-[var(--text)]"
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className="rounded-lg bg-[var(--accent)] px-6 py-2 text-[15px] font-medium leading-[22px] text-[var(--on-accent)] shadow-[var(--shadow-button)] focus-ring hover:bg-[var(--accent-hover)]"
          >
            Start free
          </Link>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggleButton />
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-2 text-[var(--text)] focus-ring"
            aria-expanded={open}
            aria-controls="landing-mobile-nav"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {open ? (
        <div
          id="landing-mobile-nav"
          className="border-t border-[var(--border)] bg-[var(--nav-glass)] px-8 py-4 backdrop-blur-xl md:hidden"
        >
          <nav className="flex flex-col gap-1" aria-label="Mobile">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2.5 text-[15px] text-[var(--text-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--text)]"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2">
            <Link
              to="/login"
              className="rounded-lg border border-[var(--border)] px-4 py-2.5 text-center text-[15px] text-[var(--text-muted)]"
              onClick={() => setOpen(false)}
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              className="rounded-lg bg-[var(--accent)] px-4 py-2.5 text-center text-[15px] font-medium text-[var(--on-accent)]"
              onClick={() => setOpen(false)}
            >
              Start free
            </Link>
          </div>
        </div>
      ) : null}
    </m.header>
  )
}
