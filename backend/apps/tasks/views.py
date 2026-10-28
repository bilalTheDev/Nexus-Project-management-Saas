from datetime import timedelta

from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.onboarding import get_or_create_onboarding
from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.projects.serializers import TransitionSerializer, WorkflowStatusSerializer
from apps.projects.sprint_models import Sprint
from apps.projects.workflow_models import Transition, WorkflowStatus
from apps.tasks.models import IssueChange, IssueLink, Task
from apps.tasks.serializers import (
    IssueChangeSerializer,
    IssueLinkSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskPositionSerializer,
    TaskUpdateSerializer,
)
from apps.tasks.services import (
    allowed_transitions,
    apply_transition,
    create_issue_link,
    snapshot_issue,
    record_changes,
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
        qs = (
            Task.objects.filter(project=project, archived_at__isnull=True)
            .select_related(
                "assignee",
                "reporter",
                "project",
                "created_by",
                "workflow_status",
                "issue_type",
                "parent",
                "sprint",
            )
            .annotate(
                comment_count=Count(
                    "comments", filter=Q(comments__deleted_at__isnull=True)
                )
            )
            .order_by("rank", "position", "created_at")
        )
        sprint = self.request.query_params.get("sprint")
        if sprint == "backlog":
            qs = qs.filter(sprint__isnull=True)
        elif sprint:
            qs = qs.filter(sprint_id=sprint)
        parent = self.request.query_params.get("parent")
        if parent:
            qs = qs.filter(parent_id=parent)
        issue_type = self.request.query_params.get("type")
        if issue_type:
            qs = qs.filter(issue_type__key=issue_type)
        return qs

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
            summary=f"Created {task.issue_key}",
        )
        onboarding = get_or_create_onboarding(request.user, self.workspace)
        checklist = dict(onboarding.checklist or {})
        checklist["create_issue"] = True
        onboarding.checklist = checklist
        onboarding.save(update_fields=["checklist", "updated_at"])
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
        statuses = list(project.workflow_statuses.order_by("position"))
        tasks = (
            Task.objects.filter(project=project, archived_at__isnull=True)
            .select_related(
                "assignee",
                "reporter",
                "project",
                "workflow_status",
                "issue_type",
                "parent",
                "sprint",
            )
            .annotate(
                comment_count=Count(
                    "comments", filter=Q(comments__deleted_at__isnull=True)
                )
            )
            .order_by("position", "created_at")
        )

        # Quick filters
        if request.query_params.get("only_mine") == "1":
            tasks = tasks.filter(assignee=request.user)
        if request.query_params.get("unassigned") == "1":
            tasks = tasks.filter(assignee__isnull=True)
        if request.query_params.get("recently_updated") == "1":
            cutoff = timezone.now() - timedelta(days=7)
            tasks = tasks.filter(updated_at__gte=cutoff)
        if request.query_params.get("sprint"):
            tasks = tasks.filter(sprint_id=request.query_params["sprint"])
        swimlane = request.query_params.get("swimlane", "none")

        priority = request.query_params.get("priority")
        assignee = request.query_params.get("assignee")
        search = request.query_params.get("search")
        if priority:
            tasks = tasks.filter(priority=priority)
        if assignee:
            tasks = tasks.filter(assignee_id=assignee)
        if search:
            tasks = tasks.filter(title__icontains=search)

        columns = {str(s.id): [] for s in statuses}
        # Also key by status.key for FE convenience
        columns_by_key = {s.key: [] for s in statuses}
        # Skip per-card epic_progress (extra queries) on the board payload.
        serialized = TaskListSerializer(
            tasks, many=True, context={"skip_epic_progress": True}
        ).data
        by_id = {str(row["id"]): row for row in serialized}
        for task in tasks:
            payload = by_id.get(str(task.id))
            if payload is None:
                continue
            if task.workflow_status_id and str(task.workflow_status_id) in columns:
                columns[str(task.workflow_status_id)].append(payload)
                columns_by_key[task.workflow_status.key].append(payload)
            elif task.status in columns_by_key:
                columns_by_key[task.status].append(payload)

        return Response(
            {
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "key": project.key,
                    "status": project.status,
                    "template_key": project.template_key,
                    "board_config": project.board_config,
                },
                "statuses": WorkflowStatusSerializer(statuses, many=True).data,
                "columns": columns_by_key,
                "columns_by_status_id": columns,
                "swimlane": swimlane,
            }
        )


class BacklogView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
            archived_at__isnull=True,
        )
        sprints = Sprint.objects.filter(project=project).exclude(
            status=Sprint.Status.COMPLETED
        )
        issues = (
            Task.objects.filter(project=project, archived_at__isnull=True)
            .select_related(
                "assignee",
                "workflow_status",
                "issue_type",
                "sprint",
                "project",
            )
            .order_by("rank", "created_at")
        )
        grouped = {
            "backlog": TaskListSerializer(
                [i for i in issues if i.sprint_id is None], many=True
            ).data,
            "sprints": [],
        }
        for sprint in sprints:
            grouped["sprints"].append(
                {
                    "sprint": {
                        "id": str(sprint.id),
                        "name": sprint.name,
                        "status": sprint.status,
                        "goal": sprint.goal,
                        "start_date": sprint.start_date,
                        "end_date": sprint.end_date,
                    },
                    "issues": TaskListSerializer(
                        [i for i in issues if i.sprint_id == sprint.id], many=True
                    ).data,
                }
            )
        return Response(grouped)


class TaskScopedMixin:
    """
    Resolve task via membership-scoped queryset.

    Foreign-tenant and missing UUIDs both yield 404 (no existence leak).
    """

    def initial(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.for_user(request.user).select_related(
                "project", "project__workspace"
            ),
            pk=kwargs.get("task_id") or self.kwargs.get("task_id"),
            archived_at__isnull=True,
        )
        self.task = task
        self.project = task.project
        self.workspace = task.project.workspace
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise Http404("Not found.")
        super().initial(request, *args, **kwargs)


class TaskDetailView(TaskScopedMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def get_object(self):
        return get_object_or_404(
            Task.objects.for_user(self.request.user).select_related(
                "assignee",
                "reporter",
                "project",
                "project__workspace",
                "created_by",
                "workflow_status",
                "issue_type",
                "parent",
                "sprint",
            ),
            pk=self.kwargs["task_id"],
            archived_at__isnull=True,
        )

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        old_assignee = task.assignee_id
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        if updated.assignee_id != old_assignee:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_ASSIGNED,
                actor=request.user,
                project=updated.project,
                task=updated,
                summary=f"Reassigned {updated.issue_key}",
            )
            if updated.assignee_id and updated.assignee_id != request.user.id:
                from apps.projects.governance_models import Notification
                from apps.projects.governance_views import notify_once

                notify_once(
                    workspace=self.workspace,
                    recipient=updated.assignee,
                    actor=request.user,
                    kind=Notification.Kind.ASSIGNED,
                    title=f"Assigned {updated.issue_key}",
                    body=updated.title,
                    link=f"/app/{self.workspace.slug}/issues/{updated.id}",
                    dedupe_key=f"assigned:{updated.id}:{updated.assignee_id}:{updated.version}",
                )
        else:
            log_activity(
                workspace=self.workspace,
                event_type=ActivityEvent.EventType.TASK_UPDATED,
                actor=request.user,
                project=updated.project,
                task=updated,
                summary=f"Updated {updated.issue_key}",
            )
        return Response(TaskDetailSerializer(updated).data)


class TaskPositionView(TaskScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def patch(self, request, *args, **kwargs):
        task = self.task
        serializer = TaskPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get("version") is not None and data["version"] != task.version:
            from rest_framework.exceptions import APIException

            class Conflict(APIException):
                status_code = 409
                default_code = "version_conflict"

            raise Conflict(
                detail={
                    "detail": "This issue changed. Reload?",
                    "code": "version_conflict",
                    "version": task.version,
                }
            )

        # Prefer explicit transition for status moves
        if data.get("transition_id"):
            apply_transition(
                issue=task,
                transition_id=data["transition_id"],
                actor=request.user,
                expected_version=data.get("version"),
            )
            task.refresh_from_db()
        elif data.get("workflow_status_id") or data.get("status"):
            target = None
            if data.get("workflow_status_id"):
                target = get_object_or_404(
                    WorkflowStatus,
                    project=task.project,
                    pk=data["workflow_status_id"],
                )
            else:
                target = get_object_or_404(
                    WorkflowStatus, project=task.project, key=data["status"]
                )
            transition = Transition.objects.filter(
                project=task.project,
                from_status=task.workflow_status,
                to_status=target,
            ).first()
            if not transition:
                from rest_framework.exceptions import APIException

                class Conflict(APIException):
                    status_code = 409
                    default_code = "invalid_transition"

                current = (
                    task.workflow_status.name if task.workflow_status else task.status
                )
                raise Conflict(
                    detail={
                        "detail": (
                            f"Cannot move from {current} to {target.name}. "
                            "No matching transition for this project workflow."
                        ),
                        "code": "invalid_transition",
                    }
                )
            apply_transition(
                issue=task,
                transition_id=transition.id,
                actor=request.user,
                expected_version=data.get("version"),
            )
            task.refresh_from_db()

        before = snapshot_issue(task)
        task.position = data["position"]
        if "rank" in data:
            task.rank = data["rank"]
        task.version += 1
        task.save(update_fields=["position", "rank", "version", "updated_at"])
        record_changes(
            issue=task,
            actor=request.user,
            before=before,
            after=snapshot_issue(task),
        )
        return Response(TaskListSerializer(task).data)


class IssueTransitionsView(TaskScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get(self, request, *args, **kwargs):
        return Response(
            TransitionSerializer(allowed_transitions(self.task), many=True).data
        )

    def post(self, request, *args, **kwargs):
        transition_id = request.data.get("transition_id")
        if not transition_id:
            raise ValidationError({"transition_id": "Required."})
        updated = apply_transition(
            issue=self.task,
            transition_id=transition_id,
            actor=request.user,
            comment=request.data.get("comment"),
            expected_version=request.data.get("version"),
        )
        return Response(TaskDetailSerializer(updated).data)


class IssueHistoryView(TaskScopedMixin, generics.ListAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = IssueChangeSerializer

    def get_queryset(self):
        return IssueChange.objects.filter(issue=self.task).select_related("actor")


class IssueLinkListCreateView(TaskScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def get(self, request, *args, **kwargs):
        links = IssueLink.objects.filter(source=self.task).select_related(
            "source", "target"
        )
        return Response(IssueLinkSerializer(links, many=True).data)

    def post(self, request, *args, **kwargs):
        target_id = request.data.get("target_id")
        link_type = request.data.get("link_type")
        target = get_object_or_404(
            Task.objects.for_user(request.user),
            pk=target_id,
            archived_at__isnull=True,
            project__workspace=self.workspace,
        )
        forward, _inverse = create_issue_link(
            source=self.task,
            target=target,
            link_type=link_type,
            actor=request.user,
        )
        return Response(
            IssueLinkSerializer(forward).data, status=status.HTTP_201_CREATED
        )


class IssueRankView(TaskScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def patch(self, request, *args, **kwargs):
        rank = request.data.get("rank")
        sprint_id = request.data.get("sprint_id", "__omit__")
        if rank is None:
            raise ValidationError({"rank": "Required."})
        before = snapshot_issue(self.task)
        self.task.rank = float(rank)
        if sprint_id != "__omit__":
            self.task.sprint_id = sprint_id
        self.task.version += 1
        self.task.save(update_fields=["rank", "sprint", "version", "updated_at"])
        record_changes(
            issue=self.task,
            actor=request.user,
            before=before,
            after=snapshot_issue(self.task),
        )
        return Response(TaskListSerializer(self.task).data)


class BulkIssueUpdateView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=kwargs["project_key"],
        )
        ids = request.data.get("issue_ids") or []
        if not ids:
            raise ValidationError({"issue_ids": "Required."})
        qs = Task.objects.filter(project=project, id__in=ids)
        updates = {}
        for field in ("priority", "sprint_id", "assignee_id"):
            if field in request.data:
                updates[field.replace("_id", "") if field.endswith("_id") else field] = (
                    request.data[field]
                )
        # Handle FKs explicitly
        if "assignee_id" in request.data:
            qs.update(assignee_id=request.data["assignee_id"])
        if "sprint_id" in request.data:
            qs.update(sprint_id=request.data["sprint_id"])
        if "priority" in request.data:
            qs.update(priority=request.data["priority"])
        if "labels" in request.data:
            for issue in qs:
                issue.labels = request.data["labels"]
                issue.save(update_fields=["labels", "updated_at"])
        if request.data.get("delete"):
            qs.update(archived_at=timezone.now())
        return Response({"updated": qs.count()})


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
            .select_related(
                "assignee", "reporter", "project", "workflow_status", "issue_type"
            )
            .order_by("due_date", "priority")
        )
        status_param = self.request.query_params.get("status")
        if status_param == "open":
            qs = qs.exclude(status=Task.Status.DONE)
        elif status_param:
            qs = qs.filter(status=status_param)
        return qs
