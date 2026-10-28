from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.comments.models import Comment
from apps.comments.serializers import CommentCreateSerializer, CommentSerializer
from apps.tasks.models import Task
from apps.workspaces.permissions import (
    ADMIN_ROLES,
    CanMutateWorkspaceContent,
    IsWorkspaceMember,
    get_membership,
)


class TaskCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsWorkspaceMember, CanMutateWorkspaceContent]

    def initial(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task.objects.for_user(request.user).select_related(
                "project", "project__workspace", "assignee"
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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects.for_user(self.request.user)
            .filter(task=self.task, deleted_at__isnull=True)
            .select_related("author")
            .order_by("created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["task"] = self.task
        ctx["workspace"] = self.workspace
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        log_activity(
            workspace=self.workspace,
            event_type=ActivityEvent.EventType.COMMENT_ADDED,
            actor=request.user,
            project=self.task.project,
            task=self.task,
            summary=f"Commented on {self.task.task_key}",
            metadata={"excerpt": comment.body[:120]},
        )
        if (
            self.task.assignee_id
            and self.task.assignee_id != request.user.id
        ):
            from apps.projects.governance_models import Notification
            from apps.projects.governance_views import notify_once

            notify_once(
                workspace=self.workspace,
                recipient=self.task.assignee,
                actor=request.user,
                kind=Notification.Kind.COMMENT,
                title=f"Comment on {self.task.issue_key}",
                body=comment.body[:200],
                link=f"/app/{self.workspace.slug}/issues/{self.task.id}",
                dedupe_key=f"comment:{comment.id}",
            )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(generics.DestroyAPIView):
    permission_classes = [IsWorkspaceMember]

    def initial(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment.objects.for_user(request.user).select_related(
                "author", "task", "task__project", "task__project__workspace"
            ),
            pk=kwargs.get("comment_id") or self.kwargs.get("comment_id"),
            deleted_at__isnull=True,
        )
        self.comment = comment
        self.workspace = comment.task.project.workspace
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise Http404("Not found.")
        super().initial(request, *args, **kwargs)

    def get_object(self):
        comment = self.comment
        if comment.author_id != self.request.user.id:
            if self.membership.role not in ADMIN_ROLES:
                raise PermissionDenied("You can only delete your own comments.")
        return comment

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
