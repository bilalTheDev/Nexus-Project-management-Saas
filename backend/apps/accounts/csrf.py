"""CSRF defence for cookie-authenticated auth endpoints.

CORS is not a CSRF defence. Cross-origin credentialed requests still need:
1. A custom header that simple form POSTs cannot set without CORS preflight
   (`X-Requested-With`), and
2. An Origin (or Referer) check against the trusted allowlist.

SameSite decision (see docs/adr/0001-auth-sessions.md):
- Local DEBUG: SameSite=Lax (localhost ports are same-site).
- Production (Vercel SPA → PythonAnywhere API): SameSite=None; Secure so the
  refresh cookie is sent on cross-site XHR. That requires this CSRF layer.
"""

from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from rest_framework.exceptions import PermissionDenied


CSRF_HEADER_NAME = "HTTP_X_REQUESTED_WITH"
CSRF_HEADER_VALUE = "XMLHttpRequest"


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    allowed = set(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])
    allowed |= set(getattr(settings, "CORS_ALLOWED_ORIGINS", []) or [])
    if origin in allowed:
        return True
    # Allow exact match after stripping trailing slash noise.
    origin = origin.rstrip("/")
    return any(origin == item.rstrip("/") for item in allowed)


def _referer_origin(referer: str) -> str:
    if not referer:
        return ""
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def enforce_cookie_csrf(request) -> None:
    """Raise PermissionDenied unless the request looks like a deliberate XHR."""
    header = request.META.get(CSRF_HEADER_NAME, "")
    if header != CSRF_HEADER_VALUE:
        raise PermissionDenied(
            detail="Missing or invalid X-Requested-With header."
        )

    origin = request.META.get("HTTP_ORIGIN", "") or _referer_origin(
        request.META.get("HTTP_REFERER", "")
    )
    # Same-origin API tooling (no Origin) is allowed only when DEBUG and no
    # Origin/Referer were sent — browsers always send Origin on cross-site XHR.
    if not origin:
        if settings.DEBUG:
            return
        raise PermissionDenied(detail="Missing Origin header.")

    if not _origin_allowed(origin):
        raise PermissionDenied(detail="Origin not allowed.")
