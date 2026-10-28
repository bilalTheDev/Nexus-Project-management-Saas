import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  fetchBreakdown,
  fetchBurndown,
  fetchCfd,
  fetchCreatedVsResolved,
  fetchProjectSummary,
  fetchSprints,
  fetchVelocity,
  unwrapList,
} from '@/lib/workspace-api'
import Charts from './ReportCharts'

function ChartShell({ title, description, children, loading, error, onRetry, table }) {
  const [showTable, setShowTable] = useState(false)
  return (
    <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-medium text-[var(--text)]">{title}</h3>
          <p className="text-sm text-[var(--text-secondary)]">{description}</p>
        </div>
        <button
          type="button"
          className="text-xs text-[var(--text-muted)] underline"
          onClick={() => setShowTable((v) => !v)}
        >
          {showTable ? 'Chart view' : 'Table view'}
        </button>
      </div>
      <div className="mt-4 min-h-[220px]">
        {loading ? (
          <div className="h-[220px] animate-pulse rounded-xl bg-[var(--surface-2)]" />
        ) : error ? (
          <div className="flex h-[220px] flex-col items-center justify-center gap-2 text-sm">
            <p className="text-[var(--danger)]">Could not load chart.</p>
            <button type="button" className="underline" onClick={onRetry}>
              Retry
            </button>
          </div>
        ) : showTable ? (
          table
        ) : (
          children
        )}
      </div>
    </section>
  )
}

export function ReportsPage() {
  const { workspaceSlug, projectKey } = useParams()
  const [breakdownBy, setBreakdownBy] = useState('priority')

  const summaryQ = useQuery({
    queryKey: ['report-summary', workspaceSlug, projectKey],
    queryFn: () => fetchProjectSummary(workspaceSlug, projectKey),
  })
  const velocityQ = useQuery({
    queryKey: ['report-velocity', workspaceSlug, projectKey],
    queryFn: () => fetchVelocity(workspaceSlug, projectKey),
  })
  const cfdQ = useQuery({
    queryKey: ['report-cfd', workspaceSlug, projectKey],
    queryFn: () => fetchCfd(workspaceSlug, projectKey),
  })
  const createdQ = useQuery({
    queryKey: ['report-cvr', workspaceSlug, projectKey],
    queryFn: () => fetchCreatedVsResolved(workspaceSlug, projectKey),
  })
  const breakdownQ = useQuery({
    queryKey: ['report-breakdown', workspaceSlug, projectKey, breakdownBy],
    queryFn: () => fetchBreakdown(workspaceSlug, projectKey, breakdownBy),
  })
  const sprintsQ = useQuery({
    queryKey: ['sprints', workspaceSlug, projectKey],
    queryFn: () => fetchSprints(workspaceSlug, projectKey),
  })

  const sprints = unwrapList(sprintsQ.data)
  const activeOrLast =
    sprints.find((s) => s.status === 'active') ||
    sprints.find((s) => s.status === 'completed') ||
    sprints[0]

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
      <div>
        <h2 className="font-display text-2xl text-[var(--text)]">Reports</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Aggregates from the server — colours use theme tokens and every chart has a table toggle.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        {[
          ['Open', summaryQ.data?.open],
          ['Done', summaryQ.data?.done],
          ['Overdue', summaryQ.data?.overdue],
          ['Due this week', summaryQ.data?.due_this_week],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4"
          >
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              {label}
            </p>
            <p className="mt-1 font-display text-3xl text-[var(--text)]">
              {summaryQ.isLoading ? '—' : value ?? 0}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
          <ChartShell
            title="Velocity"
            description="Committed vs completed points across recent sprints."
            loading={velocityQ.isLoading}
            error={velocityQ.isError}
            onRetry={() => velocityQ.refetch()}
            table={
              <table className="w-full text-left text-sm">
                <thead>
                  <tr>
                    <th>Sprint</th>
                    <th>Committed</th>
                    <th>Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {(velocityQ.data?.bars || []).map((b) => (
                    <tr key={b.sprint_id}>
                      <td>{b.sprint_name}</td>
                      <td>{b.committed}</td>
                      <td>{b.completed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            }
          >
            {(velocityQ.data?.bars || []).length === 0 ? (
              <EmptyChart label="Complete a sprint to see velocity." />
            ) : (
              <Charts.VelocityChart data={velocityQ.data.bars} />
            )}
          </ChartShell>

          <ChartShell
            title="Created vs resolved"
            description="Weekly created and completed issue counts."
            loading={createdQ.isLoading}
            error={createdQ.isError}
            onRetry={() => createdQ.refetch()}
            table={
              <table className="w-full text-left text-sm">
                <thead>
                  <tr>
                    <th>Week</th>
                    <th>Created</th>
                    <th>Resolved</th>
                  </tr>
                </thead>
                <tbody>
                  {(createdQ.data?.series || []).map((row) => (
                    <tr key={row.week}>
                      <td>{row.week}</td>
                      <td>{row.created}</td>
                      <td>{row.resolved}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            }
          >
            {(createdQ.data?.series || []).length === 0 ? (
              <EmptyChart label="No weekly activity yet." />
            ) : (
              <Charts.CreatedResolvedChart data={createdQ.data.series} />
            )}
          </ChartShell>

          <ChartShell
            title="Cumulative flow"
            description="Issue count per status per day."
            loading={cfdQ.isLoading}
            error={cfdQ.isError}
            onRetry={() => cfdQ.refetch()}
            table={
              <p className="text-sm text-[var(--text-muted)]">
                {(cfdQ.data?.series || []).length} day rows ·{' '}
                {(cfdQ.data?.statuses || []).map((s) => s.name).join(', ')}
              </p>
            }
          >
            {(cfdQ.data?.series || []).length === 0 ? (
              <EmptyChart label="No flow data in range." />
            ) : (
              <Charts.CfdChart
                series={cfdQ.data.series}
                statuses={cfdQ.data.statuses}
              />
            )}
          </ChartShell>

          <ChartShell
            title="Breakdown"
            description="Share of issues by field."
            loading={breakdownQ.isLoading}
            error={breakdownQ.isError}
            onRetry={() => breakdownQ.refetch()}
            table={
              <table className="w-full text-left text-sm">
                <thead>
                  <tr>
                    <th>Slice</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {(breakdownQ.data?.slices || []).map((s) => (
                    <tr key={s.key}>
                      <td>{s.label}</td>
                      <td>{s.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            }
          >
            <div className="mb-2 flex gap-2 text-xs">
              {['priority', 'assignee', 'type'].map((key) => (
                <button
                  key={key}
                  type="button"
                  className={
                    breakdownBy === key
                      ? 'rounded bg-[var(--surface-3)] px-2 py-1'
                      : 'px-2 py-1 text-[var(--text-muted)]'
                  }
                  onClick={() => setBreakdownBy(key)}
                >
                  {key}
                </button>
              ))}
            </div>
            {(breakdownQ.data?.slices || []).length === 0 ? (
              <EmptyChart label="No issues to break down." />
            ) : (
              <Charts.BreakdownChart data={breakdownQ.data.slices} />
            )}
          </ChartShell>
        </div>

        {activeOrLast ? (
        <BurndownBlock
          workspaceSlug={workspaceSlug}
          projectKey={projectKey}
          sprint={activeOrLast}
        />
      ) : null}
    </div>
  )
}

function BurndownBlock({ workspaceSlug, projectKey, sprint }) {
  const q = useQuery({
    queryKey: ['burndown', workspaceSlug, projectKey, sprint.id],
    queryFn: () => fetchBurndown(workspaceSlug, projectKey, sprint.id),
  })
  return (
    <ChartShell
      title={`Burndown — ${sprint.name}`}
      description="Remaining points against the ideal line."
      loading={q.isLoading}
      error={q.isError}
      onRetry={() => q.refetch()}
      table={
        <table className="w-full text-left text-sm">
          <thead>
            <tr>
              <th>Date</th>
              <th>Remaining</th>
              <th>Ideal</th>
            </tr>
          </thead>
          <tbody>
            {(q.data?.series || []).map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{row.remaining}</td>
                <td>{row.ideal}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {(q.data?.series || []).length === 0 ? (
        <EmptyChart label="Start a sprint to generate burndown." />
      ) : (
        <Charts.BurndownChart data={q.data.series} />
      )}
    </ChartShell>
  )
}

function EmptyChart({ label }) {
  return (
    <div className="flex h-[220px] items-center justify-center text-sm text-[var(--text-muted)]">
      {label}
    </div>
  )
}
