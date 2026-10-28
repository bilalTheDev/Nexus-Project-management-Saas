from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.projects.workflow_models import IssueType, WorkflowStatus
from apps.tasks.models import IssueChange, IssueLink, Task
from apps.tasks.services import epic_progress, record_changes, snapshot_issue


class WorkflowStatusBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStatus
        fields = ("id", "key", "name", "category", "position")


class IssueTypeBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ("id", "key", "name", "hierarchy_level")


class TaskListSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    task_key = serializers.CharField(read_only=True)
    issue_key = serializers.CharField(read_only=True)
    project_key = serializers.CharField(source="project.key", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_id = serializers.UUIDField(source="project.id", read_only=True)
    workflow_status = WorkflowStatusBriefSerializer(read_only=True)
    issue_type = IssueTypeBriefSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()
    epic_progress = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "task_key",
            "issue_key",
            "number",
            "title",
            "description",
            "status",
            "workflow_status",
            "issue_type",
            "parent",
            "sprint",
            "priority",
            "assignee",
            "reporter",
            "due_date",
            "position",
            "rank",
            "labels",
            "story_points",
            "resolution",
            "version",
            "project_id",
            "project_key",
            "project_name",
            "comment_count",
            "epic_progress",
            "created_at",
            "updated_at",
            "completed_at",
        )

    def get_comment_count(self, obj):
        if hasattr(obj, "comment_count"):
            return obj.comment_count
        return obj.comments.filter(deleted_at__isnull=True).count()

    def get_epic_progress(self, obj):
        if not obj.issue_type_id or obj.issue_type.hierarchy_level < 1:
            return None
        return epic_progress(obj)


class TaskDetailSerializer(TaskListSerializer):
    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + ("created_by",)


class TaskCreateSerializer(serializers.ModelSerializer):
    # User PK is BigAutoField; issue/sprint/status PKs are UUIDs.
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reporter_id = serializers.IntegerField(required=False, allow_null=True)
    issue_type_id = serializers.UUIDField(required=False, allow_null=True)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    sprint_id = serializers.UUIDField(required=False, allow_null=True)
    workflow_status_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reporter_id",
            "due_date",
            "labels",
            "issue_type_id",
            "parent_id",
            "sprint_id",
            "workflow_status_id",
            "story_points",
            "rank",
        )

    def validate(self, attrs):
        project = self.context["project"]
        issue_type_id = attrs.get("issue_type_id")
        parent_id = attrs.get("parent_id")
        issue_type = None
        if issue_type_id:
            issue_type = IssueType.objects.filter(
                project=project, pk=issue_type_id
            ).first()
            if not issue_type:
                raise serializers.ValidationError(
                    {"issue_type_id": "Unknown issue type for this project."}
                )
        else:
            issue_type = (
                project.issue_types.filter(key="task").first()
                or project.issue_types.filter(key="story").first()
                or project.issue_types.order_by("position").first()
            )
            if issue_type:
                attrs["issue_type_id"] = issue_type.id

        if issue_type:
            if issue_type.hierarchy_level >= 1 and parent_id:
                raise serializers.ValidationError(
                    {"parent_id": "An Epic cannot have a parent."}
                )
            if issue_type.hierarchy_level < 0 and not parent_id:
                raise serializers.ValidationError(
                    {"parent_id": "A Sub-task must have a non-Sub-task parent."}
                )
        if parent_id:
            parent = Task.objects.filter(project=project, pk=parent_id).first()
            if not parent:
                raise serializers.ValidationError(
                    {"parent_id": "Parent issue not found in this project."}
                )
            if parent.issue_type and parent.issue_type.hierarchy_level < 0:
                raise serializers.ValidationError(
                    {"parent_id": "A Sub-task cannot be a parent."}
                )
        return attrs

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["request"].user
        assignee_id = validated_data.pop("assignee_id", project.default_assignee_id)
        reporter_id = validated_data.pop("reporter_id", user.id)
        issue_type_id = validated_data.pop("issue_type_id", None)
        parent_id = validated_data.pop("parent_id", None)
        sprint_id = validated_data.pop("sprint_id", None)
        workflow_status_id = validated_data.pop("workflow_status_id", None)

        last = project.tasks.order_by("-number").first()
        number = (last.number + 1) if last else 1

        status_key = validated_data.get("status")
        workflow_status = None
        if workflow_status_id:
            workflow_status = WorkflowStatus.objects.filter(
                project=project, pk=workflow_status_id
            ).first()
        elif status_key:
            workflow_status = WorkflowStatus.objects.filter(
                project=project, key=status_key
            ).first()
        if workflow_status is None:
            workflow_status = (
                project.workflow_statuses.filter(key="todo").first()
                or project.workflow_statuses.filter(key="backlog").first()
                or project.workflow_statuses.order_by("position").first()
            )
        if workflow_status:
            validated_data["status"] = workflow_status.key

        max_pos = (
            project.tasks.filter(status=validated_data.get("status", Task.Status.BACKLOG))
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        position = (max_pos or 0) + 1000
        rank = validated_data.pop("rank", None)
        if rank is None:
            max_rank = (
                project.tasks.order_by("-rank").values_list("rank", flat=True).first()
            )
            rank = (max_rank or 0) + 1000

        issue = Task.objects.create(
            project=project,
            number=number,
            position=position,
            rank=rank,
            created_by=user,
            assignee_id=assignee_id,
            reporter_id=reporter_id,
            issue_type_id=issue_type_id,
            parent_id=parent_id,
            sprint_id=sprint_id,
            workflow_status=workflow_status,
            **validated_data,
        )
        return issue


class TaskUpdateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reporter_id = serializers.IntegerField(required=False, allow_null=True)
    issue_type_id = serializers.UUIDField(required=False, allow_null=True)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    sprint_id = serializers.UUIDField(required=False, allow_null=True)
    version = serializers.IntegerField(required=False)

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reporter_id",
            "due_date",
            "labels",
            "issue_type_id",
            "parent_id",
            "sprint_id",
            "story_points",
            "resolution",
            "rank",
            "version",
        )

    def update(self, instance, validated_data):
        expected = validated_data.pop("version", None)
        if expected is not None and expected != instance.version:
            from rest_framework.exceptions import APIException

            class Conflict(APIException):
                status_code = 409
                default_code = "version_conflict"

            raise Conflict(
                detail={
                    "detail": "This issue changed. Reload?",
                    "code": "version_conflict",
                    "version": instance.version,
                }
            )

        before = snapshot_issue(instance)
        if "assignee_id" in validated_data:
            instance.assignee_id = validated_data.pop("assignee_id")
        if "reporter_id" in validated_data:
            instance.reporter_id = validated_data.pop("reporter_id")
        if "issue_type_id" in validated_data:
            instance.issue_type_id = validated_data.pop("issue_type_id")
        if "parent_id" in validated_data:
            instance.parent_id = validated_data.pop("parent_id")
        if "sprint_id" in validated_data:
            instance.sprint_id = validated_data.pop("sprint_id")

        # Status string updates must go through transitions — reject direct status change
        if "status" in validated_data and validated_data["status"] != instance.status:
            raise serializers.ValidationError(
                {
                    "status": (
                        "Use the transitions API to change status. "
                        "Direct status updates are not allowed."
                    )
                }
            )
        validated_data.pop("status", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.validate_hierarchy()
        instance.version += 1
        instance.save()
        actor = self.context["request"].user
        record_changes(
            issue=instance,
            actor=actor,
            before=before,
            after=snapshot_issue(instance),
        )
        return instance


class TaskPositionSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    workflow_status_id = serializers.UUIDField(required=False)
    transition_id = serializers.UUIDField(required=False)
    position = serializers.FloatField()
    rank = serializers.FloatField(required=False)
    version = serializers.IntegerField(required=False)


class IssueChangeSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = IssueChange
        fields = ("id", "field", "old_value", "new_value", "actor", "created_at")


class IssueLinkSerializer(serializers.ModelSerializer):
    source_key = serializers.CharField(source="source.issue_key", read_only=True)
    target_key = serializers.CharField(source="target.issue_key", read_only=True)

    class Meta:
        model = IssueLink
        fields = (
            "id",
            "source",
            "target",
            "source_key",
            "target_key",
            "link_type",
            "created_at",
        )
        read_only_fields = fields
