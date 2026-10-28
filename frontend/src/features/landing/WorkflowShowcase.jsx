import { useEffect, useRef, useState } from 'react'
import { LayoutGroup, m, useReducedMotion } from 'motion/react'

const STEPS = [
  {
    id: 'plan',
    label: 'Plan',
    body: 'Break initiatives into cycles. Scope accurately with automated velocity prediction and team capacity thresholds.',
    panel: {
      id: 'NEX-104',
      status: 'In Progress',
      priority: 'P0 Urgent',
      title: 'Implement tenant schema partitioning',
      description:
        'Ensure PostgreSQL multi-tenancy migrations isolate organization schemas. Write strict isolation validation tests before advancing to Sprint 15.',
      meta: [
        ['ASSIGNEE', 'Elena Rostova'],
        ['ESTIMATE', '8 pts'],
        ['BRANCH', 'feat/rls'],
        ['CYCLE', 'Sprint 14'],
      ],
      subtasks: [
        { done: true, label: 'Draft schema migration plan' },
        { done: true, label: 'Add connection-pool tenant guards' },
        { done: true, label: 'Write isolation validation suite' },
        { done: false, label: 'Ship canary to staging tenants' },
      ],
    },
  },
  {
    id: 'build',
    label: 'Build',
    body: 'Branch-linked issue tracking. Statuses update automatically via native GitHub and GitLab webhooks as commits land.',
    panel: {
      id: 'NEX-105',
      status: 'In Review',
      priority: 'High',
      title: 'Wire webhook status sync for linked PRs',
      description:
        'Map commit and PR lifecycle events back to issue state. Keep board columns honest without manual status chores.',
      meta: [
        ['ASSIGNEE', 'Maya Kim'],
        ['ESTIMATE', '5 pts'],
        ['BRANCH', 'feat/hooks'],
        ['CYCLE', 'Sprint 14'],
      ],
      subtasks: [
        { done: true, label: 'Normalize GitHub event payloads' },
        { done: true, label: 'Map PR merged → Done' },
        { done: false, label: 'Add GitLab parity tests' },
        { done: false, label: 'Document webhook secrets rotation' },
      ],
    },
  },
  {
    id: 'ship',
    label: 'Ship',
    body: 'Zero-friction release tagging. Automatically compiled release notes, changelog updates, and compliance audit stamps.',
    panel: {
      id: 'NEX-110',
      status: 'Ready',
      priority: 'Medium',
      title: 'Compile Sprint 14 release notes',
      description:
        'Generate changelog from completed issues, attach SOC2 audit stamps, and tag the release with signed provenance.',
      meta: [
        ['ASSIGNEE', 'Alex Lee'],
        ['ESTIMATE', '3 pts'],
        ['BRANCH', 'release/14'],
        ['CYCLE', 'Sprint 14'],
      ],
      subtasks: [
        { done: true, label: 'Collect completed issue summaries' },
        { done: true, label: 'Draft customer-facing notes' },
        { done: true, label: 'Attach audit export' },
        { done: false, label: 'Publish tag + notify workspace' },
      ],
    },
  },
]

export function WorkflowShowcase() {
  const reduceMotion = useReducedMotion()
  const [active, setActive] = useState(0)
  const stepRefs = useRef([])

  useEffect(() => {
    if (reduceMotion) return undefined
    const nodes = stepRefs.current.filter(Boolean)
    if (!nodes.length) return undefined

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (!visible) return
        const idx = nodes.indexOf(visible.target)
        if (idx >= 0) setActive(idx)
      },
      { rootMargin: '-35% 0px -45% 0px', threshold: [0.25, 0.5, 0.75] },
    )

    nodes.forEach((n) => observer.observe(n))
    return () => observer.disconnect()
  }, [reduceMotion])

  const panel = STEPS[active].panel

  return (
    <section
      id="workflow"
      className="scroll-mt-24 px-10 py-32"
      aria-labelledby="workflow-heading"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col gap-16">
        <header className="flex flex-col gap-3">
          <span className="inline-flex w-fit rounded-full bg-[var(--accent-soft)] px-3 py-1 font-mono text-[13px] uppercase tracking-[0.05em] text-[var(--accent)]">
            Workflow
          </span>
          <h2
            id="workflow-heading"
            className="font-display text-[clamp(1.75rem,4vw,3rem)] leading-[1.125] tracking-[-0.025em] text-[var(--text)]"
          >
            How software gets shipped on Nexus.
          </h2>
        </header>

        <div className="grid gap-10 lg:grid-cols-[472px_1fr] lg:gap-12">
          <LayoutGroup>
            <ol className="flex flex-col gap-6">
              {STEPS.map((step, i) => {
                const selected = i === active
                return (
                  <li key={step.id} ref={(el) => { stepRefs.current[i] = el }}>
                    <button
                      type="button"
                      className="relative w-full rounded-xl px-6 py-6 text-left focus-ring"
                      onClick={() => setActive(i)}
                      aria-current={selected ? 'step' : undefined}
                    >
                      {selected ? (
                        <m.span
                          layoutId="workflow-indicator"
                          className="absolute inset-y-0 left-0 w-1 rounded-full bg-[var(--accent)]"
                          transition={{ type: 'spring', stiffness: 380, damping: 34 }}
                        />
                      ) : null}
                      <div className="flex items-baseline gap-2">
                        <span className="font-mono text-[13px] text-[var(--text-muted)]">
                          0{i + 1}
                        </span>
                        <h3
                          className={`font-display text-2xl tracking-[-0.015em] ${
                            selected
                              ? 'text-[var(--text)]'
                              : 'text-[var(--text-muted)]'
                          }`}
                        >
                          {step.label}
                        </h3>
                      </div>
                      <p className="mt-3 text-[15px] leading-[22px] text-[var(--text-muted)]">
                        {step.body}
                      </p>
                    </button>
                  </li>
                )
              })}
            </ol>
          </LayoutGroup>

          <m.div
            key={panel.id + active}
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.35 }}
            className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-8 shadow-[var(--inset-shine)]"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[12px] text-[var(--accent)]">
                {panel.id}
              </span>
              <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 font-mono text-[11px] text-[var(--accent)]">
                {panel.status}
              </span>
              <span className="rounded bg-[var(--surface-elevated)] px-2 py-0.5 font-mono text-[11px] text-[var(--text-muted)]">
                {panel.priority}
              </span>
            </div>
            <h3 className="mt-4 font-display text-2xl text-[var(--text)]">
              {panel.title}
            </h3>
            <p className="mt-3 text-[15px] leading-[22px] text-[var(--text-muted)]">
              {panel.description}
            </p>

            <dl className="mt-6 grid grid-cols-2 gap-4 rounded-xl bg-[var(--bg)] p-4 sm:grid-cols-4">
              {panel.meta.map(([label, value]) => (
                <div key={label}>
                  <dt className="font-mono text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                    {label}
                  </dt>
                  <dd className="mt-1 font-mono text-[12px] text-[var(--text)]">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>

            <p className="mt-6 font-mono text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
              Subtasks ({panel.subtasks.filter((s) => s.done).length} of{' '}
              {panel.subtasks.length} completed)
            </p>
            <ul className="mt-3 space-y-2">
              {panel.subtasks.map((s) => (
                <li
                  key={s.label}
                  className="flex items-center gap-2.5 text-[13px] text-[var(--text)]"
                >
                  <span
                    className={`flex size-3.5 items-center justify-center rounded-full border ${
                      s.done
                        ? 'border-[var(--accent-text)] bg-[var(--accent-soft)] text-[var(--accent-text)]'
                        : 'border-[var(--border-strong)]'
                    }`}
                    aria-hidden
                  >
                    {s.done ? '✓' : ''}
                  </span>
                  <span className={s.done ? 'text-[var(--text-muted)] line-through' : ''}>
                    {s.label}
                  </span>
                </li>
              ))}
            </ul>
          </m.div>
        </div>
      </div>
    </section>
  )
}
