"""API v1 route registry."""

from django.urls import include, path

from config.health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.workspaces.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.tasks.urls")),
    path("", include("apps.comments.urls")),
    path("", include("apps.activity.urls")),
]
