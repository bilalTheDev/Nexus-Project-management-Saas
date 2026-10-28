import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { PriorityPill, StatusPill } from '@/features/dashboard/OverviewPage'
import { Button } from '@/components/ui/Button'
import {
  applyIssueTransition,
  fetchComments,
  fetchIssueHistory,
  fetchIssueTransitions,
  fetchTask,
  postComment,
  updateTask,
  unwrapList,
} from '@/lib/workspace-api'
import { SafeMarkdown } from '@/components/SafeMarkdown'

export function TaskDetailPage() {
  const { workspaceSlug, taskId, issueId } = useParams()
  const id = issueId || taskId
  const [params] = useSearchParams()
  const fromProject = params.get('from')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const closeRef = useRef(null)
  const [comment, setComment] = useState('')
  const [tab, setTab] = useState('comments')

  const taskQuery = useQuery({
    queryKey: ['task', id],
    queryFn: () => fetchTask(id),
  })
  const commentsQuery = useQuery({
    queryKey: ['comments', id],
    queryFn: () => fetchComments(id),
  })
  const transitionsQuery = useQuery({
    queryKey: ['transitions', id],
    queryFn: () => fetchIssueTransitions(id),
    enabled: Boolean(id),
  })
  const historyQuery = useQuery({
    queryKey: ['history', id],
    queryFn: () => fetchIssueHistory(id),
    enabled: tab === 'history',
  })

  const updateMutation = useMutation({
    mutationFn: (payload) =>
      updateTask(id, { ...payload, version: taskQuery.data?.version }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', id] })
      queryClient.invalidateQueries({ queryKey: ['board'] })
      queryClient.invalidateQueries({ queryKey: ['history', id] })
      toast.success('Saved')
    },
    onError: (err) => {
      if (err.response?.status === 409) {
        toast.error('This issue changed. Reload?', {
          action: {
            label: 'Reload',
            onClick: () => taskQuery.refetch(),
          },
        })
        return
      }
      toast.error('Could not save issue')
    },
  })

  const transitionMutation = useMutation({
    mutationFn: (transitionId) =>
      applyIssueTransition(id, {
        transition_id: transitionId,
        version: taskQuery.data?.version,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', id] })
      queryClient.invalidateQueries({ queryKey: ['transitions', id] })
      queryClient.invalidateQueries({ queryKey: ['board'] })
      queryClient.invalidateQueries({ queryKey: ['history', id] })
      toast.success('Status updated')
    },
    onError: (err) => {
      const detail =
        err.response?.data?.detail?.detail || err.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Transition rejected')
    },
  })

  const commentMutation = useMutation({
    mutationFn: (body) => postComment(id, body),
    onSuccess: () => {
      setComment('')
      queryClient.invalidateQueries({ queryKey: ['comments', id] })
      queryClient.invalidateQueries({ queryKey: ['activity'] })
      toast.success('Comment added')
    },
  })

  function close() {
    const projectKey = fromProject || taskQuery.data?.project_key
    if (projectKey) {
      navigate(`/app/${workspaceSlug}/projects/${projectKey}/board`)
    } else {
      navigate(`/app/${workspaceSlug}/dashboard`)
    }
  }

  useEffect(() => {
    closeRef.current?.focus()
    function onKey(event) {
      if (event.key === 'Escape') close()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const task = taskQuery.data
  const comments = unwrapList(commentsQuery.data)
  const transitions = unwrapList(transitionsQuery.data)
  const history = unwrapList(historyQuery.data)

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/40">
      <button
        type="button"
        className="flex-1 cursor-default"
        aria-label="Close issue drawer"
        onClick={close}
      />
      <aside
        className="flex h-full w-full max-w-[640px] flex-col border-l border-border bg-surface shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-label="Issue detail"
      >
        <header className="flex items-center justify-between border-b border-border px-5 py-3">
          <p className="font-mono text-xs text-ink-muted">
            {task?.project_name || 'Project'} / {task?.issue_key || '…'}
          </p>
          <button
            ref={closeRef}
            type="button"
            className="rounded-md p-2 text-ink-secondary hover:bg-surface-low focus-visible:ring-2 focus-visible:ring-brand"
            aria-label="Close drawer"
            onClick={close}
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          {taskQuery.isLoading ? (
            <p className="text-ink-muted">Loading issue…</p>
          ) : taskQuery.isError ? (
            <p className="text-red-700">Issue not found.</p>
          ) : (
            <>
              <input
                className="w-full bg-transparent font-display text-3xl text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                defaultValue={task.title}
                key={task.title}
                aria-label="Issue summary"
                onBlur={(e) => {
                  if (e.target.value !== task.title) {
                    updateMutation.mutate({ title: e.target.value })
                  }
                }}
              />

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <Field label="Status">
                  <p className="text-sm text-ink">
                    {task.workflow_status?.name || task.status}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {transitions.map((tr) => (
                      <Button
                        key={tr.id}
                        type="button"
                        variant="ghost"
                        onClick={() => transitionMutation.mutate(tr.id)}
                      >
                        {tr.name}
                      </Button>
                    ))}
                  </div>
                </Field>
                <Field label="Priority">
                  <select
                    className="w-full rounded-md border border-border bg-paper px-2 py-1.5 text-sm"
                    value={task.priority}
                    onChange={(e) =>
                      updateMutation.mutate({ priority: e.target.value })
                    }
                  >
                    {['urgent', 'high', 'medium', 'low'].map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Type">
                  <p className="text-sm text-ink">
                    {task.issue_type?.name || 'Issue'}
                  </p>
                </Field>
                <Field label="Assignee">
                  <p className="text-sm text-ink">
                    {task.assignee?.full_name || 'Unassigned'}
                  </p>
                </Field>
              </div>

              {task.epic_progress ? (
                <p className="mt-4 text-sm text-ink-secondary">
                  Epic progress: {task.epic_progress.label}
                </p>
              ) : null}

              <div className="mt-6 flex flex-wrap gap-2">
                <PriorityPill priority={task.priority} />
                <StatusPill status={task.status} />
              </div>

              <h2 className="mt-8 font-display text-xl text-ink">Description</h2>
              <textarea
                className="mt-2 w-full whitespace-pre-wrap rounded-lg border border-border bg-paper p-4 font-sans text-sm text-ink-secondary"
                rows={6}
                defaultValue={task.description || ''}
                key={`desc-${task.version}`}
                onBlur={(e) => {
                  if (e.target.value !== (task.description || '')) {
                    updateMutation.mutate({ description: e.target.value })
                  }
                }}
              />

              <div className="mt-8 flex gap-2 border-b border-border">
                {['comments', 'history'].map((name) => (
                  <button
                    key={name}
                    type="button"
                    className={[
                      'px-3 py-2 text-sm capitalize',
                      tab === name
                        ? 'border-b-2 border-[var(--accent)] text-[var(--text)]'
                        : 'text-[var(--text-muted)]',
                    ].join(' ')}
                    onClick={() => setTab(name)}
                  >
                    {name}
                  </button>
                ))}
              </div>

              {tab === 'comments' ? (
                <>
                  <ul className="mt-3 space-y-3">
                    {comments.map((item) => (
                      <li
                        key={item.id}
                        className="rounded-lg border border-border bg-paper p-3"
                      >
                        <p className="text-sm font-medium text-ink">
                          {item.author?.full_name || item.author?.email}
                        </p>
                        <SafeMarkdown
                          className="mt-1 text-sm text-ink-secondary"
                          source={item.body}
                        />
                      </li>
                    ))}
                  </ul>
                  <form
                    className="mt-4"
                    onSubmit={(e) => {
                      e.preventDefault()
                      if (!comment.trim()) return
                      commentMutation.mutate(comment.trim())
                    }}
                  >
                    <textarea
                      className="w-full rounded-md border border-border bg-paper px-3 py-2 text-sm"
                      rows={3}
                      placeholder="Comment — use @email to mention someone"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <div className="mt-2 flex justify-end">
                      <Button type="submit" disabled={commentMutation.isPending}>
                        Comment
                      </Button>
                    </div>
                  </form>
                </>
              ) : (
                <ul className="mt-3 space-y-2">
                  {history.map((row) => (
                    <li
                      key={row.id}
                      className="rounded-lg border border-border bg-paper px-3 py-2 text-sm"
                    >
                      <span className="font-medium">{row.field}</span>:{' '}
                      <span className="text-ink-muted">{row.old_value || '∅'}</span>
                      {' → '}
                      <span>{row.new_value || '∅'}</span>
                      <p className="text-xs text-ink-muted">
                        {row.actor?.email} ·{' '}
                        {new Date(row.created_at).toLocaleString()}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block text-xs uppercase tracking-wide text-ink-muted">
      {label}
      <div className="mt-1 normal-case tracking-normal">{children}</div>
    </label>
  )
}
