# Nexus PRD (overview)

Full planning specification: see `Nexus_Project_Management_SaaS_PRD_Updated_PythonAnywhere.pdf` (and the extracted `.txt`) in the repository root.

## Product

Nexus is a portfolio-grade, multi-tenant project management SaaS. Teams create workspaces, invite members, organize projects, manage tasks on a Kanban board, comment, and track progress via dashboards and activity.

## MVP scope

Authentication, workspaces & roles, projects, tasks (list + Kanban), comments, activity feed, basic dashboard, and a live deployed demo.

## Non-goals (v1)

Native mobile apps, enterprise SSO/billing, Slack/email integrations, AI planning, microservices, real-time WebSockets (polling/manual refresh is enough for MVP).

## Architecture summary

- Monorepo: `frontend/` (React + Vite + JS) and `backend/` (Django + DRF modular monolith)
- PostgreSQL via Neon in production
- Frontend on Vercel; backend on PythonAnywhere
- API prefix: `/api/v1/`
