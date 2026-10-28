import { lazy, Suspense } from 'react'
import { LazyMotion, domAnimation, MotionConfig } from 'motion/react'
import { useTheme } from '@/hooks/useTheme'
import { LandingNav } from './LandingNav'
import { HeroSection } from './HeroSection'
import { LogoStrip } from './LogoStrip'

const BentoFeatures = lazy(() =>
  import('./BentoFeatures').then((m) => ({ default: m.BentoFeatures })),
)
const WorkflowShowcase = lazy(() =>
  import('./WorkflowShowcase').then((m) => ({ default: m.WorkflowShowcase })),
)
const NumbersSection = lazy(() =>
  import('./NumbersSection').then((m) => ({ default: m.NumbersSection })),
)
const TestimonialSection = lazy(() =>
  import('./TestimonialSection').then((m) => ({
    default: m.TestimonialSection,
  })),
)
const SecurityStrip = lazy(() =>
  import('./SecurityStrip').then((m) => ({ default: m.SecurityStrip })),
)
const FaqSection = lazy(() =>
  import('./FaqSection').then((m) => ({ default: m.FaqSection })),
)
const FinalCta = lazy(() =>
  import('./FinalCta').then((m) => ({ default: m.FinalCta })),
)
const LandingFooter = lazy(() =>
  import('./LandingFooter').then((m) => ({ default: m.LandingFooter })),
)

function SectionFallback() {
  return (
    <div className="mx-auto max-w-[1200px] px-10 py-24" aria-hidden>
      <div className="h-40 animate-pulse rounded-2xl bg-[var(--surface-1)]" />
    </div>
  )
}

export function LandingPage() {
  const { theme } = useTheme()

  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={domAnimation} strict>
        <div className="landing relative" data-theme={theme}>
          <div
            className="pointer-events-none absolute inset-0 landing-dot-grid"
            aria-hidden
          />
          <LandingNav />
          <main className="relative">
            <HeroSection />
            <LogoStrip />
            <Suspense fallback={<SectionFallback />}>
              <BentoFeatures />
              <WorkflowShowcase />
              <NumbersSection />
              <TestimonialSection />
              <SecurityStrip />
              <FaqSection />
              <FinalCta />
              <LandingFooter />
            </Suspense>
          </main>
        </div>
      </LazyMotion>
    </MotionConfig>
  )
}
