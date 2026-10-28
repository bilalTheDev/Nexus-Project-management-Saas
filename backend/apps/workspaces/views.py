from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import (
    ADMIN_ROLES,
    IsWorkspaceAdmin,
    IsWorkspaceMember,
)
from apps.workspaces.serializers import (
    MembershipRoleUpdateSerializer,
    MembershipSerializer,
    OwnershipTransferSerializer,
    WorkspaceCreateSerializer,
    WorkspaceSerializer,
)


class WorkspaceListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def get_queryset(self):
        return (
            Workspace.objects.filter(
                memberships__user=self.request.user,
                memberships__status=WorkspaceMembership.Status.ACTIVE,
                archived_at__isnull=True,
            )
            .annotate(
                active_member_count=Count(
                    "memberships",
                    filter=Q(memberships__status=WorkspaceMembership.Status.ACTIVE),
                    distinct=True,
                )
            )
            .prefetch_related("memberships")
            .distinct()
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = serializer.save()
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.WORKSPACE_CREATED,
            actor=request.user,
            summary=f"Created workspace {workspace.name}",
        )
        return Response(
            WorkspaceSerializer(workspace, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class WorkspaceDetailView(WorkspaceScopedMixin, generics.RetrieveUpdateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsWorkspaceMember]
    lookup_field = "slug"

    def get_object(self):
        return self.workspace

    def perform_update(self, serializer):
        if self.membership.role not in ADMIN_ROLES:
            raise PermissionDenied("Only admins can update workspace settings.")
        serializer.save()


class WorkspaceDashboardView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        workspace = self.workspace
        projects = Project.objects.filter(
            workspace=workspace, archived_at__isnull=True
        ).select_related("lead")
        tasks = Task.objects.filter(
            project__workspace=workspace, archived_at__isnull=True
        ).select_related("assignee", "project")

        my_open = tasks.filter(assignee=request.user).exclude(status=Task.Status.DONE)
        overdue = my_open.filter(due_date__lt=timezone.now())
        done = tasks.filter(status=Task.Status.DONE)

        urgent_tasks = (
            tasks.exclude(status=Task.Status.DONE)
            .filter(
                Q(priority=Task.Priority.URGENT)
                | Q(due_date__lte=timezone.now() + timedelta(days=2))
            )
            .select_related("assignee", "project", "reporter")[:12]
        )

        projects_health = []
        for project in projects:
            project_tasks = [t for t in tasks if t.project_id == project.id]
            total = len(project_tasks)
            resolved = sum(1 for t in project_tasks if t.status == Task.Status.DONE)
            open_count = total - resolved
            overdue_count = sum(
                1
                for t in project_tasks
                if t.status != Task.Status.DONE
                and t.due_date
                and t.due_date < timezone.now()
            )
            projects_health.append(
                {
                    "id": str(project.id),
                    "name": project.name,
                    "key": project.key,
                    "status": project.status,
                    "progress": int((resolved / total) * 100) if total else 0,
                    "resolved": resolved,
                    "total": total,
                    "open_tasks": open_count,
                    "overdue": overdue_count,
                    "due_date": project.due_date,
                    "lead": {
                        "id": project.lead_id,
                        "full_name": project.lead.full_name if project.lead else None,
                        "email": project.lead.email if project.lead else None,
                    }
                    if project.lead_id
                    else None,
                }
            )

        recent_activity = (
            ActivityEvent.objects.filter(workspace=workspace)
            .select_related("actor", "project", "task", "task__project")
            .order_by("-created_at")[:8]
        )

        from apps.activity.serializers import ActivityEventSerializer
        from apps.tasks.serializers import TaskListSerializer

        return Response(
            {
                "metrics": {
                    "active_projects": projects.count(),
                    "my_open_tasks": my_open.count(),
                    "overdue": overdue.count(),
                    "completed_cycle": done.count(),
                },
                "urgent_tasks": TaskListSerializer(urgent_tasks, many=True).data,
                "projects_health": projects_health,
                "upcoming_milestones": [
                    {
                        "id": str(p.id),
                        "title": f"{p.name} target",
                        "date": p.due_date,
                        "project_key": p.key,
                    }
                    for p in projects
                    if p.due_date
                ][:6],
                "recent_activity": ActivityEventSerializer(
                    recent_activity, many=True
                ).data,
            }
        )


class MembershipListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = MembershipSerializer

    def get_queryset(self):
        qs = (
            WorkspaceMembership.objects.filter(workspace=self.workspace)
            .exclude(status=WorkspaceMembership.Status.REMOVED)
            .select_related("user")
            .prefetch_related("workspace__projects")
        )
        role = self.request.query_params.get("role")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        if role == "owner_admin":
            qs = qs.filter(
                role__in=[
                    WorkspaceMembership.Role.OWNER,
                    WorkspaceMembership.Role.ADMIN,
                ]
            )
        elif role:
            qs = qs.filter(role=role)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["workspace"] = self.workspace
        return ctx

    def perform_create(self, serializer):
        if self.membership.role not in ADMIN_ROLES:
            raise PermissionDenied("Only owners and admins can invite members.")
        membership = serializer.save()
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.MEMBER_ADDED,
            actor=self.request.user,
            summary=f"Added {membership.user.email} as {membership.role}",
            metadata={"role": membership.role},
        )
        from apps.accounts.onboarding import get_or_create_onboarding

        onboarding = get_or_create_onboarding(self.request.user, self.workspace)
        checklist = dict(onboarding.checklist or {})
        checklist["invite_teammate"] = True
        onboarding.checklist = checklist
        onboarding.save(update_fields=["checklist", "updated_at"])


class MembershipDetailView(WorkspaceScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = MembershipSerializer
    lookup_url_kwarg = "membership_id"

    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            workspace=self.workspace
        ).select_related("user")

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), pk=self.kwargs[self.lookup_url_kwarg]
        )

    def patch(self, request, *args, **kwargs):
        if self.membership.role not in ADMIN_ROLES:
            raise PermissionDenied("Only owners and admins can change roles.")
        membership = self.get_object()
        if membership.role == WorkspaceMembership.Role.OWNER:
            raise ValidationError({"role": "Cannot change the owner role here."})
        serializer = MembershipRoleUpdateSerializer(
            membership, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.MEMBER_ROLE_CHANGED,
            actor=request.user,
            summary=f"Changed role for {membership.user.email}",
            metadata={"role": membership.role},
        )
        return Response(MembershipSerializer(membership, context={"request": request}).data)

    def delete(self, request, *args, **kwargs):
        if self.membership.role not in ADMIN_ROLES:
            raise PermissionDenied("Only owners and admins can remove members.")
        membership = self.get_object()
        if membership.role == WorkspaceMembership.Role.OWNER:
            owners = WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                role=WorkspaceMembership.Role.OWNER,
                status=WorkspaceMembership.Status.ACTIVE,
            ).count()
            if owners <= 1:
                raise ValidationError(
                    {"detail": "Cannot remove the final workspace owner."}
                )
        membership.status = WorkspaceMembership.Status.REMOVED
        membership.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MembershipStatsView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        members = WorkspaceMembership.objects.filter(workspace=self.workspace).exclude(
            status=WorkspaceMembership.Status.REMOVED
        )
        active = members.filter(status=WorkspaceMembership.Status.ACTIVE).count()
        pending = members.filter(status=WorkspaceMembership.Status.PENDING).count()
        admins = members.filter(
            status=WorkspaceMembership.Status.ACTIVE,
            role__in=[
                WorkspaceMembership.Role.OWNER,
                WorkspaceMembership.Role.ADMIN,
            ],
        ).count()
        return Response(
            {
                "active_seats": active,
                "seat_limit": 12,
                "workspace_admins": admins,
                "pending_invites": pending,
                "security_tier": "2FA Enforced",
            }
        )


class OwnershipTransferView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, IsWorkspaceAdmin]

    def post(self, request, *args, **kwargs):
        if self.membership.role != WorkspaceMembership.Role.OWNER:
            raise PermissionDenied("Only the current owner can transfer ownership.")
        serializer = OwnershipTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        target = WorkspaceMembership.objects.filter(
            workspace=self.workspace,
            user__email__iexact=email,
            status=WorkspaceMembership.Status.ACTIVE,
        ).select_related("user").first()
        if target is None:
            raise ValidationError({"email": "Target user is not an active member."})
        if target.user_id == request.user.id:
            raise ValidationError({"email": "You already own this workspace."})

        self.membership.role = WorkspaceMembership.Role.ADMIN
        self.membership.save(update_fields=["role"])
        target.role = WorkspaceMembership.Role.OWNER
        target.save(update_fields=["role"])
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.MEMBER_ROLE_CHANGED,
            actor=request.user,
            summary=f"Transferred ownership to {target.user.email}",
        )
        return Response({"detail": "Ownership transferred.", "owner": target.user.email})
