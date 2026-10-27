from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.activity.models import ActivityEvent


class ActivityEventSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    project_key = serializers.CharField(source="project.key", read_only=True, default=None)
    project_name = serializers.CharField(
        source="project.name", read_only=True, default=None
    )
    task_key = serializers.SerializerMethodField()

    class Meta:
        model = ActivityEvent
        fields = (
            "id",
            "event_type",
            "summary",
            "metadata",
            "actor",
            "project_key",
            "project_name",
            "task_key",
            "created_at",
        )

    def get_task_key(self, obj):
        if obj.task_id and obj.task:
            return obj.task.task_key
        return None
