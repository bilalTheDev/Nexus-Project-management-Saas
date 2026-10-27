# API contract

Prefix: `/api/v1/`. JSON request/response. Full OpenAPI via `drf-spectacular` once feature endpoints exist.

## Available now

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health/` | Readiness; reports DB reachability without leaking secrets |

## Planned (see PRD §11)

Auth (`/auth/...`), users (`/users/me/`), workspaces, members, projects, tasks, comments, activity, dashboard, my-tasks.
