import { useEffect, useState } from 'react'
import { LayoutGroup, m, useReducedMotion } from 'motion/react'

const COLUMNS = [
  {
    id: 'todo',
    label: 'To Do',
    count: 5,
    dot: 'var(--glow-aqua)',
    cards: [
      {
        id: 'NEX-112',
        title: 'Add Cmd+K quick filter for stale PRs',
        priority: 'Medium',
        priorityTone: 'aqua',
        tags: ['Core'],
        progress: null,
        avatar: { initials: 'MK', tone: 'aqua' },
      },
    ],
  },
  {
    id: 'progress',
    label: 'In Progress',
    count: 3,
    dot: 'var(--accent)',
    cards: [
      {
        id: 'NEX-105',
        title: 'Refactor permission cache invalidation',
        priority: 'High',
        priorityTone: 'muted',
        tags: ['Auth'],
        progress: '2/5',
        avatar: { initials: 'AL', tone: 'chip' },
      },
    ],
  },
  {
    id: 'review',
    label: 'In Review',
    count: 2,
    dot: 'var(--glow-emerald)',
    cards: [
      {
        id: 'NEX-109',
        title: 'Sync engine differential hashing & conflict resolver',
        priority: 'High',
        priorityTone: 'muted',
        tags: ['Backend'],
        progress: '4/4',
        avatar: { initials: 'MK', tone: 'aqua' },
      },
    ],
  },
  {
    id: 'done',
    label: 'Done',
    count: 8,
    dot: 'var(--accent-text)',
    cards: [
      {
        id: 'NEX-098',
        title: 'Ship invite link expiry + audit webhook',
        priority: 'Done',
        priorityTone: 'mint',
        tags: ['Growth'],
        progress: '3/3',
        avatar: { initials: 'ER', tone: 'accent' },
      },
    ],
  },
]

const FEATURED = {
  id: 'NEX-104',
  title: 'Implement Postgres row-level security for tenant isolation',
  priority: 'P0 Urgent',
  priorityTone: 'urgent',
  tags: ['Security', 'DB'],
  progress: '3/4',
  avatar: { initials: 'ER', tone: 'accent' },
  featured: true,
}

const LOOP = ['todo', 'progress', 'review', 'done']

function PriorityPill({ tone, children }) {
  const styles = {
    urgent:
      'bg-[var(--accent-soft-strong)] text-[var(--accent-text)] gap-1 inline-flex items-center',
    aqua: 'bg-[var(--glow-aqua-soft)] text-[var(--glow-aqua)]',
    mint: 'bg-[var(--accent-soft)] text-[var(--accent-text)]',
    muted: 'bg-[var(--surface-elevated)] text-[var(--text-muted)]',
  }
  return (
    <span
      className={`rounded px-1.5 py-0.5 font-mono text-[10px] leading-[15px] ${styles[tone] ?? styles.muted}`}
    >
      {tone === 'urgent' ? (
        <span className="size-1.5 rounded-full bg-[var(--accent)]" aria-hidden />
      ) : null}
      {children}
    </span>
  )
}

function Avatar({ initials, tone }) {
  const bg = {
    accent: 'bg-[var(--accent)] text-[var(--on-accent)]',
    aqua: 'bg-[var(--surface-3)] text-[var(--accent-text)]',
    chip: 'bg-[var(--surface-elevated)] text-[var(--text)]',
  }
  return (
    <span
      className={`flex size-5 items-center justify-center rounded-full font-mono text-[9px] font-semibold ${bg[tone] ?? bg.chip}`}
    >
      {initials}
    </span>
  )
}

function BoardCard({ card }) {
  return (
    <m.article
      layout
      layoutId={card.id}
      className={`rounded-xl p-3.5 shadow-[var(--inset-shine)] ${
        card.featured
          ? 'bg-[var(--surface-active)] shadow-[inset_0_1px_0_var(--accent-soft-strong)]'
          : 'bg-[var(--surface-2)]'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={`font-mono text-[11px] leading-[16.5px] ${
            card.featured
              ? 'font-semibold text-[var(--accent-text)]'
              : 'text-[var(--text-muted)]'
          }`}
        >
          {card.id}
        </span>
        <PriorityPill tone={card.priorityTone}>{card.priority}</PriorityPill>
      </div>
      <p
        className={`mt-2 text-[13px] leading-[16.25px] text-[var(--text)] ${
          card.featured ? 'font-semibold' : 'font-medium'
        }`}
      >
        {card.title}
      </p>
      <div className="mt-2 flex items-center justify-between gap-2 pt-2">
        <div className="flex flex-wrap gap-1">
          {card.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-[var(--surface-1)] px-2 py-0.5 font-mono text-[10px] leading-[15px] text-[var(--text-muted)]"
            >
              {tag}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-1.5">
          {card.progress ? (
            <span
              className={`font-mono text-[10px] leading-[15px] ${
                card.featured
                  ? 'text-[var(--accent-text)]'
                  : 'text-[var(--text-muted)]'
              }`}
            >
              {card.progress}
            </span>
          ) : null}
          {card.avatar ? <Avatar {...card.avatar} /> : null}
        </div>
      </div>
    </m.article>
  )
}

export function HeroBoard() {
  const reduceMotion = useReducedMotion()
  const [featuredCol, setFeaturedCol] = useState('progress')
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    if (reduceMotion || paused) return undefined
    const id = window.setInterval(() => {
      setFeaturedCol((prev) => {
        const i = LOOP.indexOf(prev)
        return LOOP[(i + 1) % LOOP.length]
      })
    }, 3200)
    return () => window.clearInterval(id)
  }, [reduceMotion, paused])

  return (
    <div
      className="relative w-full max-w-[1200px]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div
        className="pointer-events-none absolute -inset-4 rounded-[28px] bg-gradient-to-b from-[var(--glow-emerald-soft)] via-[var(--glow-aqua-soft)] to-transparent opacity-75 blur-[40px]"
        aria-hidden
      />

      <div className="relative overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-[var(--shadow-board)]">
        <div className="flex h-11 items-center gap-4 bg-[var(--surface-2)] px-4">
          <div className="flex items-center gap-2" aria-hidden>
            <span className="size-3 rounded-full bg-[var(--traffic-red)]" />
            <span className="size-3 rounded-full bg-[var(--traffic-yellow)]" />
            <span className="size-3 rounded-full bg-[var(--traffic-green)]" />
          </div>
          <div className="mx-auto flex max-w-sm flex-1 items-center justify-center gap-2 rounded bg-[var(--bg)] px-3 py-1">
            <span className="font-mono text-[11px] text-[var(--text-muted)]">
              app.nexus.so/workspace/sprint-14
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] px-6 py-3">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <h2 className="text-[19px] font-semibold tracking-[-0.01em] text-[var(--text)]">
                Sprint 14 · Core Runtime
              </h2>
              <span className="rounded-full bg-[var(--surface-2)] px-2 py-0.5 font-mono text-[11px] text-[var(--accent-text)]">
                Cycle Active
              </span>
            </div>
            <span className="hidden h-4 w-px bg-[var(--surface-elevated)] sm:block" />
            <span className="font-mono text-xs text-[var(--text-muted)]">
              Oct 14 – Oct 28
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex -space-x-1.5">
              <Avatar initials="ER" tone="aqua" />
              <Avatar initials="MK" tone="chip" />
              <Avatar initials="AL" tone="accent" />
            </div>
            <button
              type="button"
              className="rounded bg-[var(--surface-2)] px-2.5 py-1 font-mono text-[11px] text-[var(--text)] focus-ring"
            >
              Filter
            </button>
          </div>
        </div>

        <LayoutGroup>
          <div className="grid min-w-0 grid-cols-2 gap-4 overflow-x-auto p-6 md:grid-cols-4">
            {COLUMNS.map((col) => (
              <div key={col.id} className="flex min-w-0 flex-col gap-3">
                <div className="flex items-center justify-between pb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="size-2 rounded-full"
                      style={{ background: col.dot }}
                      aria-hidden
                    />
                    <span className="text-[13px] font-medium text-[var(--text)]">
                      {col.label}
                    </span>
                  </div>
                  <span
                    className={`rounded px-1.5 py-0.5 font-mono text-[11px] ${
                      col.id === 'progress'
                        ? 'bg-[var(--accent-soft)] font-medium text-[var(--accent-text)]'
                        : 'bg-[var(--surface-2)] text-[var(--text-muted)]'
                    }`}
                  >
                    {col.count}
                  </span>
                </div>
                <div className="flex flex-col gap-3">
                  {featuredCol === col.id ? (
                    <BoardCard card={FEATURED} />
                  ) : null}
                  {col.cards.map((card) => (
                    <BoardCard key={card.id} card={card} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </LayoutGroup>

        <div className="pointer-events-none absolute bottom-6 left-6 hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)]/95 px-3 py-2 shadow-[var(--shadow-button)] sm:block">
          <p className="text-[12px] font-medium text-[var(--text)]">
            Command palette
          </p>
          <p className="font-mono text-[10px] text-[var(--text-muted)]">
            Instant keyboard access ⌘K
          </p>
        </div>
        <div className="pointer-events-none absolute bottom-6 right-6 hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)]/95 px-3 py-2 shadow-[var(--shadow-button)] md:block">
          <p className="text-[12px] font-medium text-[var(--text)]">
            Audited activity trail
          </p>
          <p className="font-mono text-[10px] text-[var(--accent-text)]">
            p99 &lt; 4ms latency
          </p>
        </div>
      </div>
    </div>
  )
}
