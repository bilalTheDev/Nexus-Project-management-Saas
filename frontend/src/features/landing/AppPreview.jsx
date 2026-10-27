import { Search } from 'lucide-react'

const columns = [
  {
    title: 'Backlog',
    count: 4,
    color: 'bg-status-backlog',
    cards: [
      {
        id: 'NEX-98',
        title: 'Audit tenant membership guards',
        tags: ['Security'],
        priority: 'Med',
      },
      {
        id: 'NEX-101',
        title: 'Seed Northstar demo workspace',
        tags: ['Ops'],
        priority: 'Low',
      },
    ],
  },
  {
    title: 'In Progress',
    count: 3,
    color: 'bg-status-progress',
    cards: [
      {
        id: 'NEX-104',
        title: 'Finalize navigation hierarchy',
        tags: ['Design', 'Frontend'],
        priority: 'High',
        active: true,
      },
      {
        id: 'NEX-110',
        title: 'Wire Kanban position API',
        tags: ['API'],
        priority: 'High',
      },
    ],
  },
  {
    title: 'Done',
    count: 6,
    color: 'bg-status-done',
    cards: [
      {
        id: 'NEX-88',
        title: 'Auth cookie + CORS strategy',
        tags: ['Auth'],
        priority: 'High',
      },
      {
        id: 'NEX-91',
        title: 'Workspace slug uniqueness',
        tags: ['Backend'],
        priority: 'Med',
      },
    ],
  },
]

function Annotation({ label, className = '', style }) {
  return (
    <div
      className={`items-center gap-2 rounded-full border border-border bg-surface/95 px-3 py-1.5 text-xs font-medium text-ink shadow-sm backdrop-blur ${className}`}
      style={style}
    >
      <span className="relative flex size-2">
        <span className="absolute inset-0 animate-pulse-soft rounded-full bg-brand/40" />
        <span className="relative size-2 rounded-full bg-brand" />
      </span>
      {label}
    </div>
  )
}

export function AppPreview() {
  return (
    <div className="relative mx-auto w-full max-w-5xl animate-fade-up-delay-3">
      <div
        className="pointer-events-none absolute -inset-x-8 -top-10 -bottom-6 rounded-[2rem] bg-[radial-gradient(ellipse_at_top,_rgba(52,125,120,0.12),_transparent_55%)]"
        aria-hidden="true"
      />

      <div className="relative overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_30px_80px_-40px_rgba(32,42,53,0.45)]">
        <div className="flex items-center gap-2 border-b border-border bg-surface-low px-4 py-3">
          <span className="size-2.5 rounded-full bg-[#E07A5F]" />
          <span className="size-2.5 rounded-full bg-[#F2CC8F]" />
          <span className="size-2.5 rounded-full bg-[#81B29A]" />
          <div className="ml-3 flex flex-1 items-center gap-2 rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-ink-muted">
            <Search size={12} />
            <span className="font-mono">
              app.nexus.dev / northstar-studio / NEX-WEB
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[180px_1fr] md:grid-cols-[200px_1fr]">
          <aside className="hidden border-r border-border bg-paper p-4 sm:block">
            <p className="mb-4 font-mono text-[10px] uppercase tracking-[0.18em] text-brand">
              Northstar Studio
            </p>
            <ul className="space-y-1 text-sm">
              {['Overview', 'My Tasks', 'Projects', 'Activity', 'Members'].map(
                (item, i) => (
                  <li
                    key={item}
                    className={`rounded-md px-2.5 py-1.5 ${
                      i === 2
                        ? 'bg-mint font-medium text-ink'
                        : 'text-ink-secondary'
                    }`}
                  >
                    {item}
                  </li>
                ),
              )}
            </ul>
            <div className="mt-6 border-t border-border pt-4">
              <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-ink-muted">
                Pinned
              </p>
              <div className="space-y-2 text-xs text-ink-secondary">
                <p className="flex items-center gap-2">
                  <span className="size-1.5 rounded-full bg-status-progress" />
                  NEX-WEB
                </p>
                <p className="flex items-center gap-2">
                  <span className="size-1.5 rounded-full bg-status-review" />
                  NEX-API
                </p>
              </div>
            </div>
          </aside>

          <div className="bg-surface p-3 sm:p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-muted">
                  Cycle 34 · 4 days remaining
                </p>
                <h3 className="font-display text-lg text-ink">
                  Website Redesign
                </h3>
              </div>
              <span className="rounded-full bg-mint px-2.5 py-1 font-mono text-[10px] font-medium text-brand">
                Board view
              </span>
            </div>

            <div className="flex gap-3 overflow-x-auto pb-1">
              {columns.map((column) => (
                <div
                  key={column.title}
                  className="min-w-[200px] flex-1 rounded-xl border border-border bg-surface-low/70 p-2.5"
                >
                  <div className="mb-2.5 flex items-center gap-2 px-1">
                    <span className={`size-2 rounded-full ${column.color}`} />
                    <span className="text-xs font-semibold text-ink">
                      {column.title}
                    </span>
                    <span className="font-mono text-[10px] text-ink-muted">
                      {column.count}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {column.cards.map((card) => (
                      <article
                        key={card.id}
                        className={`rounded-lg border bg-surface p-3 shadow-sm ${
                          card.active
                            ? 'border-brand ring-1 ring-brand/20'
                            : 'border-border'
                        }`}
                      >
                        <div className="mb-1.5 flex items-center justify-between gap-2">
                          <span className="font-mono text-[10px] text-ink-muted">
                            {card.id}
                          </span>
                          <span className="rounded bg-paper px-1.5 py-0.5 font-mono text-[9px] text-ink-secondary">
                            {card.priority}
                          </span>
                        </div>
                        <p className="text-xs font-medium leading-snug text-ink">
                          {card.title}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {card.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-full bg-paper px-1.5 py-0.5 text-[9px] text-ink-secondary"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Annotation
        className="absolute -left-2 top-24 hidden animate-float lg:flex"
        label="Real-time tenant isolation"
      />
      <Annotation
        className="absolute -right-2 top-40 hidden animate-float lg:flex"
        style={{ animationDelay: '0.8s' }}
        label="Sub-100ms keyboard navigation"
      />
      <Annotation
        className="absolute bottom-8 left-1/2 hidden -translate-x-1/2 animate-float lg:flex"
        style={{ animationDelay: '1.4s' }}
        label="Audited activity trail"
      />
    </div>
  )
}
