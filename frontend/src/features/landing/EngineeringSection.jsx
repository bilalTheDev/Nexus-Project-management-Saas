import { Database, Lock, Server } from 'lucide-react'

const points = [
  {
    icon: Server,
    title: 'Instant-sync infrastructure',
    body: 'TanStack Query caching with deliberate invalidation keeps boards responsive under demo load.',
  },
  {
    icon: Database,
    title: 'Robust JSON framework core',
    body: 'Django REST Framework APIs with consistent pagination, filters, and OpenAPI via Spectacular.',
  },
  {
    icon: Lock,
    title: 'Military-grade data security',
    body: 'Workspace membership checks on every protected endpoint — tenant isolation is not optional.',
  },
]

const sampleJson = `{
  "count": 2,
  "results": [
    {
      "event_type": "task.status_changed",
      "actor": "maya.lin",
      "task": "NEX-104",
      "metadata": {
        "from": "TODO",
        "to": "IN_PROGRESS"
      }
    },
    {
      "event_type": "task.position_updated",
      "actor": "daniel.vance",
      "task": "NEX-104",
      "metadata": { "position": 0.5 }
    }
  ]
}`

export function EngineeringSection() {
  return (
    <section
      id="engineering"
      className="scroll-mt-20 border-b border-border bg-surface"
    >
      <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 sm:py-24 lg:grid-cols-2 lg:items-center lg:gap-16">
        <div>
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-brand">
            Architecture
          </p>
          <h2 className="mt-3 font-display text-3xl leading-tight tracking-tight text-ink sm:text-4xl">
            Engineered without architectural compromises.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-ink-secondary">
            A modular Django monolith, React SPA, and PostgreSQL data model —
            deployed as a portfolio-grade stack on Vercel, PythonAnywhere, and
            Neon.
          </p>

          <ul className="mt-8 space-y-5">
            {points.map((point) => (
              <li key={point.title} className="flex gap-3">
                <span className="mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-lg border border-border bg-paper text-brand">
                  <point.icon size={16} strokeWidth={1.75} />
                </span>
                <div>
                  <p className="font-medium text-ink">{point.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                    {point.body}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="overflow-hidden rounded-2xl border border-[#2a3542] bg-ink shadow-[0_24px_60px_-30px_rgba(32,42,53,0.55)]">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="size-2.5 rounded-full bg-[#E07A5F]" />
              <span className="size-2.5 rounded-full bg-[#F2CC8F]" />
              <span className="size-2.5 rounded-full bg-[#81B29A]" />
            </div>
            <p className="font-mono text-[10px] text-white/50">
              GET /api/v1/workspaces/ws_northstar/activity/
            </p>
          </div>
          <pre className="overflow-x-auto p-4 font-mono text-[11px] leading-relaxed text-[#C8D4C4] sm:text-xs">
            <code>{sampleJson}</code>
          </pre>
          <div className="border-t border-white/10 px-4 py-3 font-mono text-[10px] text-white/45">
            POST /api/v1/tasks/NEX-104/position/ · {'{ status, position }'}
          </div>
        </div>
      </div>
    </section>
  )
}
