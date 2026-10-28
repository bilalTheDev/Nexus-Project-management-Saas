import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.comments.models import Comment
from apps.workspaces.models import WorkspaceMembership

User = get_user_model()
MENTION_RE = re.compile(r"@([A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|[A-Za-z0-9._-]+)")


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "task",
            "author",
            "body",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "task", "author", "created_at", "updated_at")


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body",)

    def create(self, validated_data):
        task = self.context["task"]
        author = self.context["request"].user
        body = validated_data["body"]
        comment = Comment.objects.create(task=task, author=author, body=body)

        workspace = task.project.workspace
        tokens = {m.group(1).lower() for m in MENTION_RE.finditer(body)}
        mentioned_users = []
        if tokens:
            members = WorkspaceMembership.objects.filter(
                workspace=workspace,
                status=WorkspaceMembership.Status.ACTIVE,
            ).select_related("user")
            for membership in members:
                user = membership.user
                handles = {
                    (user.email or "").lower(),
                    (user.username or "").lower(),
                }
                if handles & tokens:
                    mentioned_users.append(user)
                    log_activity(
                        workspace=workspace,
                        event_type=ActivityEvent.EventType.MENTIONED,
                        actor=author,
                        project=task.project,
                        task=task,
                        summary=f"{author.email} mentioned {user.email} on {task.issue_key}",
                        metadata={"mentioned_user_id": str(user.id)},
                    )
        return comment
