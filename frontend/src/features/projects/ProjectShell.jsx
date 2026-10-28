import { NavLink, Outlet, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchProject } from '@/lib/workspace-api'

const ALL_NAV = [
  { id: 'summary', label: 'Summary', path: 'summary' },
  { id: 'backlog', label: 'Backlog', path: 'backlog' },
  { id: 'board', label: 'Board', path: 'board' },
  { id: 'list', label: 'List', path: 'list' },
  { id: 'reports', label: 'Reports', path: 'reports' },
  { id: 'issues', label: 'Issues', path: 'issues' },
  { id: 'releases', label: 'Releases', path: 'releases' },
  { id: 'components', label: 'Components', path: 'components' },
  { id: 'settings', label: 'Project settings', path: 'settings' },
]

export function ProjectShell() {
  const { workspaceSlug, projectKey } = useParams()
  const projectQuery = useQuery({
    queryKey: ['project', workspaceSlug, projectKey],
    queryFn: () => fetchProject(workspaceSlug, projectKey),
  })
  const project = projectQuery.data
  const allowed = new Set(project?.board_config?.nav || ALL_NAV.map((n) => n.id))
  const items = ALL_NAV.filter((item) => allowed.has(item.id))

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 sm:px-6">
        <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
          {workspaceSlug} / {projectKey}
        </p>
        <h1 className="font-display text-2xl text-[var(--text)]">
          {project?.name || projectKey}
        </h1>
        <nav className="mt-3 flex flex-wrap gap-1" aria-label="Project">
          {items.map((item) => (
            <NavLink
              key={item.id}
              to={`/app/${workspaceSlug}/projects/${projectKey}/${item.path}`}
              className={({ isActive }) =>
                [
                  'rounded-md px-3 py-1.5 text-sm',
                  isActive
                    ? 'bg-[var(--surface-3)] text-[var(--text)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface-2)]',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <Outlet />
    </div>
  )
}
