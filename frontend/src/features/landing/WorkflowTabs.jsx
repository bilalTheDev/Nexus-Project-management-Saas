import { useState } from 'react'
import { CheckCircle2, Circle, GitPullRequest } from 'lucide-react'

const tabs = [
  {
    id: 'kanban',
    number: '01',
    title: 'Kanban Delivery Engine',
    summary:
      'Drag tasks across Backlog → Done with server-validated status and fractional ordering that survives refresh.',
  },
  {
    id: 'focus',
    number: '02',
    title: 'Personal Focus & My Tasks',
    summary:
      'See everything assigned to you across projects, filtered by due date and priority — without leaving the workspace.',
  },
  {
    id: 'velocity',
    number: '03',
    title: 'Audited Velocity Metrics',
    summary:
      'Dashboard aggregates and activity events stay workspace-scoped, so progress is honest and tenant-safe.',
  },
]

export function WorkflowTabs() {
  const [active, setActive] = useState('kanban')

  return (
    <section
      id="methodology"
      className="scroll-mt-20 border-b border-border bg-paper"
    >
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
        <div className="max-w-2xl">
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-brand">
            Workflow anatomy
          </p>
          <h2 className="mt-3 font-display text-3xl leading-tight tracking-tight text-ink sm:text-4xl">
            How work breathes inside Nexus.
          </h2>
        </div>

        <div className="mt-12 grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-14">
          <div className="flex flex-col gap-2" role="tablist" aria-label="Workflow">
            {tabs.map((tab) => {
              const selected = tab.id === active
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  id={`tab-${tab.id}`}
                  aria-controls={`panel-${tab.id}`}
                  onClick={() => setActive(tab.id)}
                  className={`rounded-xl border px-4 py-4 text-left transition-colors focus-ring ${
                    selected
                      ? 'border-brand/30 bg-mint'
                      : 'border-transparent hover:border-border hover:bg-surface'
                  }`}
                >
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-xs text-brand">
                      {tab.number}
                    </span>
                    <span className="font-display text-lg text-ink">
                      {tab.title}
                    </span>
                  </div>
                  <p className="mt-2 pl-8 text-sm leading-relaxed text-ink-secondary">
                    {tab.summary}
                  </p>
                </button>
              )
            })}
          </div>

          <div
            role="tabpanel"
            id={`panel-${active}`}
            aria-labelledby={`tab-${active}`}
            className="rounded-2xl border border-border bg-surface p-5 shadow-[0_20px_50px_-36px_rgba(32,42,53,0.35)] sm:p-6"
          >
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-muted">
                  NEX-104 · Website Redesign
                </p>
                <h3 className="mt-1 font-display text-xl text-ink">
                  Finalize navigation hierarchy & nested sub-routing
                </h3>
              </div>
              <span className="rounded-full bg-mint px-2.5 py-1 font-mono text-[10px] font-medium text-brand">
                In Progress
              </span>
            </div>

            <dl className="grid gap-3 sm:grid-cols-3">
              <Meta label="Status" value="In Progress" />
              <Meta label="Assignee" value="Maya Lin" />
              <Meta label="Priority" value="High" />
            </dl>

            <div className="mt-6">
              <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.16em] text-ink-muted">
                Sub-tasks
              </p>
              <ul className="space-y-2.5">
                <SubTask done label="Map authenticated route tree" />
                <SubTask done label="Define workspace slug guards" />
                <SubTask label="Wire task drawer deep links" />
                <SubTask label="Add keyboard focus rings" />
              </ul>
            </div>

            <div className="mt-6 flex items-start gap-3 rounded-xl border border-border bg-paper p-3">
              <GitPullRequest size={16} className="mt-0.5 shrink-0 text-brand" />
              <div>
                <p className="text-sm font-medium text-ink">
                  Linked PR · feature/nav-hierarchy
                </p>
                <p className="mt-0.5 font-mono text-xs text-ink-muted">
                  webhook: position sync · activity event emitted
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Meta({ label, value }) {
  return (
    <div className="rounded-lg border border-border bg-paper px-3 py-2.5">
      <dt className="font-mono text-[10px] uppercase tracking-wider text-ink-muted">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-ink">{value}</dd>
    </div>
  )
}

function SubTask({ label, done = false }) {
  return (
    <li className="flex items-center gap-2.5 text-sm text-ink">
      {done ? (
        <CheckCircle2 size={16} className="shrink-0 text-status-done" />
      ) : (
        <Circle size={16} className="shrink-0 text-ink-muted" />
      )}
      <span className={done ? 'text-ink-secondary line-through' : ''}>
        {label}
      </span>
    </li>
  )
}
