import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Button } from '@/components/ui/Button'
import { createWorkspace } from '@/lib/workspace-api'

export function WorkspaceCreatePage() {
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [teamType, setTeamType] = useState('software')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: createWorkspace,
    onSuccess: (ws) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      navigate(`/app/${ws.slug}/projects/new`, { replace: true })
    },
    onError: (err) => {
      const detail = err.response?.data
      setError(
        detail?.slug?.[0] ||
          detail?.name?.[0] ||
          detail?.detail ||
          'Could not create workspace.',
      )
    },
  })

  function onNameChange(value) {
    setName(value)
    if (!slug || slug === slugify(name)) {
      setSlug(slugify(value))
    }
  }

  return (
    <ProtectedRoute>
      <div className="flex min-h-screen items-center justify-center bg-paper px-4">
        <form
          className="w-full max-w-md rounded-xl border border-border bg-surface p-8 shadow-sm"
          onSubmit={(e) => {
            e.preventDefault()
            setError('')
            mutation.mutate({ name, slug, team_type: teamType })
          }}
        >
          <p className="font-mono text-xs uppercase tracking-widest text-brand">
            Nexus
          </p>
          <h1 className="mt-2 font-display text-3xl text-ink">
            Name your sovereign workspace
          </h1>
          <p className="mt-2 text-sm text-ink-secondary">
            Create a tenant boundary for projects, members, and activity.
          </p>

          <label className="mt-6 block text-sm font-medium text-ink">
            Workspace name
            <input
              className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              required
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-ink">
            URL slug
            <div className="mt-1 flex items-center gap-2 rounded-md border border-border bg-paper px-3 py-2">
              <span className="font-mono text-xs text-ink-muted">/app/</span>
              <input
                className="min-w-0 flex-1 bg-transparent focus-visible:outline-none"
                value={slug}
                onChange={(e) => setSlug(slugify(e.target.value))}
                required
              />
            </div>
          </label>

          <label className="mt-4 block text-sm font-medium text-ink">
            Team type
            <select
              className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
              value={teamType}
              onChange={(e) => setTeamType(e.target.value)}
            >
              <option value="software">Software</option>
              <option value="business">Business</option>
              <option value="marketing">Marketing</option>
              <option value="other">Other</option>
            </select>
          </label>

          {error ? (
            <p className="mt-3 text-sm text-red-700" role="alert">
              {error}
            </p>
          ) : null}

          <Button
            type="submit"
            className="mt-6 w-full"
            disabled={mutation.isPending}
          >
            {mutation.isPending
              ? 'Creating…'
              : 'Create Workspace & Continue →'}
          </Button>
        </form>
      </div>
    </ProtectedRoute>
  )
}

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}
