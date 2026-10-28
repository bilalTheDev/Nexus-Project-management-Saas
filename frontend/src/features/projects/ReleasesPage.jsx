import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import {
  createRelease,
  fetchReleaseDetail,
  fetchReleaseNotes,
  fetchReleases,
  publishRelease,
  unwrapList,
} from '@/lib/workspace-api'

export function ReleasesPage() {
  const { workspaceSlug, projectKey } = useParams()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [selected, setSelected] = useState(null)

  const listQ = useQuery({
    queryKey: ['releases', workspaceSlug, projectKey],
    queryFn: () => fetchReleases(workspaceSlug, projectKey),
  })
  const detailQ = useQuery({
    queryKey: ['release', workspaceSlug, projectKey, selected],
    queryFn: () => fetchReleaseDetail(workspaceSlug, projectKey, selected),
    enabled: Boolean(selected),
  })
  const notesQ = useQuery({
    queryKey: ['release-notes', workspaceSlug, projectKey, selected],
    queryFn: () => fetchReleaseNotes(workspaceSlug, projectKey, selected),
    enabled: Boolean(selected),
  })

  const createM = useMutation({
    mutationFn: (payload) => createRelease(workspaceSlug, projectKey, payload),
    onSuccess: () => {
      setName('')
      queryClient.invalidateQueries({ queryKey: ['releases', workspaceSlug, projectKey] })
      toast.success('Release created')
    },
  })

  const publishM = useMutation({
    mutationFn: (payload) =>
      publishRelease(workspaceSlug, projectKey, selected, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['release', workspaceSlug, projectKey, selected] })
      queryClient.invalidateQueries({ queryKey: ['releases', workspaceSlug, projectKey] })
      toast.success('Release published')
    },
    onError: async (err) => {
      if (err.response?.status === 409 && err.response.data?.warning) {
        const ok = window.confirm(
          `${err.response.data.detail}\n\nPublish anyway and leave unresolved issues?`,
        )
        if (ok) {
          publishM.mutate({ force: true })
        }
        return
      }
      toast.error('Could not publish release')
    },
  })

  const releases = unwrapList(listQ.data)

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <h2 className="font-display text-2xl text-[var(--text)]">Releases</h2>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (!name.trim()) return
          createM.mutate({ name: name.trim() })
        }}
      >
        <input
          className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          placeholder="Release name (e.g. 1.2.0)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button type="submit">Create</Button>
      </form>

      <ul className="mt-6 space-y-2">
        {releases.map((r) => (
          <li key={r.id}>
            <button
              type="button"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-left"
              onClick={() => setSelected(r.id)}
            >
              <span className="font-medium text-[var(--text)]">{r.name}</span>{' '}
              <span className="font-mono text-xs uppercase text-[var(--text-muted)]">
                {r.status}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {selected && detailQ.data ? (
        <div className="mt-8 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-display text-xl text-[var(--text)]">
              {detailQ.data.release.name}
            </h3>
            {detailQ.data.release.status !== 'released' ? (
              <Button type="button" onClick={() => publishM.mutate({})}>
                Release
              </Button>
            ) : null}
          </div>
          {detailQ.data.unresolved_count > 0 ? (
            <p className="mt-2 text-sm text-[var(--warning,#a86a12)]">
              {detailQ.data.unresolved_count} unresolved issues — publishing will
              warn.
            </p>
          ) : null}
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(detailQ.data.issues_by_status || {}).map(
              ([status, issues]) => (
                <div key={status}>
                  <p className="text-xs uppercase text-[var(--text-muted)]">
                    {status}
                  </p>
                  <ul className="mt-1 space-y-1 text-sm">
                    {issues.map((i) => (
                      <li key={i.id}>
                        {i.key}: {i.title}
                      </li>
                    ))}
                  </ul>
                </div>
              ),
            )}
          </div>
          {notesQ.data?.markdown ? (
            <pre className="mt-4 overflow-auto rounded-lg bg-[var(--bg)] p-3 text-xs text-[var(--text-secondary)]">
              {notesQ.data.markdown}
            </pre>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
