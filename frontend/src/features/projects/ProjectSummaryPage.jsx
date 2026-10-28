import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchProjectSummary } from '@/lib/workspace-api'

export function ProjectSummaryPage() {
  const { workspaceSlug, projectKey } = useParams()
  const q = useQuery({
    queryKey: ['report-summary', workspaceSlug, projectKey],
    queryFn: () => fetchProjectSummary(workspaceSlug, projectKey),
  })

  const data = q.data || {}
  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
      <h2 className="font-display text-2xl text-[var(--text)]">Summary</h2>
      <p className="text-sm text-[var(--text-secondary)]">
        Open vs done, overdue, and due this week for {projectKey}.
      </p>
      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        {[
          ['Open', data.open],
          ['Done', data.done],
          ['Overdue', data.overdue],
          ['Due this week', data.due_this_week],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4"
          >
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              {label}
            </p>
            <p className="mt-1 font-display text-3xl text-[var(--text)]">
              {q.isLoading ? '—' : value ?? 0}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
