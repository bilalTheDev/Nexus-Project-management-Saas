import { useMemo } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchIssueNavigator, unwrapList } from '@/lib/workspace-api'

export function IssuesNavigatorPage() {
  const { workspaceSlug, projectKey } = useParams()
  const [params, setParams] = useSearchParams()

  const queryParams = useMemo(() => {
    const next = {
      project: projectKey || params.get('project') || undefined,
      type: params.get('type') || undefined,
      status: params.get('status') || undefined,
      priority: params.get('priority') || undefined,
      text: params.get('text') || undefined,
      q: params.get('q') || undefined,
      page: params.get('page') || '1',
    }
    Object.keys(next).forEach((k) => {
      if (!next[k]) delete next[k]
    })
    return next
  }, [params, projectKey])

  const issuesQ = useQuery({
    queryKey: ['issue-navigator', workspaceSlug, queryParams],
    queryFn: () => fetchIssueNavigator(workspaceSlug, queryParams),
  })

  function setFilter(key, value) {
    const next = new URLSearchParams(params)
    if (!value) next.delete(key)
    else next.set(key, value)
    next.delete('page')
    setParams(next)
  }

  const results = unwrapList(issuesQ.data)

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <h2 className="font-display text-2xl text-[var(--text)]">Issues</h2>
      <p className="text-sm text-[var(--text-secondary)]">
        Filters live in the URL so views can be shared. Optional query language
        via <code className="font-mono text-xs">q</code>.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <input
          className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          placeholder="Text search"
          value={params.get('text') || ''}
          onChange={(e) => setFilter('text', e.target.value)}
        />
        <select
          className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          value={params.get('priority') || ''}
          onChange={(e) => setFilter('priority', e.target.value)}
        >
          <option value="">Any priority</option>
          {['urgent', 'high', 'medium', 'low'].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input
          className="min-w-[240px] flex-1 rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 font-mono text-sm"
          placeholder='q: project = KEY AND status != done'
          value={params.get('q') || ''}
          onChange={(e) => setFilter('q', e.target.value)}
        />
      </div>

      {issuesQ.isError ? (
        <p className="mt-4 text-sm text-[var(--danger)]" role="alert">
          {issuesQ.error?.response?.data?.detail || 'Query failed'}
        </p>
      ) : null}

      <p className="mt-4 text-xs text-[var(--text-muted)]">
        {issuesQ.data?.count ?? 0} issues
      </p>
      <ul className="mt-2 divide-y divide-[var(--border)] rounded-xl border border-[var(--border)] bg-[var(--surface-1)]">
        {results.map((issue) => (
          <li key={issue.id}>
            <Link
              to={`/app/${workspaceSlug}/issues/${issue.id}?from=${issue.project_key}`}
              className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--surface-2)]"
            >
              <span className="font-mono text-xs text-[var(--text-muted)]">
                {issue.issue_key}
              </span>
              <span className="flex-1 text-sm text-[var(--text)]">
                {issue.title}
              </span>
              <span className="text-xs capitalize text-[var(--text-muted)]">
                {issue.priority}
              </span>
            </Link>
          </li>
        ))}
        {!issuesQ.isLoading && results.length === 0 ? (
          <li className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
            No issues match these filters.
          </li>
        ) : null}
      </ul>
    </div>
  )
}
