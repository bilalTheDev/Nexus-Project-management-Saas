import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { fetchOnboarding, updateOnboarding } from '@/lib/workspace-api'

const STEPS = [
  {
    title: 'Your workspace sidebar',
    body: 'Jump between the dashboard, projects, members, and activity from here.',
  },
  {
    title: 'The board',
    body: 'Columns follow your project workflow. Drag only along allowed transitions.',
  },
  {
    title: 'The backlog',
    body: 'Rank upcoming work and pull it into sprints when you are ready.',
  },
  {
    title: 'Issue view',
    body: 'Open any issue to edit fields, comment with @mentions, and read history.',
  },
  {
    title: 'Quick search',
    body: 'Press Ctrl/Cmd+K to jump to recent issues and projects without leaving the page.',
  },
  {
    title: 'Reports',
    body: 'Charts and delivery reports arrive next. For now, track progress on the board and summary.',
  },
]

export function GuidedTour() {
  const { workspaceSlug } = useParams()
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['onboarding', workspaceSlug],
    queryFn: () => fetchOnboarding(workspaceSlug),
    enabled: Boolean(workspaceSlug),
  })
  const mutation = useMutation({
    mutationFn: (payload) => updateOnboarding(workspaceSlug, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['onboarding', workspaceSlug] }),
  })

  const data = query.data
  if (!data || data.tour_completed || data.tour_skipped) return null
  const step = Math.min(data.tour_step || 0, STEPS.length - 1)
  const current = STEPS[step]

  return (
    <div
      className="fixed inset-x-0 bottom-4 z-50 mx-auto w-[min(440px,calc(100%-2rem))] rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4 shadow-raised"
      role="dialog"
      aria-label="Product tour"
    >
      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
        Tour {step + 1} / {STEPS.length}
      </p>
      <h2 className="mt-1 font-display text-xl text-[var(--text)]">
        {current.title}
      </h2>
      <p className="mt-2 text-sm text-[var(--text-secondary)]">{current.body}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          type="button"
          variant="ghost"
          onClick={() => mutation.mutate({ tour_skipped: true })}
        >
          Skip
        </Button>
        {step > 0 ? (
          <Button
            type="button"
            variant="ghost"
            onClick={() => mutation.mutate({ tour_step: step - 1 })}
          >
            Back
          </Button>
        ) : null}
        <Button
          type="button"
          onClick={() => {
            if (step >= STEPS.length - 1) {
              mutation.mutate({ tour_completed: true, tour_step: step })
            } else {
              mutation.mutate({ tour_step: step + 1 })
            }
          }}
        >
          {step >= STEPS.length - 1 ? 'Finish' : 'Next'}
        </Button>
      </div>
    </div>
  )
}
