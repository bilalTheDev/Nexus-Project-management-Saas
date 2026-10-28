"""Sprint lifecycle and completion snapshots."""

import uuid

from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.workspaces.scoping import ProjectChildScopedQuerySet


class Sprint(models.Model):
    class Status(models.TextChoices):
        FUTURE = "future", "Future"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    objects = ProjectChildScopedQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sprints",
    )
    name = models.CharField(max_length=120)
    goal = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.FUTURE,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Snapshot of issue ids + points at start / completion for reports
    start_snapshot = models.JSONField(default=dict, blank=True)
    complete_snapshot = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_sprints",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.key} / {self.name}"
