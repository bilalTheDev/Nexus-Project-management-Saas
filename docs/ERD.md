# Entity relationship design

## Core entities

- **User** — Django `AUTH_USER_MODEL` (email-first)
- **Workspace** — tenant boundary (`slug` unique, UUID PK)
- **WorkspaceMembership** — user ↔ workspace + role/status (`owner|admin|project_manager|member|viewer`)
- **Project** — belongs to one workspace (`key` unique per workspace)
- **Task** — belongs to one project; status, priority, assignee, fractional `position`, numeric `number` → `{KEY}-{n}`
- **Comment** — belongs to one task (soft delete via `deleted_at`)
- **ActivityEvent** — workspace-scoped timeline entries (sanitized JSON metadata)

## Relationships

```
User 1─* WorkspaceMembership *─1 Workspace
Workspace 1─* Project 1─* Task 1─* Comment
Workspace 1─* ActivityEvent
User optionally assigned to Task / lead of Project / actor on ActivityEvent
```
