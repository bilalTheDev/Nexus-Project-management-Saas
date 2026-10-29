# Nexus

Multi-tenant project management SaaS (portfolio MVP): workspaces, projects, workflow issues, Kanban, backlog, sprints, comments, activity, and dashboards — with cookie-based JWT auth and workspace-scoped isolation.

**Stack:** React (JSX) + Vite · Django 5 + DRF · PostgreSQL (Neon) · Vercel + PythonAnywhere

## What’s in the product

| Area | Status |
| --- | --- |
| Auth | Register / login / logout, HttpOnly refresh cookie, password reset, axes lockout |
| Workspaces | Create, switch, members & roles, ownership transfer |
| Invites | Email invite (console backend in DEBUG) + `/invite/:token` accept / signup flow |
| Projects | Templates (scrum / kanban / bug tracking), settings, lead & default assignee |
| Issues | Create, detail drawer, priority / assignee edit, optimistic board updates |
| Board | DnD columns from workflow, WIP hints, filters (mine / unassigned), light polling |
| Backlog & sprints | Backlog view, sprint lifecycle |
| Comments & activity | Mentions, activity feed, issue history |
| Dashboard | Workspace metrics, urgent work, project health |
| Reports / search | Project reports, issue navigator, global search |
| Notifications | In-app bell (assign, status, comments) |
| Onboarding | Checklist + guided tour |
| Themes | Light / dark product UI + marketing landing |

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React 19, Vite, JSX, TanStack Query, React Router, Tailwind 4, dnd-kit, Recharts |
| Backend | Python 3.11+, Django 5.2, DRF, SimpleJWT + blacklist, django-axes, Argon2 |
| Database | PostgreSQL on Neon (`DATABASE_URL` pooled; unpooled for migrations) |
| Hosting | Frontend → Vercel · API → PythonAnywhere · DB → Neon |
| Quality | GitHub Actions (ruff, bandit, pip-audit, gitleaks, Django tests, frontend build) |

## Repository layout

```
frontend/     React + Vite app (features/, lib/, e2e/)
backend/      Django modular monolith (config/ + apps/)
docs/         PRD, API, security ADRs, deployment, runbook, perf baseline
load/         k6 smoke script
.github/      CI + Dependabot
```

Backend apps: `accounts`, `workspaces`, `projects`, `tasks`, `comments`, `activity`.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: ruff, bandit, pip-audit
copy .env.example .env                # or: cp .env.example .env
# Set DATABASE_URL to Neon (recommended) or leave empty for local SQLite
python manage.py migrate
python manage.py seed_northstar       # optional demo workspace + users
python manage.py runserver
```

- API base: `http://127.0.0.1:8000/api/v1/`
- Health: `http://127.0.0.1:8000/healthz` · Ready: `http://127.0.0.1:8000/readyz`

**Demo seed (after `seed_northstar`):** `maya@northstar.studio` / `DemoPass1` (and other Northstar users with the same password). Portfolio demo only — not for production.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env                # VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
npm run dev
```

App: [http://127.0.0.1:5173](http://127.0.0.1:5173) (use the same host you put in `CORS_ALLOWED_ORIGINS` — `localhost` vs `127.0.0.1` are different origins).

### Useful commands

```bash
# Backend tests (SQLite like CI — clear Neon URLs in the shell if needed)
cd backend && python manage.py test

# Frontend
cd frontend && npm run lint && npm run build

# Perf load seed (20 projects / 2000 tasks) — optional
cd backend && python manage.py seed_perf_load
```

## Security highlights

- Access JWT in memory; refresh in HttpOnly cookie with rotation + blacklist
- Workspace-scoped querysets → foreign IDs return **404** (IDOR suite in CI)
- CORS / CSRF allowlists; production `SECURE_*` when `DJANGO_DEBUG=False`
- Never commit real `.env` / Neon credentials (only `*.env.example`)

Details: [docs/SECURITY.md](docs/SECURITY.md), [docs/adr/0001-auth-sessions.md](docs/adr/0001-auth-sessions.md), [docs/adr/0002-tenancy.md](docs/adr/0002-tenancy.md).

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/PRD.md](docs/PRD.md) | Product requirements |
| [docs/API.md](docs/API.md) | API surface |
| [docs/ERD.md](docs/ERD.md) | Data model |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | Issue workflows / templates |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Vercel / PythonAnywhere / Neon |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Ops / incident notes |
| [docs/PERF_BASELINE.md](docs/PERF_BASELINE.md) | Query & bundle baseline |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Branching & commits |

## Current status

Portfolio MVP is **feature-complete** for the delivery loop above (auth → workspace → project → board/issues → invites → notifications). Hardening Parts A–F (auth, tenancy, API, observability, CI gates) are in place. Follow-ups tracked in security/perf docs: optional TOTP, heavier board virtualization, and measured query/cache work from the perf baseline.
