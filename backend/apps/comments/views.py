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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects.filter(task=self.task, deleted_at__isnull=True)
            .select_related("author")
            .order_by("created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["task"] = self.task
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
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(generics.DestroyAPIView):
    permission_classes = [IsWorkspaceMember]

    def initial(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment.objects.select_related(
                "author", "task", "task__project", "task__project__workspace"
            ),
            pk=kwargs.get("comment_id") or self.kwargs.get("comment_id"),
            deleted_at__isnull=True,
        )
        self.comment = comment
        self.workspace = comment.task.project.workspace
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise PermissionDenied("You are not a member of this workspace.")
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
