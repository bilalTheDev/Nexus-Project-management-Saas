import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchMemberStats,
  fetchMembers,
  inviteMember,
  updateMemberRole,
  unwrapList,
} from '@/lib/workspace-api'

const ROLE_FILTERS = [
  { id: 'all', label: 'All Roles', param: undefined },
  { id: 'owner_admin', label: 'Owner & Admin', param: 'owner_admin' },
  { id: 'project_manager', label: 'Project Manager', param: 'project_manager' },
  { id: 'member', label: 'Member', param: 'member' },
]

export function MembersPage() {
  const { workspaceSlug } = useParams()
  const { user } = useAuth()
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteResult, setInviteResult] = useState(null)
  const queryClient = useQueryClient()

  const params = useMemo(() => {
    const next = {}
    const role = ROLE_FILTERS.find((r) => r.id === roleFilter)?.param
    if (role) next.role = role
    if (statusFilter !== 'all') next.status = statusFilter
    if (search.trim()) next.search = search.trim()
    return next
  }, [roleFilter, statusFilter, search])

  const membersQuery = useQuery({
    queryKey: ['members', workspaceSlug, params],
    queryFn: () => fetchMembers(workspaceSlug, params),
  })
  const statsQuery = useQuery({
    queryKey: ['member-stats', workspaceSlug],
    queryFn: () => fetchMemberStats(workspaceSlug),
  })

  const roleMutation = useMutation({
    mutationFn: ({ id, role }) => updateMemberRole(workspaceSlug, id, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', workspaceSlug] })
      queryClient.invalidateQueries({ queryKey: ['member-stats', workspaceSlug] })
    },
  })

  const inviteMutation = useMutation({
    mutationFn: (payload) => inviteMember(workspaceSlug, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['members', workspaceSlug] })
      queryClient.invalidateQueries({ queryKey: ['member-stats', workspaceSlug] })
      setInviteOpen(false)
      setInviteResult(data)
    },
  })

  const members = unwrapList(membersQuery.data)
  const stats = statsQuery.data

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
        Workspace / {workspaceSlug} / Members & Access
      </p>
      <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display text-3xl text-ink sm:text-4xl">
          Team Members
        </h1>
        <div className="flex gap-2">
          <Button variant="secondary" type="button">
            Export CSV
          </Button>
          <Button type="button" onClick={() => setInviteOpen(true)}>
            + Invite Member
          </Button>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="Active Seats"
          value={`${stats?.active_seats ?? '—'} / ${stats?.seat_limit ?? 12}`}
        />
        <Stat
          label="Workspace Admins"
          value={`${stats?.workspace_admins ?? '—'} members`}
        />
        <Stat
          label="Pending Invites"
          value={`${stats?.pending_invites ?? '—'} pending`}
        />
        <Stat
          label="Security Tier"
          value={stats?.security_tier || 'Standard'}
          accent
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <input
          type="search"
          placeholder="Search members by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[220px] flex-1 rounded-md border border-border bg-paper px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
        />
        {ROLE_FILTERS.map((filter) => (
          <button
            key={filter.id}
            type="button"
            onClick={() => setRoleFilter(filter.id)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium ${
              roleFilter === filter.id
                ? 'bg-ink text-paper'
                : 'bg-surface-low text-ink-secondary'
            }`}
          >
            {filter.label}
          </button>
        ))}
        <select
          className="rounded-md border border-border bg-paper px-2 py-1.5 text-xs"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Status filter"
        >
          <option value="all">All</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      <div className="mt-4 overflow-x-auto rounded-xl border border-border bg-paper">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-border bg-surface-low/60 text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Project Access</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {members.map((membership) => {
              const isYou = membership.user?.id === user?.id
              const isOwner = membership.role === 'owner'
              return (
                <tr key={membership.id} className="align-top">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-mint text-xs font-semibold text-brand">
                        {initials(membership.user)}
                      </div>
                      <div>
                        <p className="font-medium text-ink">
                          {membership.user?.full_name || membership.user?.email}
                          {isYou ? (
                            <span className="ml-2 rounded bg-surface-low px-1.5 py-0.5 text-[10px] text-ink-muted">
                              You
                            </span>
                          ) : null}
                        </p>
                        <p className="text-xs text-ink-muted">
                          {membership.user?.email}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {isOwner ? (
                      <span className="text-sm text-ink">Owner (Locked)</span>
                    ) : (
                      <select
                        className="rounded-md border border-border bg-surface px-2 py-1 text-sm"
                        value={membership.role}
                        onChange={(e) =>
                          roleMutation.mutate({
                            id: membership.id,
                            role: e.target.value,
                          })
                        }
                      >
                        <option value="admin">Workspace Admin</option>
                        <option value="project_manager">Project Manager</option>
                        <option value="member">Member</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    )}
                  </td>
                  <td className="px-4 py-3 text-ink-secondary">
                    {membership.project_access_count != null
                      ? `${membership.project_access_count} projects`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5 text-sm">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          membership.status === 'active'
                            ? 'bg-green-600'
                            : 'bg-stone-400'
                        }`}
                      />
                      {membership.status === 'active'
                        ? 'Active'
                        : 'Pending Invite'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-ink-muted">
                    {membership.joined_at
                      ? new Date(membership.joined_at).toLocaleDateString(
                          undefined,
                          { month: 'short', year: 'numeric' },
                        )
                      : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <p className="border-t border-border px-4 py-3 text-xs text-ink-muted">
          Showing {members.length} team accounts
        </p>
      </div>

      <div className="mt-6 rounded-xl border border-border bg-paper p-5">
        <h2 className="font-display text-xl text-ink">
          Workspace Ownership & Transfer
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-secondary">
          The workspace owner holds billing and domain governance responsibility.
          Current Sovereign:{' '}
          <span className="font-medium text-ink">
            {members.find((m) => m.role === 'owner')?.user?.email || '—'}
          </span>
        </p>
        <Button type="button" variant="secondary" className="mt-4">
          Transfer Ownership
        </Button>
      </div>

      {inviteOpen ? (
        <InviteModal
          onClose={() => setInviteOpen(false)}
          pending={inviteMutation.isPending}
          error={inviteMutation.error?.response?.data}
          onSubmit={(payload) => inviteMutation.mutate(payload)}
        />
      ) : null}

      {inviteResult ? (
        <InviteSuccessModal
          result={inviteResult}
          onClose={() => setInviteResult(null)}
        />
      ) : null}
    </div>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-border bg-paper p-4">
      <p className="text-xs uppercase tracking-wide text-ink-muted">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${accent ? 'text-brand' : 'text-ink'}`}>
        {value}
      </p>
    </div>
  )
}

function initials(user) {
  const name = user?.full_name || user?.email || '?'
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function InviteModal({ onClose, onSubmit, pending, error }) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('member')
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <form
        className="w-full max-w-md rounded-xl border border-border bg-surface p-6"
        role="dialog"
        aria-modal="true"
        aria-label="Invite member"
        onSubmit={(e) => {
          e.preventDefault()
          onSubmit({ email, role })
        }}
      >
        <h2 className="font-display text-2xl text-ink">Invite Member</h2>
        <p className="mt-1 text-sm text-ink-secondary">
          We&apos;ll email an invite link. New teammates can sign up from that link.
        </p>
        <label className="mt-4 block text-sm">
          Email
          <input
            type="email"
            required
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="mt-3 block text-sm">
          Role
          <select
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="admin">Workspace Admin</option>
            <option value="project_manager">Project Manager</option>
            <option value="member">Member</option>
            <option value="viewer">Viewer</option>
          </select>
        </label>
        {error ? (
          <p className="mt-2 text-sm text-red-700" role="alert">
            {error.email?.[0] || error.detail || 'Invite failed.'}
          </p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? 'Inviting…' : 'Send Invite'}
          </Button>
        </div>
      </form>
    </div>
  )
}

function InviteSuccessModal({ result, onClose }) {
  const [copied, setCopied] = useState(false)
  const url = result?.invite_url || ''

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <div
        className="w-full max-w-md rounded-xl border border-border bg-surface p-6"
        role="dialog"
        aria-modal="true"
        aria-label="Invite created"
      >
        <h2 className="font-display text-2xl text-ink">Invite sent</h2>
        <p className="mt-2 text-sm text-ink-secondary">
          {result?.email_sent
            ? `Email queued for ${result.email}.`
            : `Invite created for ${result.email}. Email was not delivered — copy the link below (dev: check the Django console for the message).`}
        </p>
        <label className="mt-4 block text-sm">
          Invite link
          <input
            readOnly
            className="mt-1 w-full rounded-md border border-border bg-paper px-3 py-2 font-mono text-xs"
            value={url}
            onFocus={(e) => e.target.select()}
          />
        </label>
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={copyLink}>
            {copied ? 'Copied' : 'Copy link'}
          </Button>
          <Button type="button" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}
