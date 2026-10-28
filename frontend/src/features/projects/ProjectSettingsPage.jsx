import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import {
  fetchProject,
  fetchWorkflow,
  updateProject,
  unwrapList,
} from '@/lib/workspace-api'

export function ProjectSettingsPage() {
  const { workspaceSlug, projectKey } = useParams()
  const queryClient = useQueryClient()

  const projectQuery = useQuery({
    queryKey: ['project', workspaceSlug, projectKey],
    queryFn: () => fetchProject(workspaceSlug, projectKey),
  })
  const workflowQuery = useQuery({
    queryKey: ['workflow', workspaceSlug, projectKey],
    queryFn: () => fetchWorkflow(workspaceSlug, projectKey),
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => updateProject(workspaceSlug, projectKey, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['project', workspaceSlug, projectKey],
      })
      toast.success('Project settings saved')
    },
    onError: () => toast.error('Could not save settings'),
  })

  const project = projectQuery.data
  const statuses = unwrapList(workflowQuery.data?.statuses)
  const transitions = unwrapList(workflowQuery.data?.transitions)
  const issueTypes = unwrapList(workflowQuery.data?.issue_types)

  if (projectQuery.isLoading) {
    return <p className="p-6 text-sm text-ink-muted">Loading settings…</p>
  }
  if (!project) {
    return <p className="p-6 text-sm text-danger">Project not found.</p>
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:px-6">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
          {project.key} · Settings
        </p>
        <h1 className="mt-1 font-display text-3xl text-ink">Project settings</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Defaults and the workflow seeded from the project template.
        </p>
      </div>

      <section className="rounded-2xl border border-border bg-surface-1 p-6">
        <h2 className="text-sm font-semibold text-ink">Basics</h2>
        <form
          className="mt-4 space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            const fd = new FormData(e.currentTarget)
            saveMutation.mutate({
              name: fd.get('name'),
              description: fd.get('description'),
              is_pinned: fd.get('is_pinned') === 'on',
            })
          }}
        >
          <label className="block text-sm font-medium text-ink">
            Name
            <input
              name="name"
              defaultValue={project.name}
              className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
              required
            />
          </label>
          <label className="block text-sm font-medium text-ink">
            Description
            <textarea
              name="description"
              defaultValue={project.description || ''}
              rows={3}
              className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              name="is_pinned"
              defaultChecked={Boolean(project.is_pinned)}
            />
            Pin in sidebar
          </label>
          <Button type="submit" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? 'Saving…' : 'Save'}
          </Button>
        </form>
      </section>

      <section className="rounded-2xl border border-border bg-surface-1 p-6">
        <h2 className="text-sm font-semibold text-ink">Workflow statuses</h2>
        <p className="mt-1 text-sm text-ink-secondary">
          Template: <span className="font-mono">{project.template_key}</span>
        </p>
        <ol className="mt-4 space-y-2">
          {statuses.map((s) => (
            <li
              key={s.id}
              className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm"
            >
              <span className="font-medium text-ink">{s.name}</span>
              <span className="font-mono text-[10px] text-ink-muted">
                {s.key} · {s.category}
              </span>
            </li>
          ))}
        </ol>
        <h3 className="mt-6 text-sm font-semibold text-ink">Transitions</h3>
        <ul className="mt-2 space-y-1 text-sm text-ink-secondary">
          {transitions.map((t) => (
            <li key={t.id} className="font-mono text-xs">
              {t.name}: {t.from_status_key || t.from_status} →{' '}
              {t.to_status_key || t.to_status}
            </li>
          ))}
        </ul>
        <h3 className="mt-6 text-sm font-semibold text-ink">Issue types</h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {issueTypes.map((t) => (
            <li
              key={t.id}
              className="rounded-full border border-border px-3 py-1 text-xs text-ink"
            >
              {t.name}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
