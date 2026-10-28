# API contract

Prefix: `/api/v1/`. JSON request/response. Auth: Bearer access token + HttpOnly `nexus_refresh` cookie.

## Health & auth

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health/` | Readiness |
| POST | `/auth/register/` | Register; sets refresh cookie |
| POST | `/auth/token/` | Login; sets refresh cookie |
| POST | `/auth/token/refresh/` | Rotate refresh cookie; return access |
| POST | `/auth/logout/` | Blacklist refresh; clear cookie |
| GET/PATCH | `/users/me/` | Current user |

## Workspaces & members

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET/POST | `/workspaces/` | List / create |
| GET/PATCH | `/workspaces/{slug}/` | Detail / update |
| GET | `/workspaces/{slug}/dashboard/` | Overview aggregates |
| GET/POST | `/workspaces/{slug}/members/` | List / invite by email |
| GET | `/workspaces/{slug}/members/stats/` | Seat metrics |
| PATCH/DELETE | `/workspaces/{slug}/members/{id}/` | Role update / soft-remove |
| POST | `/workspaces/{slug}/transfer-ownership/` | Ownership transfer |

## Projects, issues, workflow, comments, activity

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/project-templates/` | Scrum / Kanban / Bug tracking fixtures |
| GET/POST | `/workspaces/{slug}/projects/` | List / create (`template_key`, `?archived=1`) |
| GET | `/workspaces/{slug}/projects/key-check/?key=` | Live key uniqueness |
| GET/PATCH | `/workspaces/{slug}/projects/{key}/` | Detail / update |
| POST | `/workspaces/{slug}/projects/{key}/archive/` | Archive |
| GET | `/workspaces/{slug}/projects/{key}/workflow/` | Statuses, types, transitions |
| GET/POST | `/workspaces/{slug}/projects/{key}/issues/` | Project issues (alias: `/tasks/`) |
| GET | `/workspaces/{slug}/projects/{key}/board/` | Columns keyed by workflow status |
| GET | `/workspaces/{slug}/projects/{key}/backlog/` | Backlog + future/active sprints |
| GET/POST | `/workspaces/{slug}/projects/{key}/sprints/` | Sprint list / create |
| POST | `/workspaces/{slug}/projects/{key}/sprints/{id}/start/` | Start sprint (one active) |
| POST | `/workspaces/{slug}/projects/{key}/sprints/{id}/complete/` | Complete; move incomplete |
| GET/PATCH | `/workspaces/{slug}/onboarding/` | Checklist + guided tour flags |
| GET/PATCH | `/issues/{id}/` | Issue detail / update (`version` → 409) |
| GET/POST | `/issues/{id}/transitions/` | Allowed moves / apply (409 if invalid) |
| GET | `/issues/{id}/history/` | Append-only `IssueChange` rows |
| GET/POST | `/issues/{id}/links/` | Bidirectional issue links |
| PATCH | `/issues/{id}/position/` | Rank + transition-backed status move |
| PATCH | `/issues/{id}/rank/` | Backlog/sprint ranking |
| GET/POST | `/tasks/{id}/comments/` | Comments (`@email` mentions) |
| DELETE | `/comments/{id}/` | Soft-delete comment |
| GET | `/workspaces/{slug}/activity/` | Activity feed |
| GET | `/workspaces/{slug}/activity/stats/` | Contributor stats |

All workspace-scoped queries require an active membership. Direct status field writes are rejected — use transitions.
