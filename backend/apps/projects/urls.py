from django.urls import path

from apps.projects.views import (
    ProjectArchiveView,
    ProjectDetailView,
    ProjectListCreateView,
)

urlpatterns = [
    path(
        "workspaces/<slug:slug>/projects/",
        ProjectListCreateView.as_view(),
        name="project-list",
    ),
    path(
        "workspaces/<slug:slug>/projects/<str:project_key>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "workspaces/<slug:slug>/projects/<str:project_key>/archive/",
        ProjectArchiveView.as_view(),
        name="project-archive",
    ),
]
