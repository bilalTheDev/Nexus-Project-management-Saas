import { useEffect, useRef, useState } from 'react'
import { animate, m, useInView, useReducedMotion } from 'motion/react'

const METRICS = [
  {
    value: 100,
    suffix: 'ms',
    label: 'Keyboard response latency ceiling across all operations.',
  },
  {
    value: 5,
    suffix: '',
    label: 'Standardized workflow stages designed for extreme clarity.',
  },
  {
    value: 3,
    suffix: '',
    label: 'Strict tenant permission boundaries per workspace.',
  },
  {
    value: 0,
    suffix: '',
    label: 'Status update meetings required to understand release readiness.',
  },
]

function Metric({ value, suffix, label, index }) {
  const reduceMotion = useReducedMotion()
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-20% 0px' })
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (!inView || reduceMotion) return undefined
    const controls = animate(0, value, {
      duration: 1.1,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(Math.round(v)),
    })
    return () => controls.stop()
  }, [inView, reduceMotion, value])

  const shown = reduceMotion ? value : display

  return (
    <m.article
      ref={ref}
      className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6 shadow-[var(--inset-shine)]"
      initial={reduceMotion ? false : { opacity: 0, y: 16 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.04, duration: 0.4 }}
    >
      <p className="font-display tabular-nums text-[40px] leading-none tracking-tight text-[var(--accent-text)]">
        {shown}
        {suffix}
      </p>
      <p className="mt-3 text-[13px] leading-[18px] text-[var(--text-muted)]">
        {label}
      </p>
    </m.article>
  )
}

export function NumbersSection() {
  return (
    <section className="px-10 py-24" aria-label="Product metrics">
      <div className="mx-auto grid max-w-[1200px] gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map((metric, i) => (
          <Metric key={metric.label} {...metric} index={i} />
        ))}
      </div>
    </section>
  )
}
