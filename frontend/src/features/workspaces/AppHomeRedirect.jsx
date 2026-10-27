import { Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/useAuth'
import { fetchWorkspaces, unwrapList } from '@/lib/workspace-api'

export function AppHomeRedirect() {
  const { isAuthenticated, bootstrapping } = useAuth()
  const workspacesQuery = useQuery({
    queryKey: ['workspaces'],
    queryFn: fetchWorkspaces,
    enabled: isAuthenticated && !bootstrapping,
  })

  if (bootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-ink-muted">
        Restoring session…
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (workspacesQuery.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-ink-muted">
        Loading workspaces…
      </div>
    )
  }

  const workspaces = unwrapList(workspacesQuery.data)
  if (workspaces.length === 0) {
    return <Navigate to="/app/workspaces/new" replace />
  }
  return <Navigate to={`/app/${workspaces[0].slug}/dashboard`} replace />
}
