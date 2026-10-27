from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.projects.serializers import ProjectCreateSerializer, ProjectSerializer
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import (
    MANAGER_ROLES,
    CanMutateWorkspaceContent,
    IsWorkspaceMember,
)


class ProjectListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_queryset(self):
        qs = (
            Project.objects.filter(workspace=self.workspace)
            .select_related("lead", "created_by")
            .prefetch_related("tasks")
        )
        archived = self.request.query_params.get("archived")
        if archived == "1":
            qs = qs.exclude(archived_at__isnull=True)
        else:
            qs = qs.filter(archived_at__isnull=True)
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(key__icontains=search)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["workspace"] = self.workspace
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.PROJECT_CREATED,
            actor=request.user,
            project=project,
            summary=f"Created project {project.key}",
        )
        return Response(
            ProjectSerializer(project, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(WorkspaceScopedMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]
    serializer_class = ProjectSerializer
    lookup_field = "key"
    lookup_url_kwarg = "project_key"

    def get_queryset(self):
        return (
            Project.objects.filter(workspace=self.workspace)
            .select_related("lead", "created_by")
            .prefetch_related("tasks")
        )

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), key__iexact=self.kwargs[self.lookup_url_kwarg]
        )


class ProjectArchiveView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def post(self, request, *args, **kwargs):
        if self.membership.role not in MANAGER_ROLES:
            raise PermissionDenied("Insufficient role to archive projects.")
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        project.archived_at = timezone.now()
        project.save(update_fields=["archived_at", "updated_at"])
        return Response(ProjectSerializer(project, context={"request": request}).data)
