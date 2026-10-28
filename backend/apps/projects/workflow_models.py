"""Project-owned issue types, statuses, and transitions (team-managed)."""

import uuid

from django.db import models

from apps.projects.models import Project


class IssueType(models.Model):
    """Issue type owned by a project (Epic, Story, Task, Bug, Sub-task)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="issue_types",
    )
    key = models.SlugField(max_length=32)
    name = models.CharField(max_length=80)
    # 1 = epic, 0 = standard, -1 = sub-task
    hierarchy_level = models.SmallIntegerField(default=0)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "key"],
                name="uniq_issue_type_key_per_project",
            )
        ]

    def __str__(self) -> str:
        return f"{self.project.key}/{self.key}"


class WorkflowStatus(models.Model):
    class Category(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="workflow_statuses",
    )
    key = models.SlugField(max_length=32)
    name = models.CharField(max_length=80)
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.TODO,
    )
    position = models.PositiveSmallIntegerField(default=0)
    wip_limit = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "workflow statuses"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "key"],
                name="uniq_workflow_status_key_per_project",
            )
        ]

    def __str__(self) -> str:
        return f"{self.project.key}/{self.name}"


class Transition(models.Model):
    class Validator(models.TextChoices):
        REQUIRE_ASSIGNEE = "require_assignee", "Require assignee"
        REQUIRE_RESOLUTION = "require_resolution", "Require resolution"
        REQUIRE_COMMENT = "require_comment", "Require comment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    name = models.CharField(max_length=80)
    from_status = models.ForeignKey(
        WorkflowStatus,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
    )
    to_status = models.ForeignKey(
        WorkflowStatus,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
    )
    # List of Validator values
    validators = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "from_status", "to_status"],
                name="uniq_transition_per_status_pair",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}: {self.from_status_id} → {self.to_status_id}"
