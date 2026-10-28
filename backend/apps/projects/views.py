from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.onboarding import UserOnboarding, get_or_create_onboarding
from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.projects.serializers import (
    IssueTypeSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    SprintSerializer,
    TransitionSerializer,
    WorkflowStatusSerializer,
)
from apps.projects.sprint_models import Sprint
from apps.projects.templates import list_templates
from apps.projects.workflow_models import Transition, WorkflowStatus
from apps.tasks.models import Task
from apps.projects.governance_models import ProjectMembership
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.permissions import (
    CanMutateWorkspaceContent,
    HasProjectRole,
    HasWorkspaceRole,
    IsWorkspaceMember,
)


class ProjectTemplateListView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(list_templates())


class ProjectKeyCheckView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        key = (request.query_params.get("key") or "").strip().upper()
        if not (2 <= len(key) <= 16):
            return Response({"key": key, "available": False, "reason": "invalid"})
        taken = (
            Project.objects.for_user(request.user)
            .filter(workspace=self.workspace, key__iexact=key)
            .exists()
        )
        return Response({"key": key, "available": not taken})


class ProjectListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_queryset(self):
        qs = (
            Project.objects.for_user(self.request.user)
            .filter(workspace=self.workspace)
            .select_related("lead", "created_by", "default_assignee")
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
        onboarding = get_or_create_onboarding(request.user, self.workspace)
        checklist = dict(onboarding.checklist or {})
        checklist["create_project"] = True
        onboarding.checklist = checklist
        onboarding.save(update_fields=["checklist", "updated_at"])
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
            Project.objects.for_user(self.request.user)
            .filter(workspace=self.workspace)
            .select_related("lead", "created_by", "default_assignee")
            .prefetch_related("tasks")
        )

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), key__iexact=self.kwargs[self.lookup_url_kwarg]
        )


class ProjectArchiveView(WorkspaceScopedMixin, APIView):
    permission_classes = [
        IsWorkspaceMember,
        HasWorkspaceRole(WorkspaceMembership.Role.PROJECT_MANAGER),
    ]
    policy_action = "project.admin"

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project.objects.for_user(request.user),
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        project.archived_at = timezone.now()
        project.save(update_fields=["archived_at", "updated_at"])
        return Response(ProjectSerializer(project, context={"request": request}).data)


class ProjectWorkflowView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
            archived_at__isnull=True,
        )

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        return Response(
            {
                "statuses": WorkflowStatusSerializer(
                    project.workflow_statuses.all(), many=True
                ).data,
                "issue_types": IssueTypeSerializer(
                    project.issue_types.all(), many=True
                ).data,
                "transitions": TransitionSerializer(
                    project.transitions.select_related(
                        "from_status", "to_status"
                    ).all(),
                    many=True,
                ).data,
            }
        )


class ProjectTransitionCreateView(WorkspaceScopedMixin, APIView):
    permission_classes = [
        IsWorkspaceMember,
        HasProjectRole(ProjectMembership.Role.ADMIN),
    ]
    policy_action = "workflow.manage"

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        self.project = project
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        frm = get_object_or_404(
            WorkflowStatus, project=project, pk=data["from_status_id"]
        )
        to = get_object_or_404(
            WorkflowStatus, project=project, pk=data["to_status_id"]
        )
        transition = Transition.objects.create(
            project=project,
            name=data["name"],
            from_status=frm,
            to_status=to,
            validators=data.get("validators") or [],
        )
        return Response(
            TransitionSerializer(transition).data, status=status.HTTP_201_CREATED
        )


class ProjectStatusCreateView(WorkspaceScopedMixin, APIView):
    permission_classes = [
        IsWorkspaceMember,
        HasProjectRole(ProjectMembership.Role.ADMIN),
    ]
    policy_action = "workflow.manage"

    def get_project(self):
        return get_object_or_404(
            Project.objects.for_user(self.request.user),
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
        )

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        self.project = project
        serializer = WorkflowStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_obj = WorkflowStatus.objects.create(
            project=project, **serializer.validated_data
        )
        return Response(
            WorkflowStatusSerializer(status_obj).data, status=status.HTTP_201_CREATED
        )


class SprintListCreateView(WorkspaceScopedMixin, generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]
    serializer_class = SprintSerializer
    policy_action = "sprint.manage"

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
            archived_at__isnull=True,
        )

    def get_queryset(self):
        return Sprint.objects.for_user(self.request.user).filter(
            project=self.get_project()
        )

    def perform_create(self, serializer):
        serializer.save(project=self.get_project(), created_by=self.request.user)


class SprintStartView(WorkspaceScopedMixin, APIView):
    permission_classes = [
        IsWorkspaceMember,
        HasProjectRole(ProjectMembership.Role.ADMIN),
    ]
    policy_action = "sprint.manage"

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        sprint = get_object_or_404(Sprint, project=project, pk=kwargs["sprint_id"])
        if Sprint.objects.filter(project=project, status=Sprint.Status.ACTIVE).exists():
            raise ValidationError(
                {"detail": "Only one active sprint is allowed per project."}
            )
        if sprint.status != Sprint.Status.FUTURE:
            raise ValidationError({"detail": "Only future sprints can be started."})

        sprint.name = request.data.get("name", sprint.name)
        sprint.goal = request.data.get("goal", sprint.goal)
        if request.data.get("start_date"):
            sprint.start_date = request.data["start_date"]
        if request.data.get("end_date"):
            sprint.end_date = request.data["end_date"]

        issues = list(
            Task.objects.filter(sprint=sprint, archived_at__isnull=True).values(
                "id", "story_points", "status", "number"
            )
        )
        sprint.start_snapshot = {
            "issue_ids": [str(i["id"]) for i in issues],
            "points": sum(i["story_points"] or 0 for i in issues),
            "count": len(issues),
        }
        sprint.status = Sprint.Status.ACTIVE
        sprint.started_at = timezone.now()
        sprint.save()

        onboarding = get_or_create_onboarding(request.user, self.workspace)
        checklist = dict(onboarding.checklist or {})
        checklist["start_sprint"] = True
        onboarding.checklist = checklist
        onboarding.save(update_fields=["checklist", "updated_at"])

        return Response(SprintSerializer(sprint).data)


class SprintCompleteView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        sprint = get_object_or_404(Sprint, project=project, pk=kwargs["sprint_id"])
        if sprint.status != Sprint.Status.ACTIVE:
            raise ValidationError({"detail": "Only the active sprint can be completed."})

        move_to = request.data.get("move_incomplete_to", "backlog")
        next_sprint = None
        if move_to == "next_sprint":
            next_id = request.data.get("next_sprint_id")
            next_sprint = get_object_or_404(Sprint, project=project, pk=next_id)
            if next_sprint.status == Sprint.Status.COMPLETED:
                raise ValidationError({"detail": "Cannot move issues into a completed sprint."})

        issues = Task.objects.filter(sprint=sprint, archived_at__isnull=True)
        incomplete = issues.exclude(
            workflow_status__category="done"
        ).exclude(status=Task.Status.DONE)

        sprint.complete_snapshot = {
            "issue_ids": [str(i) for i in issues.values_list("id", flat=True)],
            "completed_ids": [
                str(i)
                for i in issues.filter(workflow_status__category="done").values_list(
                    "id", flat=True
                )
            ],
            "incomplete_ids": [str(i.id) for i in incomplete],
            "points": sum(i.story_points or 0 for i in issues),
        }
        sprint.status = Sprint.Status.COMPLETED
        sprint.completed_at = timezone.now()
        sprint.save()

        if next_sprint:
            incomplete.update(sprint=next_sprint)
        else:
            incomplete.update(sprint=None)

        return Response(SprintSerializer(sprint).data)


class OnboardingView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        state = get_or_create_onboarding(request.user, self.workspace)
        # Recompute checklist from real data
        checklist = dict(state.checklist or {})
        has_project = Project.objects.filter(
            workspace=self.workspace, archived_at__isnull=True
        ).exists()
        has_issue = Task.objects.filter(
            project__workspace=self.workspace, archived_at__isnull=True
        ).exists()
        from apps.workspaces.models import WorkspaceMembership

        has_invite = (
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                status=WorkspaceMembership.Status.ACTIVE,
            )
            .exclude(user=request.user)
            .exists()
        )
        has_sprint = Sprint.objects.filter(
            project__workspace=self.workspace, status=Sprint.Status.ACTIVE
        ).exists() or Sprint.objects.filter(
            project__workspace=self.workspace, status=Sprint.Status.COMPLETED
        ).exists()

        checklist["create_project"] = checklist.get("create_project") or has_project
        checklist["create_issue"] = checklist.get("create_issue") or has_issue
        checklist["invite_teammate"] = checklist.get("invite_teammate") or has_invite
        checklist["start_sprint"] = checklist.get("start_sprint") or has_sprint
        checklist.setdefault("use_cmdk", False)
        state.checklist = checklist
        state.save(update_fields=["checklist", "updated_at"])

        return Response(
            {
                "checklist": checklist,
                "checklist_dismissed": state.checklist_dismissed,
                "tour_completed": state.tour_completed,
                "tour_skipped": state.tour_skipped,
                "tour_step": state.tour_step,
                "links": {
                    "create_project": f"/app/{self.workspace.slug}/projects/new",
                    "create_issue": f"/app/{self.workspace.slug}/projects",
                    "invite_teammate": f"/app/{self.workspace.slug}/members",
                    "start_sprint": f"/app/{self.workspace.slug}/projects",
                    "use_cmdk": f"/app/{self.workspace.slug}/dashboard",
                },
            }
        )

    def patch(self, request, *args, **kwargs):
        state = get_or_create_onboarding(request.user, self.workspace)
        if "checklist_dismissed" in request.data:
            state.checklist_dismissed = bool(request.data["checklist_dismissed"])
        if "tour_completed" in request.data:
            state.tour_completed = bool(request.data["tour_completed"])
        if "tour_skipped" in request.data:
            state.tour_skipped = bool(request.data["tour_skipped"])
        if "tour_step" in request.data:
            state.tour_step = int(request.data["tour_step"])
        if "checklist" in request.data and isinstance(request.data["checklist"], dict):
            merged = dict(state.checklist or {})
            merged.update(request.data["checklist"])
            state.checklist = merged
        if request.data.get("restart_tour"):
            state.tour_completed = False
            state.tour_skipped = False
            state.tour_step = 0
        state.save()
        return self.get(request, *args, **kwargs)
