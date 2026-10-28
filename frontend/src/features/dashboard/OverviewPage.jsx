import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchDashboard } from '@/lib/workspace-api'

export function OverviewPage() {
  const { workspaceSlug } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard', workspaceSlug],
    queryFn: () => fetchDashboard(workspaceSlug),
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return <PageFrame title="Overview">Loading dashboard…</PageFrame>
  }
  if (isError || !data) {
    return <PageFrame title="Overview">Could not load dashboard.</PageFrame>
  }

  const { metrics, urgent_tasks, projects_health, recent_activity } = data

  return (
    <PageFrame
      eyebrow={new Date().toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      })}
      title={`Overview — ${workspaceSlug}`}
    >
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Active Projects"
          value={String(metrics.active_projects)}
          hint="On schedule"
        />
        <Metric
          label="My Open Tasks"
          value={String(metrics.my_open_tasks)}
          hint="Assigned to you"
        />
        <Metric
          label="Overdue"
          value={String(metrics.overdue)}
          hint="Requires action"
          danger={metrics.overdue > 0}
          emphasis={metrics.overdue > 0}
        />
        <Metric
          label="Completed"
          value={String(metrics.completed_cycle)}
          hint="This workspace"
        />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <section>
          <h2 className="font-display text-xl text-ink">
            Tasks Requiring Attention
          </h2>
          <ul className="surface-card mt-3 divide-y divide-border overflow-hidden">
            {urgent_tasks.length === 0 ? (
              <li className="px-4 py-6 text-sm text-ink-muted">
                No urgent items right now.
              </li>
            ) : (
              urgent_tasks.map((task) => (
                <li key={task.id}>
                  <Link
                    to={`/app/${workspaceSlug}/tasks/${task.id}`}
                    className="row-raise flex flex-wrap items-center gap-3 px-4 py-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
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

          <h2 className="mt-8 font-display text-xl text-ink">
            Project Health & Momentum
          </h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {projects_health.map((project) => (
              <Link
                key={project.id}
                to={`/app/${workspaceSlug}/projects/${project.key}/board`}
                className="surface-card surface-card-hover block p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-ink">{project.name}</p>
                    <p className="font-mono text-xs text-ink-muted">
                      {project.key}
                    </p>
                  </div>
                  <span className="rounded-full bg-mint px-2 py-0.5 text-xs text-brand">
                    {project.progress}%
                  </span>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-low">
                  <div
                    className="h-full rounded-full bg-brand"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-ink-muted">
                  {project.resolved} of {project.total} resolved ·{' '}
                  {project.open_tasks} open
                </p>
              </Link>
            ))}
          </div>
        </section>

        <aside className="space-y-4">
          <div className="surface-card p-4">
            <h2 className="font-display text-lg text-ink">Recent Activity</h2>
            <ul className="mt-3 space-y-3">
              {recent_activity.map((event) => (
                <li key={event.id} className="text-sm">
                  <p className="text-ink">
                    {event.actor?.full_name || 'System'} {event.summary}
                  </p>
                  <p className="font-mono text-xs text-ink-muted">
                    {new Date(event.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-brand/25 bg-mint/50 p-4 shadow-hairline">
            <p className="font-mono text-[10px] uppercase tracking-widest text-brand">
              Studio Handbook
            </p>
            <p className="mt-1 text-sm text-ink">
              Sprint Cycle 4 Protocol — deployment freeze rules and PR template
              standards for the Q4 launch window.
            </p>
          </div>
        </aside>
      </div>
    </PageFrame>
  )
}

function PageFrame({ eyebrow, title, children }) {
  return (
    <div className="relative mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {eyebrow ? (
        <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
          {eyebrow}
        </p>
      ) : null}
      <h1 className="mt-1 font-display text-3xl tracking-tight text-ink sm:text-4xl">
        {title}
      </h1>
      <div className="mt-6">{children}</div>
    </div>
  )
}

function Metric({ label, value, hint, danger, emphasis }) {
  return (
    <div
      className={`surface-card surface-card-hover p-4 ${emphasis ? 'glow-accent' : ''}`}
    >
      <p className="text-xs uppercase tracking-wide text-ink-muted">{label}</p>
      <p
        className={`mt-1 font-display text-3xl tracking-tight ${danger ? 'text-danger' : 'text-ink'}`}
      >
        {value}
      </p>
      <p className="mt-1 text-xs text-ink-secondary">{hint}</p>
    </div>
  )
}

export function PriorityPill({ priority }) {
  const styles = {
    urgent: 'bg-danger-soft text-danger',
    high: 'bg-warning-soft text-warning',
    medium: 'bg-surface-low text-ink-secondary',
    low: 'bg-surface-low text-ink-muted',
  }
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${styles[priority] || styles.medium}`}
    >
      {priority}
    </span>
  )
}

export function StatusPill({ status }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-low px-2 py-0.5 font-mono text-[10px] uppercase text-ink-secondary">
      <span className="status-dot text-brand" aria-hidden />
      {status?.replaceAll('_', ' ')}
    </span>
  )
}
