from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.tasks.models import Task


class TaskListSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    task_key = serializers.CharField(read_only=True)
    project_key = serializers.CharField(source="project.key", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_id = serializers.UUIDField(source="project.id", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "task_key",
            "number",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reporter",
            "due_date",
            "position",
            "labels",
            "project_id",
            "project_key",
            "project_name",
            "created_at",
            "updated_at",
            "completed_at",
        )


class TaskDetailSerializer(TaskListSerializer):
    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + ("created_by",)


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.UUIDField(required=False, allow_null=True)
    reporter_id = serializers.UUIDField(required=False, allow_null=True)

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
        )

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["request"].user
        assignee_id = validated_data.pop("assignee_id", None)
        reporter_id = validated_data.pop("reporter_id", user.id)
        last = project.tasks.order_by("-number").first()
        number = (last.number + 1) if last else 1
        max_pos = (
            project.tasks.filter(status=validated_data.get("status", Task.Status.BACKLOG))
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        position = (max_pos or 0) + 1000
        return Task.objects.create(
            project=project,
            number=number,
            position=position,
            created_by=user,
            assignee_id=assignee_id,
            reporter_id=reporter_id,
            **validated_data,
        )


class TaskUpdateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.UUIDField(required=False, allow_null=True)
    reporter_id = serializers.UUIDField(required=False, allow_null=True)

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
        )

    def update(self, instance, validated_data):
        if "assignee_id" in validated_data:
            instance.assignee_id = validated_data.pop("assignee_id")
        if "reporter_id" in validated_data:
            instance.reporter_id = validated_data.pop("reporter_id")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.status == Task.Status.DONE and not instance.completed_at:
            instance.completed_at = timezone.now()
        if instance.status != Task.Status.DONE:
            instance.completed_at = None
        instance.save()
        return instance


class TaskPositionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)
    position = serializers.FloatField()
