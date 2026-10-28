import { m, useReducedMotion } from 'motion/react'

export function TestimonialSection() {
  const reduceMotion = useReducedMotion()

  return (
    <section
      className="px-10 py-28"
      aria-labelledby="testimonial-heading"
    >
      <h2 id="testimonial-heading" className="sr-only">
        Customer testimonial
      </h2>
      <m.figure
        className="relative mx-auto max-w-[1000px] overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] px-8 py-14 shadow-[var(--inset-shine)] sm:px-14"
        initial={reduceMotion ? false : { opacity: 0, y: 20 }}
        whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-10%' }}
        transition={{ duration: 0.5 }}
      >
        <span
          className="pointer-events-none absolute -top-4 right-10 font-display text-[240px] leading-none text-[var(--highlight-soft)]"
          aria-hidden
        >
          “
        </span>
        <blockquote className="relative font-display text-[clamp(1.35rem,2.5vw,2rem)] leading-[1.35] tracking-[-0.02em] text-[var(--text)]">
          “We replaced our Jira setup of four years in a single weekend. Nexus
          gives us the exact same issue hygiene, but everything opens
          instantly.”
        </blockquote>
        <figcaption className="relative mt-10 flex items-center gap-4">
          <span
            className="flex size-12 items-center justify-center rounded-full bg-[var(--surface-3)] font-mono text-sm font-semibold text-[var(--accent-text)]"
            aria-hidden
          >
            ER
          </span>
          <div>
            <p className="font-display text-lg text-[var(--text)]">
              Elena Rostova
            </p>
            <p className="text-[15px] text-[var(--text-muted)]">
              CTO, Kinetix Platforms
            </p>
          </div>
        </figcaption>
      </m.figure>
    </section>
  )
}
