# Nexus operations runbook

Secrets never appear in this document. Use placeholders and platform secret stores only.

## Database down (Neon unreachable)

1. Confirm from PythonAnywhere / host: can the app resolve `<NEON_HOST>` and open TLS to Postgres?
2. Check Neon console: project suspended, branch deleted, compute asleep, or IP allowlist changed?
3. Prefer **pooled** `DATABASE_URL` for app traffic; use `DATABASE_URL_UNPOOLED` only for migrations.
4. Confirm `DATABASE_SSL_REQUIRE=True` and `sslmode=require` on the URL.
5. Hit `/readyz` — expect `503` with `checks.database=unavailable` (no stack traces).
6. If Neon is healthy but PA free-tier blocks outbound Postgres, upgrade PA or move the API host — **do not** switch off Neon.
7. After restore: re-check `/readyz`, then a single authenticated API smoke call.

## Auth spike / lockouts

Symptoms: many `401`/`429`, axes lockouts, user reports of “too many attempts.”

1. Inspect structured logs for `request_id`, path `/api/v1/auth/*`, status `429` / `401` (tokens/passwords/emails are redacted).
2. Confirm throttles: anon `30/min`, user `300/min`, auth scope `5/min` (prod).
3. django-axes: cooloff is `AXES_COOLOFF_MINUTES` (default 15); lockout is username+IP.
4. If legitimate traffic (launch, shared NAT): temporarily raise auth throttle / cooloff via env, then revert.
5. If abuse: block offending IPs at the host/WAF; rotate `JWT_SIGNING_KEY` if refresh cookies may be stolen (see below).
6. Optional Sentry: filter by `SENTRY_ENVIRONMENT`; PII scrubber keeps emails/tokens out of events.

## Bad / stuck migration

1. **Never** run `migrate` against the Neon pooler in transaction mode — use `DATABASE_URL_UNPOOLED` (direct).
2. From the API host: `python manage.py showmigrations` then `python manage.py migrate`.
3. If a migration failed mid-way: fix forward (prefer a new migration) over `migrate --fake` unless you understand the DB state.
4. `/readyz` reports `migrations=pending` until the plan is empty — useful as a deploy gate.
5. Neon **PITR / branch restore**: restore to a new branch, point `DATABASE_URL*` at it, verify, then cut over. See `docs/DEPLOYMENT.md`.

## Rotate keys

| Secret | Steps |
| --- | --- |
| `DJANGO_SECRET_KEY` | Generate new value → set on PA → reload WSGI. Sessions/signed cookies invalidate. |
| `JWT_SIGNING_KEY` | Set new value → reload. Existing access+refresh tokens fail verification; users re-login. Prefer rotating JWT key independently of Django secret. |
| Neon DB password | Rotate in Neon → update `DATABASE_URL` / `DATABASE_URL_UNPOOLED` on PA → reload. |
| Vercel `VITE_*` | Public only — never put secrets here. Redeploy after origin/API URL changes. |

After rotation: smoke login, refresh cookie, and one workspace-scoped GET.

## Revoke sessions

1. **Password reset** (user-driven) blacklists refresh tokens for that user (Part A behavior).
2. **Global**: rotate `JWT_SIGNING_KEY` (invalidates all JWTs) and/or flush SimpleJWT blacklist/outstanding tables after key rotation if you need a clean slate.
3. Clear `nexus_refresh` cookies by logging out (`POST` refresh/logout with CSRF header + trusted Origin).
4. Confirm axes unlock only after cooloff or deliberate admin reset — do not casually disable axes in prod.

## Breach checklist

1. **Contain** — rotate `JWT_SIGNING_KEY` and `DJANGO_SECRET_KEY`; rotate Neon credentials; invalidate sessions (above).
2. **Preserve** — export recent app logs (request IDs) and Neon/ops audit trails before wiping anything.
3. **Scope** — which envs/hosts had the secret? Vercel env? GitHub Actions? Developer machines?
4. **Access** — review Neon roles, PA account, GitHub org tokens, Vercel team; revoke unknown keys.
5. **Data** — if DB dump leaked: notify stakeholders per policy; consider Neon PITR to a known-good point **only** after understanding write loss.
6. **Hardening** — confirm `DJANGO_DEBUG=False`, `SECURE_*`, CSP (`django-csp` + `frontend/vercel.json`), CORS allowlist (no `*` with credentials).
7. **Follow-up** — file incident notes; add regression tests/CI gates for the failure mode.

## Quick health probes

| Probe | Expect |
| --- | --- |
| `GET /healthz` | `200` `{"status":"ok"}` — process up |
| `GET /readyz` | `200` when DB + migrations OK; else `503` |
| `GET /api/v1/health/` | Legacy readiness (DB only) |
