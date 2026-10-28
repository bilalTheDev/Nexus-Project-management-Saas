"""Workspace-scoped activity / audit events."""

import uuid

from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace


class ActivityEvent(models.Model):
    class EventType(models.TextChoices):
        TASK_CREATED = "task_created", "Task Created"
        TASK_UPDATED = "task_updated", "Task Updated"
        TASK_STATUS_CHANGED = "task_status_changed", "Task Status Changed"
        TASK_ASSIGNED = "task_assigned", "Task Assigned"
        COMMENT_ADDED = "comment_added", "Comment Added"
        MENTIONED = "mentioned", "Mentioned"
        PROJECT_CREATED = "project_created", "Project Created"
        PROJECT_UPDATED = "project_updated", "Project Updated"
        MEMBER_ADDED = "member_added", "Member Added"
        MEMBER_ROLE_CHANGED = "member_role_changed", "Member Role Changed"
        WORKSPACE_CREATED = "workspace_created", "Workspace Created"
        SYSTEM = "system", "System Automation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="activity_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_events",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_events",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_events",
    )
    event_type = models.CharField(max_length=64, choices=EventType.choices)
    summary = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["task", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.workspace.slug}"
