"""Issues (historically Task) belonging to a project."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.projects.models import Project
from apps.projects.sprint_models import Sprint
from apps.projects.workflow_models import IssueType, WorkflowStatus

# Late imports for optional Phase 3 FKs avoided in initial field defs — see migration 0005.


class Task(models.Model):
    """Issue work item. API/UI term is 'issue'; model kept as Task for migration continuity."""

    class Status(models.TextChoices):
        """Legacy string status — mirrored from workflow_status.key when set."""

        BACKLOG = "backlog", "Backlog"
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        IN_REVIEW = "in_review", "In Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.BACKLOG,
    )
    workflow_status = models.ForeignKey(
        WorkflowStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="issues",
    )
    issue_type = models.ForeignKey(
        IssueType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="issues",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
    )
    fix_version = models.ForeignKey(
        "projects.Release",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
    )
    components = models.ManyToManyField(
        "projects.Component",
        blank=True,
        related_name="issues",
    )
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    position = models.FloatField(default=0)
    rank = models.FloatField(default=0)
    labels = models.JSONField(default=list, blank=True)
    story_points = models.FloatField(null=True, blank=True)
    resolution = models.CharField(max_length=64, blank=True, default="")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "number"],
                name="uniq_task_number_per_project",
            )
        ]
        indexes = [
            models.Index(fields=["project", "status", "position"]),
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["project", "rank"]),
            models.Index(fields=["sprint", "rank"]),
        ]

    def __str__(self) -> str:
        return f"{self.issue_key}: {self.title}"

    @property
    def task_key(self) -> str:
        return f"{self.project.key}-{self.number}"

    @property
    def issue_key(self) -> str:
        return self.task_key

    def clean(self):
        super().clean()
        self.validate_hierarchy()

    def validate_hierarchy(self):
        if not self.issue_type_id:
            return
        level = self.issue_type.hierarchy_level
        if level >= 1 and self.parent_id:
            raise ValidationError({"parent": "An Epic cannot have a parent."})
        if level < 0:
            if not self.parent_id:
                raise ValidationError(
                    {"parent": "A Sub-task must have a non-Sub-task parent."}
                )
            parent = self.parent
            if parent and parent.issue_type and parent.issue_type.hierarchy_level < 0:
                raise ValidationError(
                    {"parent": "A Sub-task parent cannot itself be a Sub-task."}
                )
        if self.parent_id and self.parent and self.parent.project_id != self.project_id:
            raise ValidationError({"parent": "Parent must belong to the same project."})


class IssueChange(models.Model):
    """Append-only field history for an issue."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="changes",
    )
    field = models.CharField(max_length=64)
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["issue", "-created_at"]),
        ]


class IssueLink(models.Model):
    class LinkType(models.TextChoices):
        BLOCKS = "blocks", "Blocks"
        IS_BLOCKED_BY = "is_blocked_by", "Is blocked by"
        RELATES_TO = "relates_to", "Relates to"
        DUPLICATES = "duplicates", "Duplicates"
        IS_DUPLICATED_BY = "is_duplicated_by", "Is duplicated by"

    INVERSE = {
        LinkType.BLOCKS: LinkType.IS_BLOCKED_BY,
        LinkType.IS_BLOCKED_BY: LinkType.BLOCKS,
        LinkType.RELATES_TO: LinkType.RELATES_TO,
        LinkType.DUPLICATES: LinkType.IS_DUPLICATED_BY,
        LinkType.IS_DUPLICATED_BY: LinkType.DUPLICATES,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="outward_links",
    )
    target = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="inward_links",
    )
    link_type = models.CharField(max_length=32, choices=LinkType.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_issue_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "target", "link_type"],
                name="uniq_issue_link_direction",
            )
        ]
