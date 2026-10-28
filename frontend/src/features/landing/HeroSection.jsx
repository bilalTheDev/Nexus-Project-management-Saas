import { useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  m,
  useScroll,
  useTransform,
  useReducedMotion,
} from 'motion/react'
import { HeroBoard } from './HeroBoard'

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.08 + i * 0.08, duration: 0.55, ease: [0.16, 1, 0.3, 1] },
  }),
}

export function HeroSection() {
  const reduceMotion = useReducedMotion()
  const boardRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: boardRef,
    offset: ['start end', 'center center'],
  })
  const rotateX = useTransform(
    scrollYProgress,
    [0, 1],
    reduceMotion ? [0, 0] : [8, 0],
  )
  const boardY = useTransform(
    scrollYProgress,
    [0, 1],
    reduceMotion ? [0, 0] : [48, 0],
  )

  return (
    <section
      id="product"
      className="relative overflow-hidden px-8 pb-28 pt-16"
      aria-labelledby="hero-heading"
    >
      <div
        className="pointer-events-none absolute left-1/2 top-[15%] h-[70%] w-[720px] -translate-x-1/2 rounded-full bg-[var(--glow-emerald-soft)] blur-[140px]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute left-[47%] top-20 h-[220px] w-1/4 rounded-full bg-[var(--glow-aqua-soft)] blur-[130px]"
        aria-hidden
      />

      <div className="relative mx-auto flex max-w-[1200px] flex-col items-center text-center">
        <m.div
          className="mb-8 inline-flex items-center gap-1 rounded-full bg-[var(--eyebrow-bg)] px-3.5 py-1 shadow-[var(--inset-shine)]"
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="show"
        >
          <span className="size-1.5 rounded-full bg-[var(--accent)]" aria-hidden />
          <span className="font-mono text-[13px] font-medium uppercase tracking-[0.05em] text-[var(--text-muted)]">
            Modern project management
          </span>
        </m.div>

        <m.h1
          id="hero-heading"
          className="max-w-[896px] font-display text-[clamp(2.5rem,6vw,4.5rem)] leading-none tracking-[-0.03em] text-[var(--text)]"
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="show"
        >
          Good work moves{' '}
          <em className="italic text-[var(--highlight)]">forward.</em>
        </m.h1>

        <m.p
          className="mt-6 max-w-[803px] text-[17px] leading-[1.625] tracking-[-0.005em] text-[var(--text-muted)]"
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="show"
        >
          Plan sprints, track issues, and ship releases in a workspace that
          stays out of your way.
          <br />
          Fast on the keyboard, strict about access.
        </m.p>

        <m.div
          className="mt-6 flex flex-col items-center gap-4 sm:flex-row"
          custom={3}
          variants={fadeUp}
          initial="hidden"
          animate="show"
        >
          <Link
            to="/signup"
            className="rounded-[10px] bg-[var(--accent)] px-6 py-3 text-base font-medium text-[var(--on-accent)] shadow-[var(--shadow-button)] focus-ring hover:bg-[var(--accent-hover)]"
          >
            Start free
          </Link>
          <Link
            to="/login?demo=true"
            className="inline-flex items-center gap-3 rounded-[10px] bg-[var(--surface-1)] px-6 py-3 text-base text-[var(--text)] shadow-[var(--inset-shine)] focus-ring hover:bg-[var(--surface-2)]"
          >
            Explore live demo
            <span className="rounded bg-[var(--surface-2)] px-2 py-0.5 font-mono text-[11px] text-[var(--text-muted)]">
              ⌘D
            </span>
          </Link>
        </m.div>

        <m.p
          className="mt-4 font-mono text-xs text-[var(--text-muted)]"
          custom={4}
          variants={fadeUp}
          initial="hidden"
          animate="show"
        >
          No credit card required · Seeded demo workspace
        </m.p>

        <m.div
          ref={boardRef}
          className="mt-16 w-full"
          style={{
            rotateX,
            y: boardY,
            transformPerspective: 1200,
            transformOrigin: 'center top',
          }}
        >
          <HeroBoard />
        </m.div>
      </div>
    </section>
  )
}
