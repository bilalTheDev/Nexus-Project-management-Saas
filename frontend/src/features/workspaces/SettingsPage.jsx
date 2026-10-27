import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchWorkspace } from '@/lib/workspace-api'

export function SettingsPage() {
  const { workspaceSlug } = useParams()
  const { data, isLoading } = useQuery({
    queryKey: ['workspace', workspaceSlug],
    queryFn: () => fetchWorkspace(workspaceSlug),
  })

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <h1 className="font-display text-3xl text-ink">Workspace Settings</h1>
      <p className="mt-2 text-sm text-ink-secondary">
        General settings for this pass. Full export/delete controls ship in a
        later milestone.
      </p>
      {isLoading ? (
        <p className="mt-6 text-ink-muted">Loading…</p>
      ) : (
        <div className="mt-6 space-y-4 rounded-xl border border-border bg-paper p-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">Name</p>
            <p className="text-ink">{data?.name}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">Slug</p>
            <p className="font-mono text-ink">{data?.slug}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">Your role</p>
            <p className="capitalize text-ink">{data?.role}</p>
          </div>
        </div>
      )}
    </div>
  )
}
