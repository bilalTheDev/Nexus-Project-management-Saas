from django.urls import path

from apps.tasks.views import (
    BoardTasksView,
    MyTasksView,
    ProjectTaskListCreateView,
    TaskDetailView,
    TaskPositionView,
)

urlpatterns = [
    path(
        "workspaces/<slug:slug>/projects/<str:project_key>/tasks/",
        ProjectTaskListCreateView.as_view(),
        name="project-tasks",
    ),
    path(
        "workspaces/<slug:slug>/projects/<str:project_key>/board/",
        BoardTasksView.as_view(),
        name="project-board",
    ),
    path(
        "workspaces/<slug:slug>/my-tasks/",
        MyTasksView.as_view(),
        name="my-tasks",
    ),
    path("tasks/<uuid:task_id>/", TaskDetailView.as_view(), name="task-detail"),
    path(
        "tasks/<uuid:task_id>/position/",
        TaskPositionView.as_view(),
        name="task-position",
    ),
]
