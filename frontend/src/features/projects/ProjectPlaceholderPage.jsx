import { useParams } from 'react-router-dom'

export function ProjectPlaceholderPage({ title, body }) {
  const { projectKey } = useParams()
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h2 className="font-display text-2xl text-[var(--text)]">{title}</h2>
      <p className="mt-2 text-sm text-[var(--text-secondary)]">
        {body ||
          `${title} for ${projectKey} is wired in navigation. Full screens arrive in later Phase 1 polish and Phase 2 reports.`}
      </p>
    </div>
  )
}
