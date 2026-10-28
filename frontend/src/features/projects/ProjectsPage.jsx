import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import {
  createProject,
  fetchProjects,
  unwrapList,
} from '@/lib/workspace-api'

export function ProjectsPage() {
  const { workspaceSlug } = useParams()
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const activeQuery = useQuery({
    queryKey: ['projects', workspaceSlug, 'active', search],
    queryFn: () =>
      fetchProjects(workspaceSlug, search ? { search } : undefined),
  })
  const archivedQuery = useQuery({
    queryKey: ['projects', workspaceSlug, 'archived'],
    queryFn: () => fetchProjects(workspaceSlug, { archived: '1' }),
  })

  const createMutation = useMutation({
    mutationFn: (payload) => createProject(workspaceSlug, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', workspaceSlug] })
      setShowCreate(false)
    },
  })

  const projects = unwrapList(activeQuery.data)
  const archived = unwrapList(archivedQuery.data)

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
        Directory / Workspaces / Active Cycle
      </p>
      <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display text-3xl text-ink sm:text-4xl">
          Projects ({projects.length} active, {archived.length} archived)
        </h1>
        <Link
          to={`/app/${workspaceSlug}/projects/new`}
          className="inline-flex items-center rounded-md bg-[var(--text)] px-3 py-2 text-sm font-semibold text-[var(--bg)]"
        >
          + New Project
        </Link>
      </div>

      <div className="mt-6">
        <input
          type="search"
          placeholder="Search projects…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-md rounded-md border border-border bg-paper px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
        />
      </div>

      {activeQuery.isLoading ? (
        <p className="mt-8 text-ink-muted">Loading projects…</p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/app/${workspaceSlug}/projects/${project.key}/board`}
              className="rounded-xl border border-border bg-paper p-5 transition hover:border-border-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-ink">
                    {project.name}
                  </h2>
                  <p className="font-mono text-xs text-ink-muted">{project.key}</p>
                </div>
                <span className="rounded-full bg-mint px-2 py-0.5 text-xs capitalize text-brand">
                  {project.status?.replaceAll('_', ' ')}
                </span>
              </div>
              <p className="mt-3 line-clamp-2 text-sm text-ink-secondary">
                {project.description || 'No description yet.'}
              </p>
              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-surface-low">
                <div
                  className="h-full bg-brand"
                  style={{ width: `${project.progress || 0}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-ink-muted">
                {project.progress}% · {project.resolved} of {project.total_tasks}{' '}
                resolved · {project.open_tasks} open
                {project.overdue ? ` · ${project.overdue} overdue` : ''}
              </p>
              {project.lead ? (
                <p className="mt-2 text-xs text-ink-secondary">
                  Lead: {project.lead.full_name || project.lead.email}
                </p>
              ) : null}
            </Link>
          ))}
        </div>
      )}

      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-paper p-4 lg:col-span-2">
          <h2 className="font-display text-xl text-ink">
            Throughput & Burnup
          </h2>
          <p className="mt-1 text-sm text-ink-muted">
            Derived from resolved task counts in the active cycle.
          </p>
          <div className="mt-4 flex h-32 items-end gap-2">
            {[8, 12, 10, 16, 21].map((value, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-brand/80"
                  style={{ height: `${(value / 21) * 100}%` }}
                />
                <span className="font-mono text-[10px] text-ink-muted">
                  W{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-border bg-paper p-4">
          <h2 className="font-display text-xl text-ink">Archived</h2>
          <ul className="mt-3 space-y-2">
            {archived.map((project) => (
              <li key={project.id} className="text-sm text-ink-secondary">
                <span className="font-mono text-xs">{project.key}</span>{' '}
                {project.name}
              </li>
            ))}
            {archived.length === 0 ? (
              <li className="text-sm text-ink-muted">No archived projects.</li>
            ) : null}
          </ul>
        </div>
      </div>

      {showCreate ? (
        <CreateProjectModal
          onClose={() => setShowCreate(false)}
          onSubmit={(payload) => createMutation.mutate(payload)}
          pending={createMutation.isPending}
          error={createMutation.error?.response?.data}
        />
      ) : null}
    </div>
  )
}

function CreateProjectModal({ onClose, onSubmit, pending, error }) {
  const [name, setName] = useState('')
  const [key, setKey] = useState('')
  const [description, setDescription] = useState('')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <form
        className="w-full max-w-md rounded-xl border border-border bg-surface p-6"
        onSubmit={(e) => {
          e.preventDefault()
          onSubmit({
            name,
            key: key.toUpperCase(),
            description,
            status: 'planning',
            is_pinned: true,
          })
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Create project"
      >
        <h2 className="font-display text-2xl text-ink">New Project</h2>
        <label className="mt-4 block text-sm">
          Name
          <input
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              if (!key) {
                setKey(
                  e.target.value
                    .toUpperCase()
                    .replace(/[^A-Z0-9]+/g, '')
                    .slice(0, 8),
                )
              }
            }}
            required
          />
        </label>
        <label className="mt-3 block text-sm">
          Key
          <input
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2 font-mono uppercase"
            value={key}
            onChange={(e) => setKey(e.target.value.toUpperCase())}
            required
          />
        </label>
        <label className="mt-3 block text-sm">
          Description
          <textarea
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        {error ? (
          <p className="mt-2 text-sm text-red-700" role="alert">
            {error.key?.[0] || error.detail || 'Could not create project.'}
          </p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? 'Creating…' : 'Create'}
          </Button>
        </div>
      </form>
    </div>
  )
}
