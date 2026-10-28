# ADR 0002 — Multi-tenant isolation (application scoping vs Postgres RLS)

## Status

Accepted (Part B)

## Context

Nexus is a multi-workspace SaaS. Every project, issue, comment, sprint, release,
and activity row belongs to exactly one workspace. Broken object-level
authorization (IDOR) is the critical risk: a caller authenticated to workspace B
must not read or mutate workspace A resources by guessing UUIDs.

The database is **Neon Postgres**, typically reached through Neon's **pooled**
connection string (`DATABASE_URL`) for app traffic, with a direct
`DATABASE_URL_UNPOOLED` endpoint reserved for migrations. Connection pooling
(PgBouncer transaction mode / Neon's pooler) multiplexes many clients onto
shared backend connections.

## Decision

1. **Application-layer tenancy is the primary control.**
   - `WorkspaceScopedQuerySet.for_user(user)` filters by ACTIVE
     `WorkspaceMembership`.
   - `WorkspaceScopedMixin` and task/comment scoped mixins resolve objects only
     through those querysets.
   - Missing and forbidden object lookups both return **404** (no existence leak).
2. **DRF permissions** enforce role floors:
   - `IsWorkspaceMember`
   - `HasWorkspaceRole(min_role)`
   - `HasProjectRole(min_role)` wired via `apps/projects/policy.py` (`POLICY` /
     `can()`).
3. **Same-workspace FK validators** reject cross-tenant assignee / parent /
   sprint / project / label references at serializer time.
4. **Mass assignment**: serializers use explicit `fields` (+ `StrictFieldsMixin`);
   `id`, `workspace`, `created_by`, and timestamps are read-only where present.
5. **Ownership**: last-owner protection and ownership transfer run in
   `transaction.atomic()` with `select_for_update` (`apps/workspaces/services.py`).
6. **Postgres Row Level Security (RLS) is not enabled.**

### RLS evaluation (Neon pooling)

| Concern | Finding |
| --- | --- |
| Session GUCs (`SET app.workspace_id`) | Unreliable under transaction-pooling: the next checkout may be a different backend without the GUC. |
| `SET LOCAL` inside a transaction | Safer, but every request must open a transaction and re-apply before any query; easy to miss in admin, management commands, Celery, or raw SQL. |
| Pooler + RLS policies | Compatible only with careful session mode or per-transaction `SET LOCAL`; Neon's default pooled endpoint is optimized for short transactions, not sticky sessions. |
| Defence in depth value | Real, but only if 100% of DB access paths set the tenant context — including Django admin and one-off scripts. |

**Skip reason:** Until we can prove every request path (DRF, admin, migrate
data fixes, future workers) sets a transaction-local tenant GUC *and* we run
the app against a pooler mode that preserves that contract, RLS would give a
false sense of safety. Application scoping + generated IDOR tests are the
enforced boundary for now.

Revisit RLS when: (a) we adopt session pooling or direct connections for the
API process, (b) a middleware/`DatabaseWrapper` wrapper sets `SET LOCAL` on
every cursor, and (c) CI proves policies with a role that cannot bypass them.

## Consequences

- New endpoints must use scoped querysets; the URL-conf IDOR suite
  (`apps/workspaces/tests_idor.py`) fails CI if a UUID/workspace route returns
  200/403 to a foreign-tenant user.
- Do not call `Model.objects.all()` / unscoped `get()` for tenant models in
  views.
- Enabling Neon RLS later is additive — not a substitute for the above.
- Secrets (DB URLs, keys) stay out of this document and out of logs.
