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
    body: 'Use project reports for delivery charts once a project is open.',
  },
]

export function GuidedTour() {
  const { workspaceSlug } = useParams()
  const queryClient = useQueryClient()
  const queryKey = ['onboarding', workspaceSlug]

  const query = useQuery({
    queryKey,
    queryFn: () => fetchOnboarding(workspaceSlug),
    enabled: Boolean(workspaceSlug),
  })

  const mutation = useMutation({
    mutationFn: (payload) => updateOnboarding(workspaceSlug, payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey })
      const previous = queryClient.getQueryData(queryKey)
      if (previous) {
        queryClient.setQueryData(queryKey, {
          ...previous,
          tour_skipped:
            payload.tour_skipped !== undefined
              ? Boolean(payload.tour_skipped)
              : previous.tour_skipped,
          tour_completed:
            payload.tour_completed !== undefined
              ? Boolean(payload.tour_completed)
              : previous.tour_completed,
          tour_step:
            payload.tour_step !== undefined
              ? Number(payload.tour_step)
              : previous.tour_step,
        })
      }
      return { previous }
    },
    onError: (_err, _payload, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous)
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data)
    },
  })

  const data = query.data
  if (!data || data.tour_completed || data.tour_skipped) return null

  const step = Math.min(Math.max(0, Number(data.tour_step) || 0), STEPS.length - 1)
  const current = STEPS[step]
  const isLast = step >= STEPS.length - 1

  function skip() {
    mutation.mutate({ tour_skipped: true })
  }

  function back() {
    if (step <= 0 || mutation.isPending) return
    mutation.mutate({ tour_step: step - 1 })
  }

  function next() {
    if (mutation.isPending) return
    if (isLast) {
      mutation.mutate({ tour_completed: true, tour_step: step })
    } else {
      mutation.mutate({ tour_step: step + 1 })
    }
  }

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
        <Button type="button" variant="ghost" onClick={skip}>
          Skip
        </Button>
        {step > 0 ? (
          <Button type="button" variant="ghost" onClick={back}>
            Back
          </Button>
        ) : null}
        <Button type="button" onClick={next}>
          {isLast ? 'Finish' : 'Next'}
        </Button>
      </div>
    </div>
  )
}
