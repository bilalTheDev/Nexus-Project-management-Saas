# ADR 0002 — Tenant isolation

## Status

Accepted (Part B in progress)

## Decision

1. Every tenant queryset uses `WorkspaceScopedQuerySet.for_user(request.user)` (ACTIVE membership only).
2. Object retrieval goes through scoped querysets so cross-tenant IDs return **404**, not 403.
3. FK validators ensure assignee/parent/sprint/project belong to the same workspace.
4. Ownership transfer and last-owner protection live in `apps.workspaces.services` under `select_for_update()`.
5. **PostgreSQL RLS** is **not** enabled yet: Neon’s pooled connections make `SET LOCAL app.current_workspace` per-request fragile unless using a non-pooled session or proven pooler support. Revisit after a dedicated pooler/session test; document before adopting.

## Consequences

- Views must not call bare `Model.objects.all()` on tenant models.
- IDOR regression suite should iterate URL conf so new routes cannot skip coverage.
