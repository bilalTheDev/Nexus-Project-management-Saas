"""API v1 route registry. Feature routes will be added per milestone."""

from django.urls import include, path

from config.health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("", include("apps.accounts.urls")),
]
