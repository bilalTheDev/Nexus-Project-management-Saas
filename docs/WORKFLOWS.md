# Workflow engine

Team-managed projects own their statuses and transitions. The board and issue moves are validated on the server.

## Models

- `WorkflowStatus(project, key, name, category, position)` — category is `todo`, `in_progress`, or `done`
- `Transition(project, from_status, to_status, name, validators[])`
- Optional validators: `require_assignee`, `require_resolution`, `require_comment`

## APIs

| Method | Path | Behaviour |
| --- | --- | --- |
| GET | `/workspaces/{slug}/projects/{key}/workflow/` | Statuses, issue types, transitions |
| GET | `/issues/{id}/transitions/` | Allowed moves from the current status |
| POST | `/issues/{id}/transitions/` | Apply a transition; `409` if invalid or version conflict |
| PATCH | `/issues/{id}/position/` | Rank/position; status changes require `transition_id` or a matching status pair |

Direct `status` field updates on PATCH `/issues/{id}/` are rejected.

## Templates

Fixtures live in `backend/apps/projects/fixtures/templates.json` (`scrum`, `kanban`, `bug_tracking`). Creating a project applies the template (issue types, statuses, transitions, board nav flags).

## Board behaviour

Columns map 1:1 to project statuses. A drag without a matching transition snaps back and shows the server error message.
