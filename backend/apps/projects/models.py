"""Projects scoped to a single workspace."""

import uuid

from django.conf import settings
from django.db import models

from apps.workspaces.models import Workspace


class Project(models.Model):
    class Status(models.TextChoices):
        ON_TRACK = "on_track", "On Track"
        IN_REVIEW = "in_review", "In Review"
        FAST_TRACK = "fast_track", "Fast Track"
        MAINTENANCE = "maintenance", "Maintenance"
        PLANNING = "planning", "Planning"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=160)
    key = models.CharField(max_length=16)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    # Fixture key: scrum | kanban | bug_tracking
    template_key = models.CharField(max_length=32, blank=True, default="scrum")
    board_config = models.JSONField(default=dict, blank=True)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_projects",
    )
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_assignee_projects",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                name="uniq_project_key_per_workspace",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "archived_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.key} — {self.name}"


# Re-export workflow / sprint / governance models for convenient imports.
from apps.projects.workflow_models import IssueType, Transition, WorkflowStatus  # noqa: E402,F401
from apps.projects.sprint_models import Sprint  # noqa: E402,F401
from apps.projects.governance_models import (  # noqa: E402,F401
    Component,
    Notification,
    NotificationPreference,
    ProjectMembership,
    Release,
)
