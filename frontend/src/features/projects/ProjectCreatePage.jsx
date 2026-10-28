import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import {
  checkProjectKey,
  createProject,
  fetchMembers,
  fetchProjectTemplates,
  inviteMember,
  unwrapList,
} from '@/lib/workspace-api'

function suggestKey(name) {
  const letters = (name || '')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 4)
  return letters.length >= 2 ? letters : 'PROJ'
}

export function ProjectCreatePage() {
  const { workspaceSlug } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [step, setStep] = useState(0)
  const [templateKey, setTemplateKey] = useState('scrum')
  const [name, setName] = useState('')
  const [key, setKey] = useState('')
  const [keyTouched, setKeyTouched] = useState(false)
  const [leadId, setLeadId] = useState('')
  const [defaultAssigneeId, setDefaultAssigneeId] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [error, setError] = useState('')

  const templatesQuery = useQuery({
    queryKey: ['project-templates'],
    queryFn: fetchProjectTemplates,
  })
  const membersQuery = useQuery({
    queryKey: ['members', workspaceSlug],
    queryFn: () => fetchMembers(workspaceSlug),
  })
  const keyCheckQuery = useQuery({
    queryKey: ['project-key', workspaceSlug, key],
    queryFn: () => checkProjectKey(workspaceSlug, key),
    enabled: key.length >= 2,
  })

  const members = unwrapList(membersQuery.data)
  const templates = templatesQuery.data || []

  useEffect(() => {
    if (!keyTouched) setKey(suggestKey(name))
  }, [name, keyTouched])

  const createMutation = useMutation({
    mutationFn: (payload) => createProject(workspaceSlug, payload),
    onSuccess: async (project) => {
      if (inviteEmail.trim()) {
        try {
          await inviteMember(workspaceSlug, {
            email: inviteEmail.trim(),
            role: 'member',
          })
        } catch {
          /* invite is best-effort in wizard */
        }
      }
      queryClient.invalidateQueries({ queryKey: ['projects', workspaceSlug] })
      queryClient.invalidateQueries({ queryKey: ['onboarding', workspaceSlug] })
      navigate(`/app/${workspaceSlug}/projects/${project.key}/board`)
    },
    onError: (err) => {
      const detail = err.response?.data
      setError(
        detail?.key?.[0] ||
          detail?.name?.[0] ||
          detail?.detail ||
          'Could not create project.',
      )
    },
  })

  const keyAvailable = keyCheckQuery.data?.available !== false
  const canContinueName =
    name.trim().length > 1 && key.length >= 2 && keyAvailable

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.key === templateKey),
    [templates, templateKey],
  )

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--text-muted)]">
        New project · Step {step + 1} of 4
      </p>
      <h1 className="mt-2 font-display text-3xl text-[var(--text)]">
        Create your project
      </h1>
      <p className="mt-2 text-sm text-[var(--text-secondary)]">
        Pick a template, name the project, then open the board.
      </p>

      {step === 0 ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {templates.map((tmpl) => {
            const active = tmpl.key === templateKey
            return (
              <button
                key={tmpl.key}
                type="button"
                onClick={() => setTemplateKey(tmpl.key)}
                className={[
                  'rounded-2xl border p-4 text-left transition',
                  active
                    ? 'border-[var(--accent)] bg-[var(--surface-1)] shadow-raised'
                    : 'border-[var(--border)] bg-[var(--surface-1)]',
                ].join(' ')}
              >
                <p className="font-medium text-[var(--text)]">{tmpl.name}</p>
                <p className="mt-2 text-sm text-[var(--text-secondary)]">
                  {tmpl.description}
                </p>
                <ul className="mt-3 space-y-1 text-xs text-[var(--text-muted)]">
                  <li>
                    Types: {(tmpl.includes?.issue_types || []).join(', ')}
                  </li>
                  <li>Board: {tmpl.includes?.board ? 'yes' : 'no'}</li>
                  <li>Backlog: {tmpl.includes?.backlog ? 'yes' : 'no'}</li>
                  <li>Sprints: {tmpl.includes?.sprints ? 'yes' : 'no'}</li>
                </ul>
              </button>
            )
          })}
        </div>
      ) : null}

      {step === 1 ? (
        <div className="mt-8 space-y-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
          <label className="block text-sm font-medium text-[var(--text)]">
            Project name
            <input
              className="mt-1 w-full rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-[var(--text)]">
            Key
            <input
              className="mt-1 w-full rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 font-mono uppercase"
              value={key}
              onChange={(e) => {
                setKeyTouched(true)
                setKey(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 16))
              }}
              required
            />
          </label>
          {key.length >= 2 ? (
            <p
              className={
                keyAvailable
                  ? 'text-xs text-[var(--accent-text,#347D78)]'
                  : 'text-xs text-[var(--danger)]'
              }
            >
              {keyCheckQuery.isFetching
                ? 'Checking availability…'
                : keyAvailable
                  ? `${key} is available`
                  : `${key} is already taken`}
            </p>
          ) : null}
          <p className="text-xs text-[var(--text-muted)]">
            Template: {selectedTemplate?.name || templateKey}
          </p>
        </div>
      ) : null}

      {step === 2 ? (
        <div className="mt-8 space-y-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
          <label className="block text-sm font-medium text-[var(--text)]">
            Project lead
            <select
              className="mt-1 w-full rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2"
              value={leadId}
              onChange={(e) => setLeadId(e.target.value)}
            >
              <option value="">Me (default)</option>
              {members.map((m) => (
                <option key={m.id} value={m.user?.id}>
                  {m.user?.full_name || m.user?.email}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium text-[var(--text)]">
            Default assignee
            <select
              className="mt-1 w-full rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2"
              value={defaultAssigneeId}
              onChange={(e) => setDefaultAssigneeId(e.target.value)}
            >
              <option value="">Unassigned</option>
              {members.map((m) => (
                <option key={m.id} value={m.user?.id}>
                  {m.user?.full_name || m.user?.email}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {step === 3 ? (
        <div className="mt-8 space-y-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
          <label className="block text-sm font-medium text-[var(--text)]">
            Invite a teammate (optional)
            <input
              type="email"
              className="mt-1 w-full rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2"
              placeholder="teammate@company.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
            />
          </label>
          <p className="text-sm text-[var(--text-secondary)]">
            They must already have a Nexus account. You can invite more people
            later from Members.
          </p>
        </div>
      ) : null}

      {error ? (
        <p className="mt-4 text-sm text-[var(--danger)]" role="alert">
          {error}
        </p>
      ) : null}

      <div className="mt-8 flex flex-wrap items-center gap-3">
        {step > 0 ? (
          <Button type="button" variant="ghost" onClick={() => setStep((s) => s - 1)}>
            Back
          </Button>
        ) : (
          <Link
            to={`/app/${workspaceSlug}/projects`}
            className="text-sm text-[var(--text-secondary)] underline"
          >
            Cancel
          </Link>
        )}
        {step < 3 ? (
          <Button
            type="button"
            disabled={step === 1 && !canContinueName}
            onClick={() => setStep((s) => s + 1)}
          >
            Continue
          </Button>
        ) : (
          <Button
            type="button"
            disabled={createMutation.isPending}
            onClick={() => {
              setError('')
              createMutation.mutate({
                name,
                key,
                template_key: templateKey,
                lead_id: leadId || undefined,
                default_assignee_id: defaultAssigneeId || null,
              })
            }}
          >
            {createMutation.isPending ? 'Creating…' : 'Open board'}
          </Button>
        )}
      </div>
    </div>
  )
}
