import { Database, KeyRound, ScrollText } from 'lucide-react'
import { m, useReducedMotion } from 'motion/react'

const CARDS = [
  {
    icon: Database,
    title: 'Workspace isolation',
    body: 'Dedicated schema per customer. Tenant boundary guarantees verified at the database connection pool level.',
  },
  {
    icon: KeyRound,
    title: 'Role-based access',
    body: 'Granular RBAC down to field-level mutations. Scope project boards and customer data with cryptographically signed tokens.',
  },
  {
    icon: ScrollText,
    title: 'Audit log',
    body: 'Immutable append-only ledger for every access, state change, and exported report. Export via streaming webhook.',
  },
]

export function SecurityStrip() {
  const reduceMotion = useReducedMotion()

  return (
    <section
      id="security"
      className="scroll-mt-24 px-10 py-28"
      aria-labelledby="security-heading"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 text-center">
        <header className="flex flex-col items-center gap-3">
          <span className="inline-flex rounded-full bg-[var(--accent-soft)] px-3 py-1 font-mono text-[13px] uppercase tracking-[0.05em] text-[var(--accent)]">
            Architecture
          </span>
          <h2
            id="security-heading"
            className="max-w-3xl font-display text-[clamp(1.75rem,4vw,3rem)] leading-[1.125] tracking-[-0.025em] text-[var(--text)]"
          >
            Architected for data sovereignty.
          </h2>
        </header>

        <div className="grid w-full gap-6 md:grid-cols-3">
          {CARDS.map((card, i) => {
            const Icon = card.icon
            return (
              <m.article
                key={card.title}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-8 text-left shadow-[var(--inset-shine)]"
                initial={reduceMotion ? false : { opacity: 0, y: 16 }}
                whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04, duration: 0.4 }}
              >
                <span className="flex size-10 items-center justify-center rounded-lg bg-[var(--surface-2)] text-[var(--accent)]">
                  <Icon size={18} aria-hidden />
                </span>
                <h3 className="mt-5 font-display text-2xl tracking-[-0.015em] text-[var(--text)]">
                  {card.title}
                </h3>
                <p className="mt-3 text-[15px] leading-[22px] text-[var(--text-muted)]">
                  {card.body}
                </p>
              </m.article>
            )
          })}
        </div>

        <p className="font-mono text-xs text-[var(--text-muted)]">
          SOC 2 Type II controls · Encryption at rest · Regional data residency
        </p>
      </div>
    </section>
  )
}
