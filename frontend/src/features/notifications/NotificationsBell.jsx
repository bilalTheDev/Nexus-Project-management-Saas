import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import { useParams, Link } from 'react-router-dom'
import {
  fetchNotifications,
  markNotificationRead,
  unwrapList,
} from '@/lib/workspace-api'

export function NotificationsBell() {
  const { workspaceSlug } = useParams()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const notificationsQuery = useQuery({
    queryKey: ['notifications', workspaceSlug],
    queryFn: () => fetchNotifications(workspaceSlug),
    enabled: Boolean(workspaceSlug),
    refetchInterval: open ? 15000 : 60000,
  })

  const items = unwrapList(notificationsQuery.data)
  const unread = useMemo(
    () => items.filter((n) => !n.read_at).length,
    [items],
  )

  const markRead = useMutation({
    mutationFn: (id) => markNotificationRead(workspaceSlug, id),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ['notifications', workspaceSlug],
      }),
  })

  return (
    <div className="relative">
      <button
        type="button"
        className="relative rounded-md p-2 text-ink-secondary hover:bg-surface-low focus-visible:ring-2 focus-visible:ring-brand"
        aria-label={
          unread ? `Notifications, ${unread} unread` : 'Notifications'
        }
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Bell className="h-5 w-5" />
        {unread > 0 ? (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 font-mono text-[10px] text-paper">
            {unread > 9 ? '9+' : unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <>
          <button
            type="button"
            className="fixed inset-0 z-30 cursor-default"
            aria-label="Close notifications"
            onClick={() => setOpen(false)}
          />
          <div
            className="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-surface-1 shadow-overlay"
            role="dialog"
            aria-label="Notifications"
          >
            <div className="border-b border-border px-3 py-2">
              <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
                Notifications
              </p>
            </div>
            <ul className="max-h-80 overflow-y-auto">
              {items.length === 0 ? (
                <li className="px-3 py-6 text-center text-sm text-ink-muted">
                  You are all caught up.
                </li>
              ) : (
                items.slice(0, 20).map((n) => (
                  <li
                    key={n.id}
                    className={[
                      'border-b border-border px-3 py-2.5 text-sm last:border-0',
                      n.read_at ? 'opacity-70' : 'bg-mint/30',
                    ].join(' ')}
                  >
                    <p className="font-medium text-ink">{n.title || n.kind}</p>
                    {n.body ? (
                      <p className="mt-0.5 text-xs text-ink-secondary">{n.body}</p>
                    ) : null}
                    <div className="mt-1 flex items-center justify-between gap-2">
                      <span className="font-mono text-[10px] text-ink-muted">
                        {n.created_at
                          ? new Date(n.created_at).toLocaleString()
                          : ''}
                      </span>
                      <div className="flex gap-2">
                        {n.link ? (
                          <Link
                            to={n.link.startsWith('/') ? n.link : `/${n.link}`}
                            className="text-xs font-semibold text-brand underline-offset-2 hover:underline"
                            onClick={() => setOpen(false)}
                          >
                            Open
                          </Link>
                        ) : null}
                        {!n.read_at ? (
                          <button
                            type="button"
                            className="text-xs text-ink-muted underline-offset-2 hover:underline"
                            onClick={() => markRead.mutate(n.id)}
                          >
                            Mark read
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </li>
                ))
              )}
            </ul>
          </div>
        </>
      ) : null}
    </div>
  )
}
