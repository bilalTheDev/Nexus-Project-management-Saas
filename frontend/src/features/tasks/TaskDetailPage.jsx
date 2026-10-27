import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { PriorityPill, StatusPill } from '@/features/dashboard/OverviewPage'
import { Button } from '@/components/ui/Button'
import {
  fetchComments,
  fetchTask,
  postComment,
  updateTask,
  unwrapList,
} from '@/lib/workspace-api'

export function TaskDetailPage() {
  const { workspaceSlug, taskId } = useParams()
  const [params] = useSearchParams()
  const fromProject = params.get('from')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const closeRef = useRef(null)
  const [comment, setComment] = useState('')

  const taskQuery = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(taskId),
  })
  const commentsQuery = useQuery({
    queryKey: ['comments', taskId],
    queryFn: () => fetchComments(taskId),
  })

  const updateMutation = useMutation({
    mutationFn: (payload) => updateTask(taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', taskId] })
      queryClient.invalidateQueries({ queryKey: ['board'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const commentMutation = useMutation({
    mutationFn: (body) => postComment(taskId, body),
    onSuccess: () => {
      setComment('')
      queryClient.invalidateQueries({ queryKey: ['comments', taskId] })
      queryClient.invalidateQueries({ queryKey: ['activity'] })
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
  }, [taskId])

  const task = taskQuery.data
  const comments = unwrapList(commentsQuery.data)

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/40">
      <button
        type="button"
        className="flex-1 cursor-default"
        aria-label="Close task drawer"
        onClick={close}
      />
      <aside
        className="flex h-full w-full max-w-[640px] flex-col border-l border-border bg-surface shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-label="Task detail"
      >
        <header className="flex items-center justify-between border-b border-border px-5 py-3">
          <p className="font-mono text-xs text-ink-muted">
            {task?.project_name || 'Project'} / {task?.task_key || '…'}
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
            <p className="text-ink-muted">Loading task…</p>
          ) : taskQuery.isError ? (
            <p className="text-red-700">Task not found.</p>
          ) : (
            <>
              <input
                className="w-full bg-transparent font-display text-3xl text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                defaultValue={task.title}
                aria-label="Task title"
                onBlur={(e) => {
                  if (e.target.value !== task.title) {
                    updateMutation.mutate({ title: e.target.value })
                  }
                }}
              />

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <Field label="Status">
                  <select
                    className="w-full rounded-md border border-border bg-paper px-2 py-1.5 text-sm"
                    value={task.status}
                    onChange={(e) =>
                      updateMutation.mutate({ status: e.target.value })
                    }
                  >
                    {[
                      'backlog',
                      'todo',
                      'in_progress',
                      'in_review',
                      'done',
                    ].map((s) => (
                      <option key={s} value={s}>
                        {s.replaceAll('_', ' ')}
                      </option>
                    ))}
                  </select>
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
                <Field label="Assignee">
                  <p className="text-sm text-ink">
                    {task.assignee?.full_name || 'Unassigned'}
                  </p>
                </Field>
                <Field label="Due">
                  <p className="text-sm text-ink">
                    {task.due_date
                      ? new Date(task.due_date).toLocaleString()
                      : 'None'}
                  </p>
                </Field>
              </div>

              <div className="mt-6 flex flex-wrap gap-2">
                <PriorityPill priority={task.priority} />
                <StatusPill status={task.status} />
                {task.labels?.map((label) => (
                  <span
                    key={label}
                    className="rounded bg-mint px-2 py-0.5 text-xs text-brand"
                  >
                    {label}
                  </span>
                ))}
              </div>

              <h2 className="mt-8 font-display text-xl text-ink">
                Description & Acceptance Criteria
              </h2>
              <pre className="mt-2 whitespace-pre-wrap rounded-lg border border-border bg-paper p-4 font-sans text-sm text-ink-secondary">
                {task.description || 'No description.'}
              </pre>

              <h2 className="mt-8 font-display text-xl text-ink">Activity & Comments</h2>
              <ul className="mt-3 space-y-3">
                {comments.map((item) => (
                  <li
                    key={item.id}
                    className="rounded-lg border border-border bg-paper p-3"
                  >
                    <p className="text-sm font-medium text-ink">
                      {item.author?.full_name || item.author?.email}
                    </p>
                    <p className="mt-1 text-sm text-ink-secondary">{item.body}</p>
                    <p className="mt-1 text-xs text-ink-muted">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
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
                  className="w-full rounded-md border border-border bg-paper px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                  rows={3}
                  placeholder="Write a comment…"
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
          )}
        </div>

        <footer className="border-t border-border px-5 py-3 text-xs text-ink-muted">
          <Link
            to={`/app/${workspaceSlug}/dashboard`}
            className="underline-offset-2 hover:underline"
          >
            Back to overview
          </Link>
        </footer>
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
