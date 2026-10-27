import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  fetchActivity,
  fetchActivityStats,
  unwrapList,
} from '@/lib/workspace-api'

export function ActivityPage() {
  const { workspaceSlug } = useParams()
  const [search, setSearch] = useState('')
  const [project, setProject] = useState('')
  const [eventType, setEventType] = useState('')

  const params = useMemo(() => {
    const next = { days: 14 }
    if (search.trim()) next.search = search.trim()
    if (project) next.project = project
    if (eventType) next.event_type = eventType
    return next
  }, [search, project, eventType])

  const feedQuery = useQuery({
    queryKey: ['activity', workspaceSlug, params],
    queryFn: () => fetchActivity(workspaceSlug, params),
    refetchInterval: 30000,
  })
  const statsQuery = useQuery({
    queryKey: ['activity-stats', workspaceSlug],
    queryFn: () => fetchActivityStats(workspaceSlug),
    refetchInterval: 30000,
  })

  const events = unwrapList(feedQuery.data)
  const groups = groupByDay(events)

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
        Workspace / {workspaceSlug} / Activity Log
      </p>
      <div className="mt-1 flex flex-wrap items-center gap-3">
        <h1 className="font-display text-3xl text-ink sm:text-4xl">
          Activity History
        </h1>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-mint px-2.5 py-1 text-xs font-medium text-brand">
          <span className="h-1.5 w-1.5 rounded-full bg-brand" />
          Live updates active
        </span>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <input
          type="search"
          placeholder="Search actor or task…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[220px] flex-1 rounded-md border border-border bg-paper px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
        />
        <input
          className="rounded-md border border-border bg-paper px-3 py-2 text-sm"
          placeholder="Project key"
          value={project}
          onChange={(e) => setProject(e.target.value.toUpperCase())}
        />
        <select
          className="rounded-md border border-border bg-paper px-3 py-2 text-sm"
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
        >
          <option value="">All Event Types</option>
          <option value="task_status_changed">Status changes</option>
          <option value="comment_added">Comments</option>
          <option value="system">System</option>
          <option value="member_added">Members</option>
        </select>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-8">
          {feedQuery.isLoading ? (
            <p className="text-ink-muted">Loading activity…</p>
          ) : groups.length === 0 ? (
            <p className="text-ink-muted">No activity yet.</p>
          ) : (
            groups.map(([day, items]) => (
              <section key={day}>
                <h2 className="font-mono text-xs uppercase tracking-widest text-ink-muted">
                  {day} — {items.length} occurrence
                  {items.length === 1 ? '' : 's'}
                </h2>
                <ul className="mt-3 space-y-3">
                  {items.map((event) => (
                    <li
                      key={event.id}
                      className="rounded-xl border border-border bg-paper p-4"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-mint text-xs font-semibold text-brand">
                          {(event.actor?.full_name || 'SYS')
                            .split(' ')
                            .map((p) => p[0])
                            .join('')
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-ink">
                            <span className="font-semibold">
                              {event.actor?.full_name || 'SYSTEM'}
                            </span>{' '}
                            {event.summary}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {event.metadata?.from && event.metadata?.to ? (
                              <span className="rounded bg-surface-low px-2 py-0.5 font-mono text-[10px] text-ink-secondary">
                                {event.metadata.from} → {event.metadata.to}
                              </span>
                            ) : null}
                            {event.project_name ? (
                              <span className="rounded bg-mint px-2 py-0.5 text-[10px] text-brand">
                                {event.project_name}
                              </span>
                            ) : null}
                            {event.metadata?.ci ? (
                              <span className="rounded bg-green-100 px-2 py-0.5 text-[10px] text-green-800">
                                {event.metadata.ci}
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-2 text-xs text-ink-muted">
                            {new Date(event.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ))
          )}
        </div>

        <aside className="space-y-4">
          <div className="rounded-xl border border-border bg-paper p-4">
            <h2 className="font-display text-lg text-ink">Velocity</h2>
            <p className="mt-2 font-display text-3xl text-ink">
              {statsQuery.data?.week_events ?? '—'}
            </p>
            <p className="text-xs text-ink-muted">Logged events this week</p>
          </div>
          <div className="rounded-xl border border-border bg-paper p-4">
            <h2 className="font-display text-lg text-ink">Top Contributors</h2>
            <ol className="mt-3 space-y-2">
              {(statsQuery.data?.top_contributors || []).map((c, index) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span>
                    {index + 1}. {c.full_name}
                  </span>
                  <span className="font-mono text-xs text-ink-muted">
                    {c.actions}
                  </span>
                </li>
              ))}
            </ol>
          </div>
          <div className="rounded-xl border border-border bg-surface-low/50 p-4 text-sm text-ink-secondary">
            <p className="font-medium text-ink">Audit Integrity Policy</p>
            <p className="mt-1">
              Significant state transitions are retained for 90 days. Activity
              metadata never stores tokens or secrets.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}

function groupByDay(events) {
  const map = new Map()
  for (const event of events) {
    const day = new Date(event.created_at).toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
    if (!map.has(day)) map.set(day, [])
    map.get(day).push(event)
  }
  return [...map.entries()]
}
