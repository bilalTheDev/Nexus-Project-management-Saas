import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { PriorityPill } from '@/features/dashboard/OverviewPage'
import { fetchBoard, updateTaskPosition } from '@/lib/workspace-api'

export function KanbanBoardPage() {
  const { workspaceSlug, projectKey } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeId, setActiveId] = useState(null)
  const [snapshot, setSnapshot] = useState(null)
  const [onlyMine, setOnlyMine] = useState(false)
  const [unassigned, setUnassigned] = useState(false)

  const boardQuery = useQuery({
    queryKey: ['board', workspaceSlug, projectKey, onlyMine, unassigned],
    queryFn: () =>
      fetchBoard(workspaceSlug, projectKey, {
        only_mine: onlyMine ? '1' : undefined,
        unassigned: unassigned ? '1' : undefined,
      }),
  })

  const statuses = boardQuery.data?.statuses || []
  const columns = boardQuery.data?.columns || {}
  const flatTasks = useMemo(() => {
    const map = {}
    for (const status of statuses) {
      for (const task of columns[status.key] || []) {
        map[task.id] = task
      }
    }
    return map
  }, [columns, statuses])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  const moveMutation = useMutation({
    mutationFn: ({ taskId, status, position, version }) =>
      updateTaskPosition(taskId, { status, position, version }),
    onError: (err) => {
      if (snapshot) {
        queryClient.setQueryData(
          ['board', workspaceSlug, projectKey, onlyMine, unassigned],
          snapshot,
        )
      }
      const detail =
        err.response?.data?.detail?.detail ||
        err.response?.data?.detail ||
        'That move is not allowed.'
      toast.error(typeof detail === 'string' ? detail : 'Move rejected')
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ['board', workspaceSlug, projectKey],
      })
    },
  })

  function findColumn(taskId) {
    for (const status of statuses) {
      if ((columns[status.key] || []).some((t) => t.id === taskId)) {
        return status.key
      }
    }
    return null
  }

  function onDragStart(event) {
    setActiveId(event.active.id)
    setSnapshot(boardQuery.data)
  }

  function onDragEnd(event) {
    setActiveId(null)
    const { active, over } = event
    if (!over) return
    const taskId = active.id
    const task = flatTasks[taskId]
    if (!task) return

    let toStatus = findColumn(over.id)
    if (!toStatus && statuses.some((s) => s.key === over.id)) {
      toStatus = over.id
    }
    if (!toStatus) return
    const fromStatus = findColumn(taskId)
    const list = [...(columns[toStatus] || [])].filter((t) => t.id !== taskId)
    const overIndex = list.findIndex((t) => t.id === over.id)
    const insertAt = overIndex >= 0 ? overIndex : list.length
    list.splice(insertAt, 0, task)
    const prev = list[insertAt - 1]
    const next = list[insertAt + 1]
    const position =
      prev && next
        ? (prev.position + next.position) / 2
        : prev
          ? prev.position + 1000
          : next
            ? next.position / 2 || 1000
            : 1000

    if (fromStatus === toStatus && task.position === position) return

    moveMutation.mutate({
      taskId,
      status: toStatus,
      position,
      version: task.version,
    })
  }

  if (boardQuery.isLoading) {
    return <p className="p-6 text-sm text-[var(--text-muted)]">Loading board…</p>
  }
  if (boardQuery.isError) {
    return (
      <p className="p-6 text-sm text-[var(--danger)]">Could not load board.</p>
    )
  }

  const activeTask = activeId ? flatTasks[activeId] : null

  return (
    <div className="px-4 py-6 sm:px-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl text-[var(--text)]">Board</h2>
          <p className="text-sm text-[var(--text-secondary)]">
            Columns follow the project workflow. Invalid moves snap back.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={onlyMine}
              onChange={(e) => setOnlyMine(e.target.checked)}
            />
            Only my issues
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={unassigned}
              onChange={(e) => setUnassigned(e.target.checked)}
            />
            Unassigned
          </label>
        </div>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
      >
        <div className="flex gap-3 overflow-x-auto pb-4">
          {statuses.map((status) => {
            const items = columns[status.key] || []
            const overWip =
              status.wip_limit && items.length > status.wip_limit
            return (
              <BoardColumn
                key={status.id}
                status={status}
                items={items}
                overWip={overWip}
                workspaceSlug={workspaceSlug}
                onOpen={(id) =>
                  navigate(`/app/${workspaceSlug}/issues/${id}?from=${projectKey}`)
                }
              />
            )
          })}
        </div>
        <DragOverlay>
          {activeTask ? (
            <div className="w-72 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-3 shadow-raised">
              <p className="font-mono text-xs text-[var(--text-muted)]">
                {activeTask.issue_key}
              </p>
              <p className="text-sm text-[var(--text)]">{activeTask.title}</p>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}

function BoardColumn({ status, items, overWip, workspaceSlug, onOpen }) {
  const { setNodeRef } = useDroppable({ id: status.key })
  return (
    <section
      ref={setNodeRef}
      className="flex w-72 shrink-0 flex-col rounded-2xl border border-[var(--border)] bg-[var(--surface-2)]"
    >
      <header className="flex items-center justify-between px-3 py-2">
        <h3 className="text-sm font-medium text-[var(--text)]">{status.name}</h3>
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {items.length}
          {status.wip_limit ? ` / ${status.wip_limit}` : ''}
        </span>
      </header>
      {overWip ? (
        <p className="px-3 text-xs text-[var(--danger)]">WIP hint exceeded</p>
      ) : null}
      <SortableContext
        items={items.map((t) => t.id)}
        strategy={verticalListSortingStrategy}
      >
        <ul className="flex max-h-[70vh] flex-col gap-2 overflow-y-auto p-2">
          {items.map((task) => (
            <BoardCard
              key={task.id}
              task={task}
              workspaceSlug={workspaceSlug}
              onOpen={() => onOpen(task.id)}
            />
          ))}
        </ul>
      </SortableContext>
    </section>
  )
}

function BoardCard({ task, onOpen, workspaceSlug: _workspaceSlug }) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: task.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }
  return (
    <li
      ref={setNodeRef}
      style={style}
      className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-3"
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          className="mt-0.5 cursor-grab text-[var(--text-muted)]"
          aria-label="Drag issue"
          {...attributes}
          {...listeners}
        >
          ⋮⋮
        </button>
        <button type="button" className="min-w-0 flex-1 text-left" onClick={onOpen}>
          <p className="font-mono text-[10px] text-[var(--text-muted)]">
            {task.issue_key}
          </p>
          <p className="text-sm text-[var(--text)]">{task.title}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            <PriorityPill priority={task.priority} />
            {task.issue_type?.name ? (
              <span className="rounded bg-[var(--surface-3)] px-1.5 py-0.5 text-[10px]">
                {task.issue_type.name}
              </span>
            ) : null}
            {task.assignee?.full_name || task.assignee?.email ? (
              <span className="text-[10px] text-[var(--text-muted)]">
                {task.assignee.full_name || task.assignee.email}
              </span>
            ) : null}
          </div>
        </button>
      </div>
    </li>
  )
}
