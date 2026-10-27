from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.tasks.serializers import (
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskPositionSerializer,
    TaskUpdateSerializer,
)
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import (
    CanMutateWorkspaceContent,
    IsWorkspaceMember,
    get_membership,
)


class ProjectTaskListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get_project(self):
        return get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
            archived_at__isnull=True,
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer
        return TaskListSerializer

    def get_queryset(self):
        project = self.get_project()
        return (
            Task.objects.filter(project=project, archived_at__isnull=True)
            .select_related("assignee", "reporter", "project", "created_by")
            .order_by("status", "position", "created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["project"] = self.get_project()
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.TASK_CREATED,
            actor=request.user,
            project=task.project,
            task=task,
            summary=f"Created {task.task_key}",
        )
        return Response(
            TaskDetailSerializer(task).data, status=status.HTTP_201_CREATED
        )


class BoardTasksView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        tasks = (
            Task.objects.filter(project=project, archived_at__isnull=True)
            .select_related("assignee", "reporter", "project")
            .order_by("position", "created_at")
        )
        status_filter = request.query_params.get("status")
        priority = request.query_params.get("priority")
        assignee = request.query_params.get("assignee")
        search = request.query_params.get("search")
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        if priority:
            tasks = tasks.filter(priority=priority)
        if assignee:
            tasks = tasks.filter(assignee_id=assignee)
        if search:
            tasks = tasks.filter(title__icontains=search)
        columns = {key: [] for key, _ in Task.Status.choices}
        for task in tasks:
            columns[task.status].append(TaskListSerializer(task).data)
        return Response(
            {
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "key": project.key,
                    "status": project.status,
                },
                "columns": columns,
            }
        )


class TaskScopedMixin:
    """Resolve workspace from task_id before permission checks."""

    def initial(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.select_related("project", "project__workspace"),
            pk=kwargs.get("task_id") or self.kwargs.get("task_id"),
            archived_at__isnull=True,
        )
        self.task = task
        self.workspace = task.project.workspace
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise PermissionDenied("You are not a member of this workspace.")
        super().initial(request, *args, **kwargs)


class TaskDetailView(TaskScopedMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def get_object(self):
        return get_object_or_404(
            Task.objects.select_related(
                "assignee", "reporter", "project", "project__workspace", "created_by"
            ),
            pk=self.kwargs["task_id"],
            archived_at__isnull=True,
        )

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        old_status = task.status
        old_assignee = task.assignee_id
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        if updated.status != old_status:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_STATUS_CHANGED,
                actor=request.user,
                project=updated.project,
                task=updated,
                summary=f"Transitioned {updated.task_key}",
                metadata={"from": old_status, "to": updated.status},
            )
        elif updated.assignee_id != old_assignee:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_ASSIGNED,
                actor=request.user,
                project=updated.project,
                task=updated,
                summary=f"Reassigned {updated.task_key}",
            )
        else:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_UPDATED,
                actor=request.user,
                project=updated.project,
                task=updated,
                summary=f"Updated {updated.task_key}",
            )
        return Response(TaskDetailSerializer(updated).data)


class TaskPositionView(TaskScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def patch(self, request, *args, **kwargs):
        task = self.task
        serializer = TaskPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_status = task.status
        task.status = serializer.validated_data["status"]
        task.position = serializer.validated_data["position"]
        if task.status == Task.Status.DONE and not task.completed_at:
            task.completed_at = timezone.now()
        if task.status != Task.Status.DONE:
            task.completed_at = None
        task.save(update_fields=["status", "position", "completed_at", "updated_at"])

        if old_status != task.status:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_STATUS_CHANGED,
                actor=request.user,
                project=task.project,
                task=task,
                summary=f"Moved {task.task_key}",
                metadata={"from": old_status, "to": task.status},
            )
        return Response(TaskListSerializer(task).data)


class MyTasksView(WorkspaceScopedMixin, generics.ListAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = TaskListSerializer

    def get_queryset(self):
        qs = (
            Task.objects.filter(
                project__workspace=self.workspace,
                assignee=self.request.user,
                archived_at__isnull=True,
            )
            .select_related("assignee", "reporter", "project")
            .order_by("due_date", "priority")
        )
        status_param = self.request.query_params.get("status")
        if status_param == "open":
            qs = qs.exclude(status=Task.Status.DONE)
        elif status_param:
            qs = qs.filter(status=status_param)
        return qs
