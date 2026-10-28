# Nexus PRD (overview)

Full planning specification: see `Nexus_Project_Management_SaaS_PRD_Updated_PythonAnywhere.pdf` (and the extracted `.txt`) in the repository root.

## Product

Nexus is a portfolio-grade, multi-tenant project management SaaS. Teams create workspaces, invite members, organize projects, manage tasks on a Kanban board, comment, and track progress via dashboards and activity.

## MVP scope

Authentication, workspaces & roles, projects, tasks (list + Kanban), comments, activity feed, basic dashboard, and a live deployed demo.

## Built (Phase 1 — Jira-equivalent core)

- Project templates (Scrum / Kanban / Bug tracking) from fixtures
- Issue types + parent hierarchy (Epic → Story/Task/Bug → Sub-task)
- Workflow statuses + transitions with server-side 409 on invalid moves
- Backlog + sprint lifecycle (create / start / complete + snapshots)
- Board columns from project statuses; optimistic DnD with rollback toasts
- Issue drawer with transitions, comments (@mentions), history, version conflicts
- Onboarding checklist + guided tour (server-backed) + Ctrl/Cmd+K palette
- See `docs/WORKFLOWS.md`

## Deferred

- Phase 2: Recharts reports, issue navigator / query language, global search depth
- Phase 3: Releases, components, project roles/`policy.py`, notifications
- Attachments storage, `@xyflow` workflow canvas, full Playwright suite in CI
- i18next message catalogue (strings still inline for Phase 1)

## Non-goals (v1)

Native mobile apps, enterprise SSO/billing, Slack/email integrations, AI planning, microservices, real-time WebSockets (polling/manual refresh is enough for MVP).

## Architecture summary

- Monorepo: `frontend/` (React + Vite + JS) and `backend/` (Django + DRF modular monolith)
- PostgreSQL via Neon in production
- Frontend on Vercel; backend on PythonAnywhere
- API prefix: `/api/v1/`
