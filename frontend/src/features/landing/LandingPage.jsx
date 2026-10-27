import { MarketingNav } from './MarketingNav'
import { HeroSection } from './HeroSection'
import { LogoCloud } from './LogoCloud'
import { FeaturePillars } from './FeaturePillars'
import { WorkflowTabs } from './WorkflowTabs'
import { EngineeringSection } from './EngineeringSection'
import { BottomCta } from './BottomCta'
import { MarketingFooter } from './MarketingFooter'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <MarketingNav />
      <main>
        <HeroSection />
        <LogoCloud />
        <FeaturePillars />
        <WorkflowTabs />
        <EngineeringSection />
        <BottomCta />
      </main>
      <MarketingFooter />
    </div>
  )
}
