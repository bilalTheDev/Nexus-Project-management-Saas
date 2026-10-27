import { Link } from 'react-router-dom'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'

export function WorkspaceCreatePlaceholder() {
  const { user, logout, bootstrapping, isAuthenticated } = useAuth()

  if (bootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-page text-ink-secondary">
        Loading session…
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-page px-4">
        <p className="text-ink-secondary">Please sign in to continue.</p>
        <Button to="/login">Sign in</Button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-page px-4 py-8 text-ink">
      <div className="mx-auto flex max-w-2xl items-center justify-between">
        <NexusLogo />
        <ThemeToggle />
      </div>
      <div className="mx-auto mt-16 max-w-xl rounded-2xl border border-border bg-surface p-8 shadow-panel">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand">
          Signed in
        </p>
        <h1 className="mt-3 font-display text-3xl text-ink">
          Welcome, {user?.full_name || user?.email}
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-ink-secondary">
          Auth is connected. Workspace creation comes next — for now you’re at
          the post-login landing route.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button to="/" variant="secondary">
            Back to homepage
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => logout()}
          >
            Sign out
          </Button>
          <Link to="/login" className="sr-only">
            login
          </Link>
        </div>
      </div>
    </div>
  )
}
