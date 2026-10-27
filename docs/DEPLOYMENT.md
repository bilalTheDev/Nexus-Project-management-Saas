# Deployment

Target stack: **Vercel** (frontend) · **PythonAnywhere** (Django) · **Neon** (PostgreSQL).

## Order of operations

1. Create Neon database; store `DATABASE_URL` in backend-only secrets (SSL as required).
2. Deploy Django on PythonAnywhere; configure WSGI, env vars, migrations, static files.
3. Verify `/api/v1/health/` and authenticated API smoke tests.
4. Deploy Vite app on Vercel with root `frontend/` and `VITE_API_BASE_URL` pointing at the PythonAnywhere API.
5. Confirm CORS, auth cookies/CSRF (when configured), and end-to-end journeys.

## Production settings checklist

- `DJANGO_DEBUG=False`
- Strong unique `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` = real PythonAnywhere host
- `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` = real Vercel origin
- Never put `DATABASE_URL` or Django secrets in frontend/`VITE_` variables

Detailed PythonAnywhere reload, migration, and troubleshooting steps will be filled in when first deploying (M7).
