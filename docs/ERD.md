# Entity relationship design

Stub — expand during M1+ as models land.

## Core entities (planned)

- **User** — Django `AUTH_USER_MODEL` (custom, email-first)
- **Workspace** — tenant boundary (`slug` unique)
- **WorkspaceMembership** — user ↔ workspace + role/status
- **Project** — belongs to one workspace (`key` unique per workspace)
- **Task** — belongs to one project; status, priority, assignee, position
- **Comment** — belongs to one task
- **ActivityEvent** — workspace-scoped timeline entries

See the PRD §10 for fields, constraints, and relationship rules.
