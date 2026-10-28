# ADR 0001 — Authentication and session tokens

## Status

Accepted (Part A)

## Context

Nexus is a SPA on Vercel calling a Django API on PythonAnywhere. Access tokens in
`localStorage` are easy XSS prey. Refresh tokens in JSON bodies are easy to
exfiltrate. Cross-site cookie sessions need an explicit CSRF plan because CORS
is not a CSRF defence.

## Decision

1. **SimpleJWT** with `token_blacklist`. Access lifetime **10 minutes**, refresh
   **7 days**, rotate + blacklist on refresh, update last login.
2. **`JWT_SIGNING_KEY`** from its own environment variable (falls back to
   `DJANGO_SECRET_KEY` only in local/dev if unset). Rotate independently.
3. **Refresh token** lives in an HttpOnly cookie (`nexus_refresh`), path
   `/api/v1/auth/`. Response JSON returns **access only**. The SPA keeps access
   in memory.
4. **SameSite**
   - `DEBUG=True`: `Lax` (localhost Vite + API are same-site).
   - Production: `None` + `Secure` so credentialed cross-site POSTs from Vercel
     include the cookie. Override with `JWT_REFRESH_COOKIE_SAMESITE`.
5. **CSRF for cookie endpoints** (`/auth/token/refresh/`, `/auth/logout/`):
   require `X-Requested-With: XMLHttpRequest` **and** `Origin`/`Referer` in
   `CSRF_TRUSTED_ORIGINS` ∪ `CORS_ALLOWED_ORIGINS`. Simple HTML forms cannot set
   the custom header without a CORS preflight the API will reject from foreign
   origins.
6. **Brute force**: `django-axes` lockout on username+IP; DRF `auth` scope
   throttle **5/minute** on login, register, password-reset, refresh, logout.
7. **Passwords**: min length 10, Django validators, **Argon2** first hasher.
8. **Password reset**: generic responses; Django’s timed single-use token;
   blacklists **all** outstanding refresh tokens on confirm. Debug uid/token in
   JSON only when `DEBUG` and `ALLOW_PASSWORD_RESET_DEBUG=True`.
9. **TOTP 2FA** for Owner/Admin is deferred (P1).

## Consequences

- Frontend must send `X-Requested-With` and `withCredentials: true` on refresh.
- Production must set distinct `JWT_SIGNING_KEY`, HTTPS, and exact CORS/CSRF
  origin lists (never `*`).
- Axes migrations are required on every environment.
