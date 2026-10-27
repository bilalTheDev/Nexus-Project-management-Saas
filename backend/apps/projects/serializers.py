from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.projects.models import Project
from apps.tasks.models import Task


class ProjectSerializer(serializers.ModelSerializer):
    lead = UserSerializer(read_only=True)
    lead_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    progress = serializers.SerializerMethodField()
    open_tasks = serializers.SerializerMethodField()
    overdue = serializers.SerializerMethodField()
    resolved = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "workspace",
            "name",
            "key",
            "description",
            "status",
            "start_date",
            "due_date",
            "lead",
            "lead_id",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "is_pinned",
            "progress",
            "open_tasks",
            "overdue",
            "resolved",
            "total_tasks",
        )
        read_only_fields = (
            "id",
            "workspace",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "progress",
            "open_tasks",
            "overdue",
            "resolved",
            "total_tasks",
        )

    def _tasks(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "tasks" in obj._prefetched_objects_cache:
            return [t for t in obj.tasks.all() if t.archived_at is None]
        return list(obj.tasks.filter(archived_at__isnull=True))

    def get_total_tasks(self, obj):
        return len(self._tasks(obj))

    def get_resolved(self, obj):
        return sum(1 for t in self._tasks(obj) if t.status == Task.Status.DONE)

    def get_open_tasks(self, obj):
        return sum(1 for t in self._tasks(obj) if t.status != Task.Status.DONE)

    def get_overdue(self, obj):
        from django.utils import timezone

        now = timezone.now()
        return sum(
            1
            for t in self._tasks(obj)
            if t.status != Task.Status.DONE and t.due_date and t.due_date < now
        )

    def get_progress(self, obj):
        total = self.get_total_tasks(obj)
        if not total:
            return 0
        return int((self.get_resolved(obj) / total) * 100)

    def validate_key(self, value):
        key = value.strip().upper()
        if not (2 <= len(key) <= 16):
            raise serializers.ValidationError("Project key must be 2–16 characters.")
        return key


class ProjectCreateSerializer(serializers.ModelSerializer):
    lead_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Project
        fields = (
            "name",
            "key",
            "description",
            "status",
            "start_date",
            "due_date",
            "lead_id",
            "is_pinned",
        )

    def validate_key(self, value):
        key = value.strip().upper()
        workspace = self.context["workspace"]
        if Project.objects.filter(workspace=workspace, key__iexact=key).exists():
            raise serializers.ValidationError(
                "A project with this key already exists in the workspace."
            )
        return key

    def create(self, validated_data):
        lead_id = validated_data.pop("lead_id", None)
        workspace = self.context["workspace"]
        user = self.context["request"].user
        return Project.objects.create(
            workspace=workspace,
            created_by=user,
            lead_id=lead_id,
            **validated_data,
        )
