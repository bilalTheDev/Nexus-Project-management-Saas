from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.projects.models import Project
from apps.projects.sprint_models import Sprint
from apps.projects.templates import apply_template, get_template
from apps.projects.workflow_models import IssueType, Transition, WorkflowStatus
from apps.tasks.models import Task


class ProjectSerializer(serializers.ModelSerializer):
    lead = UserSerializer(read_only=True)
    lead_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    default_assignee = UserSerializer(read_only=True)
    default_assignee_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    progress = serializers.SerializerMethodField()
    open_tasks = serializers.SerializerMethodField()
    open_issues = serializers.SerializerMethodField()
    overdue = serializers.SerializerMethodField()
    resolved = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()
    total_issues = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "workspace",
            "name",
            "key",
            "description",
            "status",
            "template_key",
            "board_config",
            "start_date",
            "due_date",
            "lead",
            "lead_id",
            "default_assignee",
            "default_assignee_id",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "is_pinned",
            "progress",
            "open_tasks",
            "open_issues",
            "overdue",
            "resolved",
            "total_tasks",
            "total_issues",
        )
        read_only_fields = (
            "id",
            "workspace",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "board_config",
            "progress",
            "open_tasks",
            "open_issues",
            "overdue",
            "resolved",
            "total_tasks",
            "total_issues",
        )

    def _tasks(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "tasks" in obj._prefetched_objects_cache:
            return [t for t in obj.tasks.all() if t.archived_at is None]
        return list(obj.tasks.filter(archived_at__isnull=True))

    def get_total_tasks(self, obj):
        return len(self._tasks(obj))

    def get_total_issues(self, obj):
        return self.get_total_tasks(obj)

    def get_resolved(self, obj):
        return sum(1 for t in self._tasks(obj) if t.status == Task.Status.DONE)

    def get_open_tasks(self, obj):
        return sum(1 for t in self._tasks(obj) if t.status != Task.Status.DONE)

    def get_open_issues(self, obj):
        return self.get_open_tasks(obj)

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

    def update(self, instance, validated_data):
        if "lead_id" in validated_data:
            instance.lead_id = validated_data.pop("lead_id")
        if "default_assignee_id" in validated_data:
            instance.default_assignee_id = validated_data.pop("default_assignee_id")
        return super().update(instance, validated_data)


class ProjectCreateSerializer(serializers.ModelSerializer):
    lead_id = serializers.UUIDField(required=False, allow_null=True)
    default_assignee_id = serializers.UUIDField(required=False, allow_null=True)
    template_key = serializers.CharField(required=False, default="scrum")

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
            "default_assignee_id",
            "template_key",
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

    def validate_template_key(self, value):
        key = (value or "scrum").strip().lower()
        if get_template(key) is None:
            raise serializers.ValidationError("Unknown project template.")
        return key

    def create(self, validated_data):
        lead_id = validated_data.pop("lead_id", None)
        default_assignee_id = validated_data.pop("default_assignee_id", None)
        template_key = validated_data.pop("template_key", "scrum")
        workspace = self.context["workspace"]
        user = self.context["request"].user
        if lead_id is None:
            lead_id = user.id
        project = Project.objects.create(
            workspace=workspace,
            created_by=user,
            lead_id=lead_id,
            default_assignee_id=default_assignee_id,
            template_key=template_key,
            **validated_data,
        )
        apply_template(project, template_key)
        return project


class WorkflowStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStatus
        fields = (
            "id",
            "key",
            "name",
            "category",
            "position",
            "wip_limit",
        )


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ("id", "key", "name", "hierarchy_level", "position")


class TransitionSerializer(serializers.ModelSerializer):
    from_status = WorkflowStatusSerializer(read_only=True)
    to_status = WorkflowStatusSerializer(read_only=True)
    from_status_id = serializers.UUIDField(write_only=True)
    to_status_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Transition
        fields = (
            "id",
            "name",
            "from_status",
            "to_status",
            "from_status_id",
            "to_status_id",
            "validators",
        )


class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = (
            "id",
            "name",
            "goal",
            "status",
            "start_date",
            "end_date",
            "started_at",
            "completed_at",
            "start_snapshot",
            "complete_snapshot",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "started_at",
            "completed_at",
            "start_snapshot",
            "complete_snapshot",
            "created_at",
            "updated_at",
        )
