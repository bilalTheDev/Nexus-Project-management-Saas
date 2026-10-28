"""Per-user onboarding checklist and guided tour flags (server-backed)."""

import uuid

from django.conf import settings
from django.db import models

from apps.workspaces.models import Workspace


class UserOnboarding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="onboarding_states",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="onboarding_states",
    )
    checklist_dismissed = models.BooleanField(default=False)
    # Keys: create_project, create_issue, invite_teammate, start_sprint, use_cmdk
    checklist = models.JSONField(default=dict, blank=True)
    tour_completed = models.BooleanField(default=False)
    tour_skipped = models.BooleanField(default=False)
    tour_step = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workspace"],
                name="uniq_onboarding_per_user_workspace",
            )
        ]

    CHECKLIST_KEYS = (
        "create_project",
        "create_issue",
        "invite_teammate",
        "start_sprint",
        "use_cmdk",
    )


def get_or_create_onboarding(user, workspace) -> UserOnboarding:
    state, _ = UserOnboarding.objects.get_or_create(
        user=user,
        workspace=workspace,
        defaults={
            "checklist": {key: False for key in UserOnboarding.CHECKLIST_KEYS},
        },
    )
    return state
