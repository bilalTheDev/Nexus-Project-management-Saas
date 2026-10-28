import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { createComponent, fetchComponents, unwrapList } from '@/lib/workspace-api'

export function ComponentsPage() {
  const { workspaceSlug, projectKey } = useParams()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')

  const listQ = useQuery({
    queryKey: ['components', workspaceSlug, projectKey],
    queryFn: () => fetchComponents(workspaceSlug, projectKey),
  })

  const createM = useMutation({
    mutationFn: (payload) => createComponent(workspaceSlug, projectKey, payload),
    onSuccess: () => {
      setName('')
      queryClient.invalidateQueries({
        queryKey: ['components', workspaceSlug, projectKey],
      })
      toast.success('Component created')
    },
  })

  const components = unwrapList(listQ.data)

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <h2 className="font-display text-2xl text-[var(--text)]">Components</h2>
      <p className="text-sm text-[var(--text-secondary)]">
        Name a component, optionally assign a lead and default assignee later.
      </p>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (!name.trim()) return
          createM.mutate({ name: name.trim() })
        }}
      >
        <input
          className="flex-1 rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          placeholder="Component name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button type="submit">Add</Button>
      </form>
      <ul className="mt-6 space-y-2">
        {components.map((c) => (
          <li
            key={c.id}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-4 py-3 text-sm text-[var(--text)]"
          >
            {c.name}
          </li>
        ))}
      </ul>
    </div>
  )
}
