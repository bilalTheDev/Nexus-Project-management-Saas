import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
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
import { PriorityPill, StatusPill } from '@/features/dashboard/OverviewPage'
import { fetchBoard, updateTaskPosition } from '@/lib/workspace-api'

const COLUMNS = [
  { id: 'backlog', label: 'Backlog' },
  { id: 'todo', label: 'To Do' },
  { id: 'in_progress', label: 'In Progress' },
  { id: 'in_review', label: 'In Review' },
  { id: 'done', label: 'Done' },
]

export function KanbanBoardPage() {
  const { workspaceSlug, projectKey } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeId, setActiveId] = useState(null)
  const [snapshot, setSnapshot] = useState(null)

  const boardQuery = useQuery({
    queryKey: ['board', workspaceSlug, projectKey],
    queryFn: () => fetchBoard(workspaceSlug, projectKey),
  })

  const columns = boardQuery.data?.columns || {}
  const flatTasks = useMemo(() => {
    const map = {}
    for (const col of COLUMNS) {
      for (const task of columns[col.id] || []) {
        map[task.id] = task
      }
    }
    return map
  }, [columns])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  const moveMutation = useMutation({
    mutationFn: ({ taskId, status, position }) =>
      updateTaskPosition(taskId, { status, position }),
    onError: () => {
      if (snapshot) {
        queryClient.setQueryData(
          ['board', workspaceSlug, projectKey],
          snapshot,
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ['board', workspaceSlug, projectKey],
      })
    },
  })

  function findColumn(taskId) {
    for (const col of COLUMNS) {
      if ((columns[col.id] || []).some((t) => t.id === taskId)) return col.id
    }
    return null
  }

  function onDragStart(event) {
    setActiveId(event.active.id)
    setSnapshot(structuredClone(boardQuery.data))
  }

  function onDragEnd(event) {
    const { active, over } = event
    setActiveId(null)
    if (!over) return

    const taskId = active.id
    const overId = over.id
    const fromCol = findColumn(taskId)
    let toCol = COLUMNS.some((c) => c.id === overId) ? overId : findColumn(overId)
    if (!fromCol || !toCol) return

    const next = structuredClone(boardQuery.data)
    const fromList = next.columns[fromCol] || []
    const toList = next.columns[toCol] || []
    const fromIndex = fromList.findIndex((t) => t.id === taskId)
    if (fromIndex < 0) return
    const [task] = fromList.splice(fromIndex, 1)

    let insertIndex = toList.findIndex((t) => t.id === overId)
    if (insertIndex < 0) insertIndex = toList.length
    task.status = toCol
    toList.splice(insertIndex, 0, task)
    next.columns[fromCol] = fromList
    next.columns[toCol] = toList
    queryClient.setQueryData(['board', workspaceSlug, projectKey], next)

    const prev = toList[insertIndex - 1]
    const following = toList[insertIndex + 1]
    let position
    if (prev && following) position = (prev.position + following.position) / 2
    else if (prev) position = prev.position + 1000
    else if (following) position = following.position - 1000
    else position = 1000

    moveMutation.mutate({ taskId, status: toCol, position })
  }

  if (boardQuery.isLoading) {
    return <div className="p-8 text-ink-muted">Loading board…</div>
  }
  if (boardQuery.isError) {
    return <div className="p-8 text-red-700">Could not load board.</div>
  }

  const project = boardQuery.data.project
  const activeTask = activeId ? flatTasks[activeId] : null

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="border-b border-border px-4 py-4 sm:px-6">
        <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
          {workspaceSlug} / Projects / {project.key}
        </p>
        <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-2xl text-ink sm:text-3xl">
            {project.name}
          </h1>
          <Link
            to={`/app/${workspaceSlug}/projects`}
            className="text-sm text-ink-secondary underline-offset-2 hover:underline"
          >
            Back to projects
          </Link>
        </div>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
      >
        <div className="flex flex-1 gap-3 overflow-x-auto p-4 sm:p-6">
          {COLUMNS.map((column) => {
            const tasks = columns[column.id] || []
            return (
              <section
                key={column.id}
                className="flex w-72 shrink-0 flex-col rounded-xl border border-border bg-paper"
                aria-label={column.label}
              >
                <header className="flex items-center justify-between border-b border-border px-3 py-2">
                  <h2 className="font-mono text-xs uppercase tracking-wide text-ink-secondary">
                    {column.label}
                  </h2>
                  <span className="text-xs text-ink-muted">{tasks.length}</span>
                </header>
                <SortableContext
                  id={column.id}
                  items={tasks.map((t) => t.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <ul className="flex-1 space-y-2 overflow-y-auto p-2">
                    <ColumnDropZone id={column.id} />
                    {tasks.map((task) => (
                      <SortableTaskCard
                        key={task.id}
                        task={task}
                        onOpen={() =>
                          navigate(
                            `/app/${workspaceSlug}/tasks/${task.id}?from=${projectKey}`,
                          )
                        }
                      />
                    ))}
                  </ul>
                </SortableContext>
              </section>
            )
          })}
        </div>
        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} dragging /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}

function ColumnDropZone({ id }) {
  const { setNodeRef } = useDroppable({ id })
  return <div ref={setNodeRef} className="min-h-2" />
}

function SortableTaskCard({ task, onOpen }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }
  return (
    <li ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <TaskCard task={task} onOpen={onOpen} />
    </li>
  )
}

function TaskCard({ task, onOpen, dragging }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className={`w-full rounded-lg border border-border bg-surface p-3 text-left shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
        dragging ? 'rotate-1 shadow-lg ring-1 ring-brand' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] text-ink-muted">{task.task_key}</span>
        <PriorityPill priority={task.priority} />
      </div>
      <p className="mt-1 text-sm font-semibold text-ink">{task.title}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <StatusPill status={task.status} />
        {task.labels?.map((label) => (
          <span
            key={label}
            className="rounded bg-mint px-1.5 py-0.5 text-[10px] text-brand"
          >
            {label}
          </span>
        ))}
      </div>
    </button>
  )
}
