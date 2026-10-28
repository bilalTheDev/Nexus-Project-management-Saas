import { useEffect, useRef, useState } from 'react'
import { m, useReducedMotion } from 'motion/react'
import keyboardIcon from '@/assets/landing/bento-keyboard.svg'

function useFinePointer() {
  const [fine, setFine] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(hover: hover) and (pointer: fine)')
    const sync = () => setFine(mq.matches)
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])
  return fine
}

function useSpotlight(enabled) {
  const ref = useRef(null)
  const onPointerMove = (e) => {
    if (!enabled || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    ref.current.style.setProperty('--spot-x', `${e.clientX - rect.left}px`)
    ref.current.style.setProperty('--spot-y', `${e.clientY - rect.top}px`)
  }
  return { ref, onPointerMove }
}

function Tile({ className, children, index }) {
  const reduceMotion = useReducedMotion()
  const finePointer = useFinePointer()
  const canSpotlight = !reduceMotion && finePointer
  const { ref, onPointerMove } = useSpotlight(canSpotlight)

  return (
    <m.article
      ref={ref}
      onPointerMove={onPointerMove}
      data-spotlight={canSpotlight ? 'on' : 'off'}
      className={`landing-bento-tile relative overflow-hidden rounded-2xl border border-[var(--border)] p-8 ${className}`}
      initial={reduceMotion ? false : { opacity: 0, y: 20 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.45, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
      whileHover={reduceMotion ? undefined : { y: -4 }}
    >
      {children}
    </m.article>
  )
}

function TileLabel({ children, trailing }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="font-mono text-[13px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
        {children}
      </span>
      {trailing}
    </div>
  )
}

export function BentoFeatures() {
  return (
    <section
      id="capabilities"
      className="relative px-10 py-32"
      aria-labelledby="bento-heading"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col gap-16">
        <header className="flex max-w-xl flex-col gap-3">
          <span className="inline-flex w-fit rounded-full bg-[var(--accent-soft)] px-3 py-1 font-mono text-[13px] uppercase tracking-[0.05em] text-[var(--accent)]">
            Capabilities
          </span>
          <h2
            id="bento-heading"
            className="font-display text-[clamp(1.75rem,4vw,3rem)] leading-[1.125] tracking-[-0.025em] text-[var(--text)]"
          >
            Precision engineering for high-velocity software squads.
          </h2>
          <p className="max-w-xl text-[17px] leading-[27px] tracking-[-0.005em] text-[var(--text-muted)]">
            Every component tuned for 60fps keyboard interaction, rigorous data
            segregation, and zero configuration friction.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
          {/* Board Engine — span 8 */}
          <Tile className="md:col-span-8" index={0}>
            <TileLabel
              trailing={
                <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 font-mono text-[11px] text-[var(--accent-text)]">
                  60 FPS DOM SYNC
                </span>
              }
            >
              Board engine
            </TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Kanban that keeps up
            </h3>
            <p className="mt-2 max-w-md text-[15px] leading-[22px] text-[var(--text-muted)]">
              Instant optimistic mutations. Reorder, reprioritize, and tag
              across thousands of open backlog cards without layout thrashing.
            </p>
            <div className="mt-6 flex gap-3 overflow-hidden rounded-xl bg-[var(--bg)] p-4">
              <div className="flex flex-1 flex-col gap-2 rounded-lg bg-[var(--surface-2)] p-2.5">
                <span className="font-mono text-[10px] uppercase text-[var(--text-muted)]">
                  Sprint stage
                </span>
                <span className="h-2 w-[70%] rounded bg-[var(--surface-elevated)]" />
                <span className="h-2 w-[50%] rounded bg-[var(--surface-elevated)]" />
              </div>
              <div className="flex flex-1 flex-col gap-2 rounded-lg bg-[var(--surface-active)] p-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase text-[var(--accent)]">
                    Moving NEX-104
                  </span>
                  <span className="size-1.5 rounded-full bg-[var(--accent)]" />
                </div>
                <span className="h-2 w-[80%] rounded bg-[var(--accent-glow)]" />
                <span className="h-2 w-[65%] rounded bg-[var(--surface-elevated)]" />
              </div>
              <div className="flex flex-1 flex-col gap-2 rounded-lg bg-[var(--surface-2)] p-2.5">
                <span className="font-mono text-[10px] uppercase text-[var(--text-muted)]">
                  Done
                </span>
                <span className="h-2 w-full rounded bg-[var(--accent-glow)]" />
              </div>
            </div>
          </Tile>

          {/* Keyboard */}
          <Tile className="md:col-span-4" index={1}>
            <TileLabel
              trailing={
                <img src={keyboardIcon} alt="" width={17} height={12} />
              }
            >
              Keyboard-first
            </TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Command everything
            </h3>
            <p className="mt-2 text-[15px] leading-[22px] text-[var(--text-muted)]">
              Navigate your entire workspace without ever lifting your hands
              from home row.
            </p>
            <div className="mt-6 flex flex-col gap-2 rounded-xl bg-[var(--bg)] p-3.5 font-mono">
              <div className="flex items-center justify-between border-b border-transparent pb-2">
                <span className="flex gap-1.5 text-xs">
                  <span className="text-[var(--accent)]">&gt;</span>
                  <span className="text-[var(--text)]">assign to Elena</span>
                </span>
                <kbd className="rounded bg-[var(--surface-chip)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">
                  ↵
                </kbd>
              </div>
              <div className="flex items-center justify-between text-[11px] text-[var(--text-faint-soft)]">
                <span>change status → In Review</span>
                <kbd className="rounded bg-[var(--surface-chip)] px-1.5 py-0.5 text-[10px]">
                  S
                </kbd>
              </div>
              <div className="flex items-center justify-between text-[11px] text-[var(--text-faint-soft)]">
                <span>create branch NEX-104</span>
                <kbd className="rounded bg-[var(--surface-chip)] px-1.5 py-0.5 text-[10px]">
                  B
                </kbd>
              </div>
            </div>
          </Tile>

          {/* Cycle */}
          <Tile className="md:col-span-4" index={2}>
            <TileLabel>Cycle planning</TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Backlog and sprints
            </h3>
            <p className="mt-2 text-[15px] leading-[22px] text-[var(--text-muted)]">
              Clean sprint horizons that keep debt low and momentum transparent.
            </p>
            <div className="mt-6 flex flex-col gap-3 rounded-xl bg-[var(--bg)] p-4">
              <div className="flex items-center justify-between font-mono text-xs">
                <span className="text-[var(--text)]">Sprint 14 Velocity</span>
                <span className="font-semibold text-[var(--accent)]">68%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[var(--surface-elevated)]">
                <div className="h-full w-[68%] rounded-full bg-[var(--accent)]" />
              </div>
              <p className="font-mono text-[11px] text-[var(--text-muted)]">
                34 of 50 story points resolved
              </p>
            </div>
          </Tile>

          {/* Isolation */}
          <Tile className="md:col-span-4" index={3}>
            <TileLabel>Data isolation</TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Tenant isolation
            </h3>
            <p className="mt-2 text-[15px] leading-[22px] text-[var(--text-muted)]">
              Granular schema partitioning with zero row bleed between
              organizations.
            </p>
            <div className="mt-6 flex flex-col gap-2 rounded-xl bg-[var(--bg)] p-3.5 font-mono text-[11px]">
              <div className="flex justify-between py-1">
                <span className="text-[var(--text)]">Owner</span>
                <span className="text-[var(--accent-text)]">Full Schema / Admin</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[var(--text)]">Member</span>
                <span className="text-[var(--text-muted)]">Mutate Issue / Run</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[var(--text)]">Guest</span>
                <span className="text-[var(--text-muted)]">Read-only Stream</span>
              </div>
            </div>
          </Tile>

          {/* Audit */}
          <Tile className="md:col-span-4" index={4}>
            <TileLabel>Audit trail</TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Immutable records
            </h3>
            <p className="mt-2 text-[15px] leading-[22px] text-[var(--text-muted)]">
              Append-only cryptographic event trail for enterprise compliance
              &amp; SOC2.
            </p>
            <div className="mt-6 flex flex-col gap-2 rounded-xl bg-[var(--bg)] p-3.5 font-mono text-[10px]">
              {[
                ['NEX-104 → Done', '12s ago'],
                ['token_svc rotated', '4m ago'],
                ['RBAC matrix v2 locked', '1h ago'],
              ].map(([event, when]) => (
                <div key={event} className="flex justify-between gap-2">
                  <span
                    className={
                      event.startsWith('NEX')
                        ? 'text-[var(--text)]'
                        : 'text-[var(--text-muted)]'
                    }
                  >
                    {event}
                  </span>
                  <span className="text-[var(--text-muted)]">{when}</span>
                </div>
              ))}
            </div>
          </Tile>

          {/* Velocity — span 8 */}
          <Tile className="md:col-span-8" index={5}>
            <TileLabel
              trailing={
                <span className="font-mono text-[11px] text-[var(--accent)]">
                  BURNDOWN TRACKING
                </span>
              }
            >
              Real-time velocity
            </TileLabel>
            <h3 className="mt-6 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
              Reports that explain
            </h3>
            <p className="mt-2 max-w-lg text-[15px] leading-[22px] text-[var(--text-muted)]">
              No vanity metrics. Understand team throughput, PR review
              turnarounds, and release blockers with crystal precision.
            </p>
            <div className="mt-6 rounded-xl bg-[var(--bg)] p-4">
              <div className="mb-2 flex justify-between font-mono text-xs">
                <span className="text-[var(--text-muted)]">Ideal Line (38 pts)</span>
                <span className="font-semibold text-[var(--accent)]">
                  Actual Velocity: -12% delta
                </span>
              </div>
              <svg
                viewBox="0 0 640 96"
                className="h-24 w-full"
                role="img"
                aria-label="Burndown chart"
              >
                <line
                  x1="40"
                  y1="12"
                  x2="600"
                  y2="84"
                  stroke="var(--text-muted)"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                  opacity="0.5"
                />
                <path
                  d="M40 16 C 160 22, 240 28, 320 48 S 520 78, 560 80"
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
                <circle cx="560" cy="80" r="4" fill="var(--accent)" />
              </svg>
              <div className="mt-2 flex justify-between font-mono text-[10px] text-[var(--text-muted)]">
                <span>Day 1</span>
                <span>Day 5</span>
                <span>Day 10</span>
                <span>Day 14 (Release)</span>
              </div>
            </div>
          </Tile>
        </div>
      </div>
    </section>
  )
}
