import { ArrowRight, Command } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { AppPreview } from './AppPreview'

export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,_rgba(229,241,236,0.9),_transparent_60%),linear-gradient(180deg,_#FAF9F5_0%,_#F5F4F0_100%)]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, rgba(32,42,53,0.06) 1px, transparent 0)',
          backgroundSize: '22px 22px',
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-14 sm:px-6 sm:pb-24 sm:pt-20">
        <div className="mx-auto max-w-3xl text-center">
          <p className="animate-fade-up font-mono text-[11px] font-medium uppercase tracking-[0.22em] text-brand">
            Nexus / Modern Project Management · v1.0 Spec Release
          </p>

          <h1 className="animate-fade-up-delay-1 mt-5 font-display text-[2.75rem] leading-[1.08] tracking-[-0.02em] text-ink sm:text-6xl md:text-[4.25rem]">
            Good work moves forward.
          </h1>

          <p className="animate-fade-up-delay-1 mt-5 font-display text-xl italic text-ink-secondary sm:text-2xl">
            Clear ownership. Fluid execution. Zero ambient panic.
          </p>

          <p className="animate-fade-up-delay-2 mx-auto mt-5 max-w-2xl text-base leading-relaxed text-ink-secondary sm:text-lg">
            Nexus gives small teams a calm place to plan projects, assign work,
            discuss tasks, and see what is progressing — without the ambient
            noise of bloated project tools.
          </p>

          <div className="animate-fade-up-delay-2 mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button to="/signup" className="min-w-[168px] px-5 py-3">
              Start Free Trial
              <ArrowRight size={16} />
            </Button>
            <Button
              to="/login?demo=true"
              variant="secondary"
              className="min-w-[168px] px-5 py-3"
            >
              Explore Live Demo
              <span className="inline-flex items-center gap-0.5 rounded border border-border bg-paper px-1.5 py-0.5 font-mono text-[10px] text-ink-muted">
                <Command size={10} />D
              </span>
            </Button>
          </div>

          <p className="animate-fade-up-delay-2 mt-5 font-mono text-[11px] tracking-wide text-ink-muted">
            No credit card required · Seeded demo workspace ready · PostgreSQL +
            Django architecture
          </p>
        </div>

        <div className="mt-14">
          <AppPreview />
        </div>
      </div>
    </section>
  )
}
