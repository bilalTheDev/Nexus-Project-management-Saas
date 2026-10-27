"""HttpOnly refresh-token cookie helpers."""

from django.conf import settings


REFRESH_COOKIE_NAME = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "nexus_refresh")


def set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=int(
            settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME").total_seconds()
        ),
        path="/api/v1/auth/",
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth/",
        samesite="Lax",
    )
