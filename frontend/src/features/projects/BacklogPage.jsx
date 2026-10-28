import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import {
  completeSprint,
  createIssue,
  createSprint,
  fetchBacklog,
  rankIssue,
  startSprint,
} from '@/lib/workspace-api'

export function BacklogPage() {
  const { workspaceSlug, projectKey } = useParams()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [sprintName, setSprintName] = useState('')

  const backlogQuery = useQuery({
    queryKey: ['backlog', workspaceSlug, projectKey],
    queryFn: () => fetchBacklog(workspaceSlug, projectKey),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ['backlog', workspaceSlug, projectKey],
    })
    queryClient.invalidateQueries({ queryKey: ['onboarding', workspaceSlug] })
  }

  const createIssueMutation = useMutation({
    mutationFn: (payload) => createIssue(workspaceSlug, projectKey, payload),
    onSuccess: () => {
      setTitle('')
      invalidate()
      toast.success('Issue created')
    },
    onError: () => toast.error('Could not create issue'),
  })

  const createSprintMutation = useMutation({
    mutationFn: (payload) => createSprint(workspaceSlug, projectKey, payload),
    onSuccess: () => {
      setSprintName('')
      invalidate()
      toast.success('Sprint created')
    },
  })

  const startMutation = useMutation({
    mutationFn: (sprintId) =>
      startSprint(workspaceSlug, projectKey, sprintId, {
        goal: 'Delivery goal',
      }),
    onSuccess: () => {
      invalidate()
      toast.success('Sprint started')
    },
    onError: (err) =>
      toast.error(err.response?.data?.detail || 'Could not start sprint'),
  })

  const completeMutation = useMutation({
    mutationFn: (sprintId) =>
      completeSprint(workspaceSlug, projectKey, sprintId, {
        move_incomplete_to: 'backlog',
      }),
    onSuccess: () => {
      invalidate()
      toast.success('Sprint completed')
    },
  })

  const moveMutation = useMutation({
    mutationFn: ({ issueId, sprintId, rank }) =>
      rankIssue(issueId, { sprint_id: sprintId, rank }),
    onSuccess: invalidate,
    onError: () => toast.error('Could not move issue'),
  })

  const data = backlogQuery.data
  if (backlogQuery.isLoading) {
    return <p className="p-6 text-sm text-[var(--text-muted)]">Loading backlog…</p>
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl text-[var(--text)]">Backlog</h2>
          <p className="text-sm text-[var(--text-secondary)]">
            Rank issues and plan them into sprints.
          </p>
        </div>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            if (!sprintName.trim()) return
            createSprintMutation.mutate({ name: sprintName.trim() })
          }}
        >
          <input
            className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
            placeholder="New sprint name"
            value={sprintName}
            onChange={(e) => setSprintName(e.target.value)}
          />
          <Button type="submit">Create sprint</Button>
        </form>
      </div>

      {(data?.sprints || []).map((group) => (
        <section key={group.sprint.id} className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-medium text-[var(--text)]">
              {group.sprint.name}{' '}
              <span className="font-mono text-xs uppercase text-[var(--text-muted)]">
                {group.sprint.status}
              </span>
            </h3>
            <div className="flex gap-2">
              {group.sprint.status === 'future' ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => startMutation.mutate(group.sprint.id)}
                >
                  Start
                </Button>
              ) : null}
              {group.sprint.status === 'active' ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => completeMutation.mutate(group.sprint.id)}
                >
                  Complete
                </Button>
              ) : null}
            </div>
          </div>
          <ul className="mt-3 space-y-2">
            {group.issues.map((issue) => (
              <IssueRow
                key={issue.id}
                issue={issue}
                workspaceSlug={workspaceSlug}
                onToBacklog={() =>
                  moveMutation.mutate({
                    issueId: issue.id,
                    sprintId: null,
                    rank: Date.now(),
                  })
                }
              />
            ))}
          </ul>
          <div className="mt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                const first = (data.backlog || [])[0]
                if (!first) {
                  toast.message('Create an issue in the backlog first')
                  return
                }
                moveMutation.mutate({
                  issueId: first.id,
                  sprintId: group.sprint.id,
                  rank: Date.now(),
                })
              }}
            >
              Pull top backlog issue
            </Button>
          </div>
        </section>
      ))}

      <section className="mt-10">
        <h3 className="font-medium text-[var(--text)]">Backlog</h3>
        <ul className="mt-3 space-y-2">
          {(data?.backlog || []).map((issue) => (
            <IssueRow
              key={issue.id}
              issue={issue}
              workspaceSlug={workspaceSlug}
            />
          ))}
        </ul>
        <form
          className="mt-4 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            if (!title.trim()) return
            createIssueMutation.mutate({ title: title.trim(), status: 'todo' })
          }}
        >
          <input
            className="min-w-0 flex-1 rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
            placeholder="Create issue"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Button type="submit">Add</Button>
        </form>
      </section>
    </div>
  )
}

function IssueRow({ issue, workspaceSlug, onToBacklog }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2">
      <Link
        to={`/app/${workspaceSlug}/issues/${issue.id}`}
        className="min-w-0"
      >
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {issue.issue_key}
        </span>{' '}
        <span className="text-sm text-[var(--text)]">{issue.title}</span>
      </Link>
      {onToBacklog ? (
        <button
          type="button"
          className="text-xs text-[var(--text-muted)] underline"
          onClick={onToBacklog}
        >
          To backlog
        </button>
      ) : null}
    </li>
  )
}
