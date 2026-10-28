# Nexus security model

**Standard:** defence in depth, rapid detection, fast recovery — not “unbreakable.”  
**Stack note:** Repo is Django + DRF + React/Vite/**JSX** (not TypeScript). Prompt mentions TypeScript; we do not migrate languages.

Secrets never appear in this document. Use placeholders: `<NEON_HOST>`, `<DJANGO_SECRET_KEY>`, etc.

---

## Step 0 — Deployment gate (Neon / PythonAnywhere)

| Check | Result |
| --- | --- |
| `DATABASE_URL` points at Neon (`*.neon.tech`) | Yes (agent env) |
| `sslmode=require` present in URL | Yes |
| `DATABASE_SSL_REQUIRE` default / env | `True` (settings pass `ssl_require=True` to `dj_database_url`) |
| TCP `create_connection((host, 5432), 5)` **from this agent** | **OK** |
| Same check **from a free PythonAnywhere console** | **Not run here** — you must verify on PA |

**Honest framing:** Free PythonAnywhere only allows outbound HTTP(S) to an allowlist; raw PostgreSQL on port 5432 often **fails** on free plans. If your PA console check fails, options are: paid PythonAnywhere (keep Neon) or host Django elsewhere. **Do not switch database.**

---

## Assets

| Asset | Sensitivity |
| --- | --- |
| User credentials & JWT refresh cookies | Critical |
| Access tokens (in-memory on client) | High |
| Workspace / project / issue data (multi-tenant) | Critical |
| Activity / notification / audit records | High |
| Neon database & backups | Critical |
| `DJANGO_SECRET_KEY` / future `SIGNING_KEY` | Critical |
| GitHub Actions secrets, Vercel/PA env | Critical |
| Demo seed passwords (dev only) | Medium (must never ship to prod) |

---

## Trust boundaries

```text
[Browser] --HTTPS--> [Vercel static SPA]
     |                      |
     | Bearer access        | no secrets in VITE_*
     | + cookie refresh     |
     v                      v
[PythonAnywhere Django/DRF] --TLS Postgres--> [Neon]
     ^
     | CI / git push
[GitHub]
```

| Boundary | Trust assumption |
| --- | --- |
| Browser | Untrusted; XSS steals what JS can reach |
| Vercel | Serves static assets only; env limited to public `VITE_*` |
| PythonAnywhere | Runs trusted app code; holds DB URL & secret key |
| Neon | Trusted data store; SSL required |
| GitHub | Trusted for source; compromised Actions = secret leak |

---

## Current controls (as of branch)

**Auth (Part A)**
- SimpleJWT + `token_blacklist`; refresh in HttpOnly cookie (`nexus_refresh`), access in memory
- Access TTL **10m**, refresh **7d**, rotate + blacklist; `JWT_SIGNING_KEY` separate from `DJANGO_SECRET_KEY`
- Cookie: HttpOnly; Secure when not DEBUG or SameSite=None; SameSite Lax (DEBUG) / None (prod); path `/api/v1/auth/`
- Cookie refresh/logout require `X-Requested-With` + trusted Origin (CORS ≠ CSRF)
- `django-axes` lockout (username+IP); auth throttle **5/min**; anon 30 / user 300
- Passwords: min 10, Django validators, Argon2 first; reset generic + revokes all refresh tokens
- Register duplicate email returns generic conflict (no enumeration)
- See `docs/adr/0001-auth-sessions.md`

**Authz / tenancy**
- Workspace membership checks (`IsWorkspaceMember`, `CanMutateWorkspaceContent`)
- Most list/create views scoped via `WorkspaceScopedMixin` + slug
- Project `policy.py` exists (Phase 3) but not fully wired into every view
- Issue `version` optimistic concurrency on some paths

**Other**
- CORS allowlist + credentials; CSRF trusted origins list
- CI: lint/build frontend; Django check, makemigrations --check, tests on SQLite
- Access token **not** in localStorage (theme preference only)

---

## STRIDE (summary)

| Boundary | Spoofing | Tampering | Repudiation | Info disclosure | DoS | Elevation |
| --- | --- | --- | --- | --- | --- | --- |
| Browser | XSS / stolen Bearer | Client-side only | Weak client audit | Tokens in memory / DOM XSS | N/A | Bypass UI guards |
| Vercel↔API | Origin spoof if CORS weak | — | — | Misconfigured `VITE_*` | Flood API | — |
| API | Stolen refresh / weak login | IDOR / mass assign | Mutable activity? | DEBUG / verbose errors | Unthrottled | Role confusion |
| Neon | Stolen DB URL | SQL via app bugs | — | Backup exposure | Exhaust compute | — |
| GitHub | Compromised token | Malicious PR | — | Secret in logs | — | Workflow inject |

---

## OWASP API Top 10 cross-check (selected)

| Risk | Status |
| --- | --- |
| Broken object level authorization | **Gap** — not every object lookup is membership-scoped identically (e.g. cross-link by UUID); no generated IDOR matrix |
| Broken authentication | **Partial** — cookie JWT good start; access TTL 30m; no axes; no separate signing key; refresh CSRF weak |
| Broken object property level | **Partial** — explicit serializer fields common; not audited everywhere; no unknown-field reject |
| Unrestricted resource consumption | **Gap** — no global anon/user throttles; board can return large payloads; page size not hard-capped at 100 everywhere |
| Security misconfiguration | **Gap** — DEBUG defaults True; no HSTS/CSP/`check --deploy` in CI; no `vercel.json` security headers |
| SSRF / unsafe consumption | Low today (few outbound calls) |
| Unsafe inventory | Partial OpenAPI (spectacular) without CI drift fail |

---

## Gaps by severity

### Critical
1. **Tenant IDOR surface** — Object fetches by UUID (issues, comments, links) must always resolve through workspace-scoped querysets; missing systematic tests per URL pattern.
2. **Production defaults unsafe** — `DJANGO_DEBUG` defaults True; missing `SECURE_*` / HSTS / SSL redirect when deployed.

### High
3. **Refresh cookie CSRF** — Cookie-based `/auth/token/refresh/` lacks custom header + origin check (CORS ≠ CSRF).
4. **Cross-site cookie risk** — `SameSite=Lax` may drop refresh on some cross-site POSTs from Vercel→PA; `None` needs Secure + CSRF plan (document before changing).
5. **Auth hardening incomplete** — No `django-axes`; access lifetime 30m (target 10m); no `SIGNING_KEY` separate from `SECRET_KEY`; password min 8 vs 10+; no Argon2 first hasher.
6. **Password reset** — Does not revoke refresh tokens; `?debug=1` can return reset tokens (must never enable in prod).

### Medium
7. **Authorization matrix not enforced uniformly** — `policy.py` / project roles exist but views still mostly use coarse workspace mutate roles.
8. **API limits** — No `max_page_size`; weak default throttles; no consistent error envelope; Browsable API / renderers not locked to JSON in prod.
9. **CI/CD security gates missing** — No bandit, pip-audit, gitleaks, semgrep, CodeQL, `check --deploy`, secret-in-dist scan, Dependabot.
10. **Observability / recovery** — No request-id logs, `/readyz`, Sentry scrubbing, RUNBOOK, backup restore drill, CSP.

### Low
11. Register email enumeration (`email already exists`).
12. No Idempotency-Key store; fractional rank rebalance not scheduled.
13. ActivityEvent not proven append-only at DB/admin layer.
14. Markdown rendering without DOMPurify (when rich text ships).

---

## Residual accepted (for now)

- Free-tier host CPU/cold-start limits — document after measurement.
- Optional RLS on Neon — evaluate against pooler; not assumed.
- Optional TOTP for Owner/Admin — P1.
