# Deployment

Target stack: **Vercel** (frontend) · **PythonAnywhere** (Django) · **Neon** (PostgreSQL).

## Order of operations

1. Create Neon database; store `DATABASE_URL` in backend-only secrets (SSL as required).
2. Deploy Django on PythonAnywhere; configure WSGI, env vars, migrations, static files.
3. Verify `/healthz`, `/readyz`, and authenticated API smoke tests.
4. Deploy Vite app on Vercel with root `frontend/` and `VITE_API_BASE_URL` pointing at the PythonAnywhere API.
5. Confirm CORS, auth cookies/CSRF (when configured), CSP headers (`frontend/vercel.json`), and end-to-end journeys.

## Production settings checklist

- `DJANGO_DEBUG=False`
- Strong unique `DJANGO_SECRET_KEY` (not `django-insecure-*`)
- Separate `JWT_SIGNING_KEY`
- `DJANGO_ALLOWED_HOSTS` = real PythonAnywhere host
- `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` = real Vercel origin (never `*` with credentials)
- `SECURE_PROXY_SSL_HEADER_ENABLED=True` **only** on PythonAnywhere (or hosts that strip client `X-Forwarded-Proto`) so `SECURE_SSL_REDIRECT` / secure cookies see HTTPS correctly
- Optional: `SENTRY_DSN` (Sentry init uses `send_default_pii=False` + scrubber)
- Never put `DATABASE_URL` or Django secrets in frontend/`VITE_` variables

### HTTPS / HSTS notes

When `DJANGO_DEBUG=False`, Django enables SSL redirect, HSTS (`SECURE_HSTS_SECONDS`, default 1 year), secure cookies, `nosniff`, referrer policy, and `X_FRAME_OPTIONS=DENY`.

**HSTS preload caution:** leave `SECURE_HSTS_PRELOAD=False` unless you intentionally submit the host to the browser preload list. Preload is difficult to undo and requires every subdomain to serve HTTPS permanently.

## Neon connection pooling

| URL | Use |
| --- | --- |
| `DATABASE_URL` | App traffic — prefer Neon **pooled** endpoint |
| `DATABASE_URL_UNPOOLED` | `migrate` / `makemigrations` / `showmigrations` / `sqlmigrate` only |

### `CONN_MAX_AGE` / `CONN_HEALTH_CHECKS` (pooler-compatible)

Configured via Django `DATABASES["default"]` from `dj-database-url`:

| Situation | Recommended |
| --- | --- |
| Neon **transaction** pooler (`*-pooler.*` in host) | `DATABASE_CONN_MAX_AGE=0` (default when pooler host detected). Persistent Django conn caching fights the pooler. |
| Neon **session** pooler or **direct** host | Short age, e.g. `DATABASE_CONN_MAX_AGE=60`–`600`. Health checks enable automatically when age &gt; 0. |
| Migrations | Always `conn_max_age=0` (forced in settings). |

Override explicitly with `DATABASE_CONN_MAX_AGE` (seconds). Do not set a high `CONN_MAX_AGE` against a transaction-mode pooler.

## Neon PITR / branch restore

Neon continuous backups support point-in-time recovery (plan-dependent):

1. In Neon console, restore to a **new branch** at the chosen timestamp (prefer new branch over in-place surprise).
2. Point staging `DATABASE_URL` / `DATABASE_URL_UNPOOLED` at the restored branch; run `/readyz` and smoke tests.
3. Cut production URLs over only after verification; keep the previous branch until you confirm write traffic is healthy.
4. Re-run any required migrations if the restore point predates schema changes you still need.
5. Document the incident time window in the runbook notes (`docs/RUNBOOK.md`).

## Health probes

| Path | Meaning |
| --- | --- |
| `/healthz` | Process alive |
| `/readyz` | DB reachable + no pending migrations |
| `/api/v1/health/` | Legacy DB readiness |

## Frontend (Vercel)

- Project root: `frontend/`
- Security headers (CSP `script-src 'self'`, `frame-ancestors 'none'`, `connect-src` including API hosts) live in `frontend/vercel.json`
- After changing API origin, update CSP `connect-src` and redeploy

Detailed PythonAnywhere reload and troubleshooting steps: see `docs/RUNBOOK.md`.
