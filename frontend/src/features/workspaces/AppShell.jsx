import { useEffect, useId, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  CheckCircle2,
  FolderKanban,
  LayoutDashboard,
  Menu,
  Plus,
  Settings,
  Users2,
  X,
} from 'lucide-react'
import { NexusLogo } from '@/components/NexusLogo'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchProjects,
  fetchWorkspace,
  fetchWorkspaces,
  unwrapList,
} from '@/lib/workspace-api'

const SIDEBAR_WIDTH = 246
const MOBILE_BP = 768

function useIsMobile() {
  const [mobile, setMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < MOBILE_BP : false,
  )
  useEffect(() => {
    const onResize = () => setMobile(window.innerWidth < MOBILE_BP)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  return mobile
}

function navClass({ isActive }) {
  return ['nav-item', isActive ? 'nav-item-active' : ''].filter(Boolean).join(' ')
}

export function AppShell() {
  const { workspaceSlug } = useParams()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isMobile = useIsMobile()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const menuButtonRef = useRef(null)
  const closeButtonRef = useRef(null)
  const drawerTitleId = useId()

  const workspaceQuery = useQuery({
    queryKey: ['workspace', workspaceSlug],
    queryFn: () => fetchWorkspace(workspaceSlug),
    enabled: Boolean(workspaceSlug),
  })

  const workspacesQuery = useQuery({
    queryKey: ['workspaces'],
    queryFn: fetchWorkspaces,
  })

  const projectsQuery = useQuery({
    queryKey: ['projects', workspaceSlug, 'pinned'],
    queryFn: () => fetchProjects(workspaceSlug),
    enabled: Boolean(workspaceSlug),
  })

  const workspaces = unwrapList(workspacesQuery.data)
  const projects = unwrapList(projectsQuery.data).filter((p) => !p.archived_at)
  const pinned = projects.filter((p) => p.is_pinned).slice(0, 6)

  useEffect(() => {
    if (!isMobile) setDrawerOpen(false)
  }, [isMobile])

  useEffect(() => {
    if (!drawerOpen) return undefined
    const previous = document.activeElement
    closeButtonRef.current?.focus()

    function onKeyDown(event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        setDrawerOpen(false)
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      if (previous instanceof HTMLElement) previous.focus()
      else menuButtonRef.current?.focus()
    }
  }, [drawerOpen])

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  const sidebar = (
    <aside
      className="sidebar-glass flex h-full flex-col"
      style={{ width: SIDEBAR_WIDTH }}
      aria-label="Workspace navigation"
    >
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <NexusLogo showWordmark={false} markClassName="size-7" />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] uppercase tracking-widest text-brand">
            Nexus
          </p>
          <select
            className="w-full truncate bg-transparent text-sm font-semibold text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            value={workspaceSlug}
            aria-label="Switch workspace"
            onChange={(e) => navigate(`/app/${e.target.value}/dashboard`)}
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.slug}>
                {ws.name}
              </option>
            ))}
          </select>
        </div>
        {isMobile ? (
          <button
            ref={closeButtonRef}
            type="button"
            className="rounded-md p-1.5 text-ink-secondary hover:bg-surface-low focus-visible:ring-2 focus-visible:ring-brand"
            aria-label="Close navigation drawer"
            onClick={() => setDrawerOpen(false)}
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      <div className="px-3 py-3">
        <Link
          to={`/app/${workspaceSlug}/projects`}
          className="btn-lift flex w-full items-center justify-center gap-2 rounded-lg bg-ink px-3 py-2.5 text-sm font-semibold text-paper shadow-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          onClick={() => setDrawerOpen(false)}
        >
          <Plus className="h-4 w-4" />
          New Task
        </Link>
      </div>

      <nav
        className="flex-1 space-y-1 overflow-y-auto px-3 pb-4"
        aria-labelledby={drawerTitleId}
      >
        <p id={drawerTitleId} className="sr-only">
          Primary navigation
        </p>
        <NavLink
          to={`/app/${workspaceSlug}/dashboard`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <LayoutDashboard className="h-4 w-4" />
          Overview
        </NavLink>
        <NavLink
          to={`/app/${workspaceSlug}/my-tasks`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <CheckCircle2 className="h-4 w-4" />
          My Tasks
        </NavLink>
        <NavLink
          to={`/app/${workspaceSlug}/projects`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <FolderKanban className="h-4 w-4" />
          Projects
        </NavLink>
        <NavLink
          to={`/app/${workspaceSlug}/activity`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <Activity className="h-4 w-4" />
          Activity
        </NavLink>

        <div className="pt-4">
          <p className="px-3 pb-2 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
            Pinned Projects
          </p>
          <ul className="space-y-1">
            {pinned.map((project) => (
              <li key={project.id}>
                <NavLink
                  to={`/app/${workspaceSlug}/projects/${project.key}/board`}
                  className={navClass}
                  onClick={() => setDrawerOpen(false)}
                >
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-brand"
                    aria-hidden
                  />
                  <span className="min-w-0 flex-1 truncate">{project.name}</span>
                  <span className="font-mono text-[10px] text-ink-muted">
                    {project.key}
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <div className="space-y-1 border-t border-border px-3 py-3">
        <NavLink
          to={`/app/${workspaceSlug}/members`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <Users2 className="h-4 w-4" />
          Members
        </NavLink>
        <NavLink
          to={`/app/${workspaceSlug}/settings`}
          className={navClass}
          onClick={() => setDrawerOpen(false)}
        >
          <Settings className="h-4 w-4" />
          Settings
        </NavLink>
        <div className="mt-2 flex items-center gap-2 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-mint text-xs font-semibold text-brand shadow-hairline">
            {(user?.full_name || user?.email || '?')
              .split(' ')
              .map((p) => p[0])
              .join('')
              .slice(0, 2)
              .toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">
              {user?.full_name || user?.email}
            </p>
            <p className="truncate text-xs text-ink-muted">
              {workspaceQuery.data?.role || 'Member'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="text-xs text-ink-muted underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          >
            Sign out
          </button>
        </div>
      </div>
    </aside>
  )

  return (
    <div className="flex min-h-screen bg-paper text-ink">
      {!isMobile ? (
        <div className="sticky top-0 z-30 h-screen shrink-0">{sidebar}</div>
      ) : null}

      {isMobile && drawerOpen ? (
        <div className="fixed inset-0 z-40 flex" role="presentation">
          <button
            type="button"
            className="absolute inset-0 bg-ink/40"
            aria-label="Close navigation overlay"
            onClick={() => setDrawerOpen(false)}
          />
          <div
            className="relative z-10 h-full shadow-overlay"
            role="dialog"
            aria-modal="true"
            aria-labelledby={drawerTitleId}
          >
            {sidebar}
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="topbar-glass sticky top-0 z-20 flex h-14 items-center gap-3 px-4">
          {isMobile ? (
            <button
              ref={menuButtonRef}
              type="button"
              className="rounded-md p-2 text-ink-secondary hover:bg-surface-low focus-visible:ring-2 focus-visible:ring-brand"
              aria-label="Open navigation drawer"
              aria-expanded={drawerOpen}
              onClick={() => setDrawerOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>
          ) : null}
          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-[10px] uppercase tracking-widest text-ink-muted">
              Workspace / {workspaceQuery.data?.name || workspaceSlug}
            </p>
          </div>
          <ThemeToggle />
        </header>
        <main className="relative flex-1 overflow-y-auto bg-paper">
          <div
            className="pointer-events-none absolute inset-x-0 top-0 h-64 hero-atmosphere"
            aria-hidden
          />
          <div className="relative">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
