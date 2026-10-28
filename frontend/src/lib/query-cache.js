/** Helpers to update React Query caches without full refetches. */

/**
 * Merge a task into every matching board query for a project.
 * Moves the card between columns when status/workflow_status changes.
 */
export function upsertTaskOnBoards(queryClient, { workspaceSlug, projectKey, task }) {
  if (!workspaceSlug || !projectKey || !task?.id) return

  queryClient.setQueriesData(
    { queryKey: ['board', workspaceSlug, projectKey] },
    (old) => {
      if (!old?.columns || !old?.statuses) return old

      const columns = {}
      for (const key of Object.keys(old.columns)) {
        columns[key] = (old.columns[key] || []).filter((t) => t.id !== task.id)
      }

      const statusKey =
        task.workflow_status?.key || task.status || findStatusKey(old, task.id)

      const targetKey =
        statusKey && columns[statusKey] != null
          ? statusKey
          : findStatusKey(old, task.id) || Object.keys(columns)[0]

      if (targetKey != null && columns[targetKey]) {
        const list = [...columns[targetKey], { ...task }]
        list.sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
        columns[targetKey] = list
      }

      return { ...old, columns }
    },
  )
}

/**
 * Patch fields on a task that already sits on board columns (no column move).
 */
export function patchTaskOnBoards(queryClient, { workspaceSlug, projectKey, taskId, patch }) {
  if (!workspaceSlug || !projectKey || !taskId) return

  queryClient.setQueriesData(
    { queryKey: ['board', workspaceSlug, projectKey] },
    (old) => {
      if (!old?.columns) return old
      const columns = {}
      let found = false
      for (const key of Object.keys(old.columns)) {
        columns[key] = (old.columns[key] || []).map((t) => {
          if (t.id !== taskId) return t
          found = true
          return { ...t, ...patch }
        })
      }
      return found ? { ...old, columns } : old
    },
  )
}

function findStatusKey(board, taskId) {
  for (const status of board.statuses || []) {
    const key = status.key
    if ((board.columns[key] || []).some((t) => t.id === taskId)) {
      return key
    }
  }
  for (const key of Object.keys(board.columns || {})) {
    if ((board.columns[key] || []).some((t) => t.id === taskId)) {
      return key
    }
  }
  return null
}
