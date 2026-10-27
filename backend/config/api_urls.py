"""API v1 route registry. Feature routes will be added per milestone."""

from django.urls import path

from config.health import health

urlpatterns = [
    path("health/", health, name="health"),
]
