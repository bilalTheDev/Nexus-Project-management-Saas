import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AuthLayout } from '@/features/auth/AuthLayout'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { acceptInvite, previewInvite } from '@/lib/workspace-api'

export function InviteAcceptPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated, bootstrapping } = useAuth()
  const [acceptError, setAcceptError] = useState('')

  const previewQuery = useQuery({
    queryKey: ['invite-preview', token],
    queryFn: () => previewInvite(token),
    enabled: Boolean(token),
    retry: false,
  })

  const acceptMutation = useMutation({
    mutationFn: () => acceptInvite(token),
    onSuccess: (data) => {
      navigate(`/app/${data.workspace_slug}/dashboard`, { replace: true })
    },
    onError: (err) => {
      const detail = err.response?.data?.detail
      setAcceptError(
        typeof detail === 'string'
          ? detail
          : 'Could not accept this invite. Try signing in with the invited email.',
      )
    },
  })

  const preview = previewQuery.data
  const emailMatch = useMemo(() => {
    if (!user?.email || !preview?.email) return false
    return user.email.toLowerCase() === preview.email.toLowerCase()
  }, [user, preview])

  if (previewQuery.isLoading || bootstrapping) {
    return (
      <AuthLayout title="Checking invite…" subtitle="One moment.">
        <p className="text-sm text-ink-muted">Loading invite details…</p>
      </AuthLayout>
    )
  }

  if (previewQuery.isError || !preview) {
    return (
      <AuthLayout title="Invite unavailable" subtitle="This link cannot be used.">
        <p className="text-sm text-ink-secondary">
          The invite may have expired or already been accepted.
        </p>
        <Button to="/login" className="mt-4">
          Go to sign in
        </Button>
      </AuthLayout>
    )
  }

  const signupHref = `/signup?email=${encodeURIComponent(preview.email)}&invite=${encodeURIComponent(token)}`
  const loginHref = `/login?email=${encodeURIComponent(preview.email)}&invite=${encodeURIComponent(token)}`

  return (
    <AuthLayout
      title={`Join ${preview.workspace_name}`}
      subtitle={
        preview.invited_by
          ? `${preview.invited_by} invited you as ${preview.role.replace('_', ' ')}.`
          : `You've been invited as ${preview.role.replace('_', ' ')}.`
      }
    >
      <div className="space-y-4 rounded-lg border border-border bg-paper p-4 text-sm">
        <p>
          <span className="text-ink-muted">Invited email</span>
          <br />
          <span className="font-medium text-ink">{preview.email}</span>
        </p>
        <p className="text-ink-secondary">
          Expires {new Date(preview.expires_at).toLocaleString()}
        </p>
      </div>

      {acceptError ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {acceptError}
        </p>
      ) : null}

      {!isAuthenticated ? (
        <div className="mt-5 flex flex-col gap-2">
          {preview.account_exists ? (
            <>
              <Button to={loginHref} className="w-full">
                Sign in to accept
              </Button>
              <p className="text-center text-xs text-ink-muted">
                Use {preview.email} to join this workspace.
              </p>
            </>
          ) : (
            <>
              <Button to={signupHref} className="w-full">
                Create account & join
              </Button>
              <p className="text-center text-xs text-ink-muted">
                Already have an account?{' '}
                <Link to={loginHref} className="text-brand underline">
                  Sign in
                </Link>
              </p>
            </>
          )}
        </div>
      ) : emailMatch ? (
        <Button
          className="mt-5 w-full"
          disabled={acceptMutation.isPending}
          onClick={() => {
            setAcceptError('')
            acceptMutation.mutate()
          }}
        >
          {acceptMutation.isPending ? 'Joining…' : 'Accept invite'}
        </Button>
      ) : (
        <div className="mt-5 space-y-3">
          <p className="text-sm text-ink-secondary">
            You&apos;re signed in as <strong>{user.email}</strong>, but this invite
            is for <strong>{preview.email}</strong>.
          </p>
          <Button to={loginHref} variant="secondary" className="w-full">
            Switch account
          </Button>
        </div>
      )}
    </AuthLayout>
  )
}
