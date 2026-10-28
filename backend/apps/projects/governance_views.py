from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.governance_models import (
    Component,
    Notification,
    NotificationPreference,
    ProjectMembership,
    Release,
)
from apps.projects.models import Project
from apps.projects.policy import effective_permissions, get_project_role
from apps.tasks.models import Task
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import (
    CanMutateWorkspaceContent,
    HasProjectRole,
    IsWorkspaceMember,
    get_membership,
)
from rest_framework import serializers


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = (
            "id",
            "name",
            "description",
            "status",
            "start_date",
            "release_date",
            "released_at",
            "created_at",
        )
        read_only_fields = ("id", "status", "released_at", "created_at")


class ComponentSerializer(serializers.ModelSerializer):
    # User PKs are BigAutoField (int), not UUID.
    lead_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    default_assignee_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = Component
        fields = (
            "id",
            "name",
            "description",
            "lead",
            "lead_id",
            "default_assignee",
            "default_assignee_id",
            "created_at",
        )
        read_only_fields = ("id", "lead", "default_assignee", "created_at")

    def validate(self, attrs):
        from apps.workspaces.validators import validate_same_workspace_fks

        return validate_same_workspace_fks(attrs, self.context, project=self.context.get("project"))

    def create(self, validated_data):
        lead_id = validated_data.pop("lead_id", None)
        default_assignee_id = validated_data.pop("default_assignee_id", None)
        return Component.objects.create(
            lead_id=lead_id,
            default_assignee_id=default_assignee_id,
            **validated_data,
        )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "body",
            "link",
            "read_at",
            "created_at",
        )
        read_only_fields = fields


class ReleaseListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]
    serializer_class = ReleaseSerializer
    policy_action = "release.manage"

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsWorkspaceMember(),
                HasProjectRole(ProjectMembership.Role.ADMIN)(),
            ]
        return super().get_permissions()

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def get_queryset(self):
        return Release.objects.for_user(self.request.user).filter(
            project=self.get_project()
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["workspace"] = self.workspace
        ctx["project"] = self.get_project()
        return ctx

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class ReleaseDetailView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]
    policy_action = "release.manage"

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        release = get_object_or_404(
            Release.objects.for_user(request.user),
            project=project,
            pk=kwargs["release_id"],
        )
        issues = Task.objects.for_user(request.user).filter(
            fix_version=release, archived_at__isnull=True
        )
        by_status = {}
        for issue in issues.select_related("workflow_status"):
            key = issue.workflow_status.name if issue.workflow_status else issue.status
            by_status.setdefault(key, []).append(
                {"id": str(issue.id), "key": issue.issue_key, "title": issue.title}
            )
        unresolved = issues.exclude(
            workflow_status__category="done"
        ).exclude(status=Task.Status.DONE)
        return Response(
            {
                "release": ReleaseSerializer(release).data,
                "issues_by_status": by_status,
                "unresolved_count": unresolved.count(),
            }
        )


class ReleasePublishView(WorkspaceScopedMixin, APIView):
    permission_classes = [
        IsWorkspaceMember,
        HasProjectRole(ProjectMembership.Role.ADMIN),
    ]
    policy_action = "release.manage"

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        self.project = project
        release = get_object_or_404(
            Release.objects.for_user(request.user),
            project=project,
            pk=kwargs["release_id"],
        )
        unresolved = (
            Task.objects.for_user(request.user)
            .filter(fix_version=release, archived_at__isnull=True)
            .exclude(workflow_status__category="done")
            .exclude(status=Task.Status.DONE)
        )
        move_to = request.data.get("move_unresolved_to")
        force = bool(request.data.get("force"))
        if unresolved.exists() and not force and not move_to:
            return Response(
                {
                    "warning": True,
                    "detail": f"{unresolved.count()} unresolved issues remain. Pass force=true or move_unresolved_to.",
                    "unresolved_count": unresolved.count(),
                },
                status=status.HTTP_409_CONFLICT,
            )
        if move_to:
            target = get_object_or_404(
                Release.objects.for_user(request.user), project=project, pk=move_to
            )
            unresolved.update(fix_version=target)
        release.status = Release.Status.RELEASED
        release.released_at = timezone.now()
        release.save(update_fields=["status", "released_at", "updated_at"])
        return Response(ReleaseSerializer(release).data)


class ReleaseNotesView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project.objects.for_user(request.user),
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        release = get_object_or_404(
            Release.objects.for_user(request.user),
            project=project,
            pk=kwargs["release_id"],
        )
        issues = (
            Task.objects.for_user(request.user)
            .filter(fix_version=release, archived_at__isnull=True)
            .filter(workflow_status__category="done")
            .select_related("issue_type")
        )
        grouped = {}
        for issue in issues:
            t = issue.issue_type.name if issue.issue_type else "Other"
            grouped.setdefault(t, []).append(f"- {issue.issue_key}: {issue.title}")
        lines = [f"# Release notes — {release.name}", ""]
        for type_name, items in grouped.items():
            lines.append(f"## {type_name}")
            lines.extend(items)
            lines.append("")
        return Response({"markdown": "\n".join(lines)})


class ComponentListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]
    serializer_class = ComponentSerializer

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def get_queryset(self):
        return Component.objects.for_user(self.request.user).filter(
            project=self.get_project()
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["workspace"] = self.workspace
        ctx["project"] = self.get_project()
        return ctx

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class MePermissionsView(APIView):
    def get(self, request, *args, **kwargs):
        from django.http import Http404
        from apps.workspaces.models import Workspace

        project_key = request.query_params.get("project")
        slug = request.query_params.get("workspace")
        membership = None
        project = None
        if slug:
            workspace = (
                Workspace.objects.for_user(request.user)
                .filter(slug=slug, archived_at__isnull=True)
                .first()
            )
            if workspace is None:
                raise Http404("Workspace not found.")
            membership = get_membership(request.user, workspace)
            if project_key:
                project = (
                    Project.objects.for_user(request.user)
                    .filter(workspace=workspace, key__iexact=project_key)
                    .first()
                )
        if membership is None:
            raise Http404("Workspace not found.")
        project_role = get_project_role(request.user, project) if project else None
        return Response(
            effective_permissions(
                workspace_role=membership.role, project_role=project_role
            )
        )


class NotificationListView(WorkspaceScopedMixin, generics.ListAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.for_user(self.request.user).filter(
            workspace=self.workspace, recipient=self.request.user
        )


class NotificationMarkReadView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def post(self, request, *args, **kwargs):
        note = get_object_or_404(
            Notification.objects.for_user(request.user),
            pk=kwargs["notification_id"],
            recipient=request.user,
            workspace=self.workspace,
        )
        note.read_at = timezone.now()
        note.save(update_fields=["read_at"])
        return Response(NotificationSerializer(note).data)


def notify_once(*, workspace, recipient, actor, kind, title, body="", link="", dedupe_key=""):
    """Create a notification exactly once for a dedupe_key."""
    prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)
    allowed = {
        Notification.Kind.ASSIGNED: prefs.assigned,
        Notification.Kind.MENTIONED: prefs.mentioned,
        Notification.Kind.STATUS_CHANGED: prefs.status_on_watched,
        Notification.Kind.COMMENT: prefs.comment_on_watched,
    }
    if not allowed.get(kind, True):
        return None
    if dedupe_key:
        existing = Notification.objects.filter(
            recipient=recipient, dedupe_key=dedupe_key
        ).first()
        if existing:
            return existing
    return Notification.objects.create(
        workspace=workspace,
        recipient=recipient,
        actor=actor,
        kind=kind,
        title=title,
        body=body,
        link=link,
        dedupe_key=dedupe_key,
    )
