import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchProjects, updateOnboarding, unwrapList } from '@/lib/workspace-api'

export function CommandPalette() {
  const { workspaceSlug } = useParams()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  const projectsQuery = useQuery({
    queryKey: ['projects', workspaceSlug, 'cmdk'],
    queryFn: () => fetchProjects(workspaceSlug),
    enabled: open && Boolean(workspaceSlug),
  })

  useEffect(() => {
    function onKey(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen((value) => !value)
      }
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (!open || !workspaceSlug) return
    updateOnboarding(workspaceSlug, {
      checklist: { use_cmdk: true },
    }).catch(() => {})
  }, [open, workspaceSlug])

  const projects = unwrapList(projectsQuery.data)
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return projects.slice(0, 8)
    return projects
      .filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.key.toLowerCase().includes(q),
      )
      .slice(0, 8)
  }, [projects, query])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center bg-black/40 pt-[12vh] px-4">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Close search"
        onClick={() => setOpen(false)}
      />
      <div
        role="dialog"
        aria-label="Quick search"
        className="relative w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-raised"
      >
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search projects…"
          className="w-full border-b border-[var(--border)] bg-transparent px-4 py-3 text-[var(--text)] outline-none"
        />
        <ul className="max-h-72 overflow-auto p-2">
          <li>
            <button
              type="button"
              className="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-[var(--surface-2)]"
              onClick={() => {
                setOpen(false)
                navigate(`/app/${workspaceSlug}/projects/new`)
              }}
            >
              Create project
            </button>
          </li>
          {filtered.map((project) => (
            <li key={project.id}>
              <button
                type="button"
                className="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-[var(--surface-2)]"
                onClick={() => {
                  setOpen(false)
                  navigate(
                    `/app/${workspaceSlug}/projects/${project.key}/board`,
                  )
                }}
              >
                <span className="font-mono text-xs text-[var(--text-muted)]">
                  {project.key}
                </span>{' '}
                {project.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export function RestartTourButton() {
  const { workspaceSlug } = useParams()
  if (!workspaceSlug) return null
  return (
    <button
      type="button"
      className="text-xs text-[var(--text-muted)] underline"
      onClick={() => {
        updateOnboarding(workspaceSlug, { restart_tour: true }).then(() => {
          window.location.reload()
        })
      }}
    >
      Restart tour
    </button>
  )
}
