import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { PriorityPill, StatusPill } from '@/features/dashboard/OverviewPage'
import { api } from '@/lib/api'
import { unwrapList } from '@/lib/workspace-api'

export function MyTasksPage() {
  const { workspaceSlug } = useParams()
  const { data, isLoading } = useQuery({
    queryKey: ['my-tasks', workspaceSlug],
    queryFn: () =>
      api
        .get(`/workspaces/${workspaceSlug}/my-tasks/`, {
          params: { status: 'open' },
        })
        .then((r) => r.data),
    refetchInterval: 15_000,
  })
  const tasks = unwrapList(data)

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="font-display text-3xl text-ink">My Tasks</h1>
      <p className="mt-1 text-sm text-ink-secondary">
        Open deliverables assigned to you in this workspace.
      </p>
      {isLoading ? (
        <p className="mt-6 text-ink-muted">Loading…</p>
      ) : (
        <ul className="mt-6 divide-y divide-border rounded-xl border border-border bg-paper">
          {tasks.length === 0 ? (
            <li className="px-4 py-8 text-sm text-ink-muted">
              No open assigned tasks.
            </li>
          ) : (
            tasks.map((task) => (
              <li key={task.id}>
                <Link
                  to={`/app/${workspaceSlug}/tasks/${task.id}?from=${task.project_key}`}
                  className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-surface-low"
                >
                  <span className="font-mono text-xs text-ink-muted">
                    {task.task_key}
                  </span>
                  <span className="flex-1 text-sm font-medium text-ink">
                    {task.title}
                  </span>
                  <PriorityPill priority={task.priority} />
                  <StatusPill status={task.status} />
                </Link>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
