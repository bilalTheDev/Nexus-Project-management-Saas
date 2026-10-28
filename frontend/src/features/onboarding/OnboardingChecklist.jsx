import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, X } from 'lucide-react'
import { fetchOnboarding, updateOnboarding } from '@/lib/workspace-api'

const LABELS = {
  create_project: 'Create a project',
  create_issue: 'Create an issue',
  invite_teammate: 'Invite a teammate',
  start_sprint: 'Start a sprint',
  use_cmdk: 'Use quick search (Ctrl/Cmd+K)',
}

export function OnboardingChecklist() {
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
  if (!data || data.checklist_dismissed) return null

  const entries = Object.entries(LABELS)
  const doneCount = entries.filter(([key]) => data.checklist?.[key]).length

  return (
    <aside className="mx-3 mb-3 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-[var(--text)]">Getting started</p>
          <p className="text-xs text-[var(--text-muted)]">
            {doneCount} of {entries.length} complete
          </p>
        </div>
        <button
          type="button"
          aria-label="Dismiss checklist"
          className="text-[var(--text-muted)]"
          onClick={() => mutation.mutate({ checklist_dismissed: true })}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <ul className="mt-3 space-y-2">
        {entries.map(([key, label]) => {
          const done = Boolean(data.checklist?.[key])
          const href = data.links?.[key] || `/app/${workspaceSlug}/dashboard`
          return (
            <li key={key}>
              <Link
                to={href}
                className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text)]"
              >
                <span
                  className={[
                    'flex h-4 w-4 items-center justify-center rounded-full border',
                    done
                      ? 'border-[var(--accent)] bg-[var(--accent)] text-white'
                      : 'border-[var(--border)]',
                  ].join(' ')}
                >
                  {done ? <Check className="h-3 w-3" /> : null}
                </span>
                <span className={done ? 'line-through opacity-70' : ''}>
                  {label}
                </span>
              </Link>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
