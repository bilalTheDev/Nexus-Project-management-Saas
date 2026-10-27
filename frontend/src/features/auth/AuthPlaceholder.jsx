import { Link, useLocation } from 'react-router-dom'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/Button'

export function AuthPlaceholder({ mode = 'login' }) {
  const location = useLocation()
  const isDemo = new URLSearchParams(location.search).get('demo') === 'true'
  const title = mode === 'signup' ? 'Create your account' : 'Welcome back'
  const subtitle =
    mode === 'signup'
      ? 'Sign up is next — this route is reserved for the auth suite.'
      : isDemo
        ? 'Demo mode requested. Full login UI lands in the next milestone.'
        : 'Sign in is next — this route is reserved for the auth suite.'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-page px-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-8 shadow-panel">
        <div className="flex items-center justify-between gap-3">
          <NexusLogo />
          <ThemeToggle />
        </div>
        <h1 className="mt-6 font-display text-3xl text-ink">{title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
          {subtitle}
        </p>
        <div className="mt-8 flex flex-col gap-2">
          <Button to="/" variant="secondary" className="w-full">
            Back to homepage
          </Button>
          <p className="text-center text-xs text-ink-muted">
            Or go to{' '}
            <Link to={mode === 'signup' ? '/login' : '/signup'} className="text-brand underline">
              {mode === 'signup' ? 'Sign in' : 'Sign up'}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
