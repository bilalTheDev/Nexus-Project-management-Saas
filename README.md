# Nexus

Multi-tenant project management SaaS (portfolio MVP) built with **React + JavaScript**, **Django REST Framework**, and **PostgreSQL**.

Inspired by tools like Linear/Jira: workspaces, projects, Kanban tasks, comments, activity, and dashboards — with tenant isolation and production-minded deployment (Vercel + PythonAnywhere + Neon).

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React, Vite, JavaScript, TanStack Query, React Router, Tailwind CSS |
| Backend | Python 3.11+, Django, Django REST Framework, SimpleJWT |
| Database | PostgreSQL (Neon in production; SQLite optional for local bootstrap) |
| Hosting | Frontend → Vercel · Backend → PythonAnywhere · DB → Neon |

## Repository layout

```
frontend/     React + Vite + JavaScript app
backend/      Django modular monolith (config/ + apps/)
docs/         PRD, ERD, API, deployment notes
.github/      CI workflows
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Health check: [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/)

### Frontend

```bash
cd frontend
npm install
copy .env.example .env   # or: cp .env.example .env
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

## Current status

**M0 — Foundation** initialized:

- Monorepo with `frontend/` and `backend/`
- Vite React JavaScript scaffold + feature folder layout
- Django/DRF project with modular apps and custom `User` model
- Health endpoint, env examples, docs stubs, CI skeleton

Feature pages and domain APIs will be built in later milestones (auth → workspaces → projects → tasks).

## Documentation

- [docs/PRD.md](docs/PRD.md) — product requirements overview
- [docs/ERD.md](docs/ERD.md) — entity relationships (stub)
- [docs/API.md](docs/API.md) — API contract (stub)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — deploy runbook (stub)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — branching and commit conventions
