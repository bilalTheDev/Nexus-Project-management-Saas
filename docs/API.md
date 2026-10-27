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

## Projects, tasks, comments, activity

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET/POST | `/workspaces/{slug}/projects/` | List / create (`?archived=1`) |
| GET/PATCH | `/workspaces/{slug}/projects/{key}/` | Detail / update |
| POST | `/workspaces/{slug}/projects/{key}/archive/` | Archive |
| GET/POST | `/workspaces/{slug}/projects/{key}/tasks/` | Project tasks |
| GET | `/workspaces/{slug}/projects/{key}/board/` | Kanban columns |
| GET | `/workspaces/{slug}/my-tasks/` | Assignee filter |
| GET/PATCH | `/tasks/{id}/` | Task detail / update |
| PATCH | `/tasks/{id}/position/` | Status + fractional position |
| GET/POST | `/tasks/{id}/comments/` | Comments |
| DELETE | `/comments/{id}/` | Soft-delete comment |
| GET | `/workspaces/{slug}/activity/` | Activity feed |
| GET | `/workspaces/{slug}/activity/stats/` | Contributor stats |

All workspace-scoped queries require an active membership.
