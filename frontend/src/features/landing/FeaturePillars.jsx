import { Keyboard, ShieldCheck, Sparkles } from 'lucide-react'

const pillars = [
  {
    icon: Sparkles,
    title: 'Clarity Over Chaos',
    body: 'Cryptographic audit logging, milestone pacing, and status that updates itself — so your team spends less time in status meetings and more time shipping.',
  },
  {
    icon: Keyboard,
    title: 'High-Density Fluidity',
    body: 'Optimized for 1440px desktops with a persistent drawer hierarchy and keyboard ergonomics (j / k / l) that keep your hands on the board.',
  },
  {
    icon: ShieldCheck,
    title: 'Sovereign Workspaces',
    body: 'PostgreSQL-backed tenant isolation, unique project keys per workspace, and deliberate authorization on every API request — not just hidden buttons.',
  },
]

export function FeaturePillars() {
  return (
    <section
      id="product"
      className="scroll-mt-20 border-b border-border bg-surface"
    >
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
        <div className="max-w-2xl">
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-brand">
            Designed for product
          </p>
          <h2 className="mt-3 font-display text-3xl leading-tight tracking-tight text-ink sm:text-4xl md:text-[2.75rem]">
            Every pixel engineered for zero cognitive friction.
          </h2>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-ink-secondary">
            A calm interface that keeps ownership obvious, progress visible, and
            noise out of the way — so teams can move work forward with intent.
          </p>
        </div>

        <div className="mt-14 grid gap-8 md:grid-cols-3 md:gap-10">
          {pillars.map((pillar) => (
            <article key={pillar.title} className="group">
              <div className="mb-5 inline-flex size-11 items-center justify-center rounded-xl border border-border bg-paper text-brand transition-colors group-hover:border-brand/30 group-hover:bg-mint">
                <pillar.icon size={20} strokeWidth={1.75} />
              </div>
              <h3 className="font-display text-xl text-ink">{pillar.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-secondary">
                {pillar.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
