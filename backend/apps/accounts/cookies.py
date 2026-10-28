"""HttpOnly refresh-token cookie helpers."""

from django.conf import settings


REFRESH_COOKIE_NAME = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "nexus_refresh")


def refresh_cookie_samesite() -> str:
    """
    Lax locally (same-site localhost). None in production so Vercel→API
    credentialed POSTs include the cookie. Override via JWT_REFRESH_COOKIE_SAMESITE.
    """
    configured = getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", None)
    if configured:
        return configured
    return "Lax" if settings.DEBUG else "None"


def set_refresh_cookie(response, refresh_token: str) -> None:
    samesite = refresh_cookie_samesite()
    # SameSite=None requires Secure; always Secure when not DEBUG.
    secure = (not settings.DEBUG) or samesite == "None"
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=int(
            settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME").total_seconds()
        ),
        path="/api/v1/auth/",
    )


def clear_refresh_cookie(response) -> None:
    samesite = refresh_cookie_samesite()
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth/",
        samesite=samesite,
    )
