"""Phase 3: releases, components, project roles, notifications."""

import uuid

from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.workspaces.models import Workspace
from apps.workspaces.scoping import NotificationScopedQuerySet, ProjectChildScopedQuerySet


class Release(models.Model):
    class Status(models.TextChoices):
        UNRELEASED = "unreleased", "Unreleased"
        RELEASED = "released", "Released"
        ARCHIVED = "archived", "Archived"

    objects = ProjectChildScopedQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="releases")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.UNRELEASED
    )
    start_date = models.DateField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-release_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="uniq_release_name_per_project"
            )
        ]

    def __str__(self) -> str:
        return f"{self.project.key} / {self.name}"


class Component(models.Model):
    objects = ProjectChildScopedQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="components"
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_components",
    )
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_component_assignee",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="uniq_component_name_per_project"
            )
        ]


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Project Admin"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"], name="uniq_project_membership"
            )
        ]


class Notification(models.Model):
    class Kind(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        MENTIONED = "mentioned", "Mentioned"
        STATUS_CHANGED = "status_changed", "Status changed"
        COMMENT = "comment", "Comment on watched"

    objects = NotificationScopedQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="notifications"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    # Idempotency key so retries create once
    dedupe_key = models.CharField(max_length=191, blank=True, default="")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    link = models.CharField(max_length=255, blank=True, default="")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "dedupe_key"],
                name="uniq_notification_dedupe",
                condition=~models.Q(dedupe_key=""),
            )
        ]


class NotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_prefs",
    )
    assigned = models.BooleanField(default=True)
    mentioned = models.BooleanField(default=True)
    status_on_watched = models.BooleanField(default=True)
    comment_on_watched = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
