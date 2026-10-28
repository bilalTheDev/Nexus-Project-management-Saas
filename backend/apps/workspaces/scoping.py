"""Workspace-scoped querysets — every tenant object lookup goes through these."""

from django.db import models


def active_membership_workspace_ids(user):
    """Subquery of workspace PKs where ``user`` has an ACTIVE membership."""
    from apps.workspaces.models import WorkspaceMembership

    if not user or not getattr(user, "is_authenticated", False):
        return WorkspaceMembership.objects.none().values("workspace_id")
    return WorkspaceMembership.objects.filter(
        user=user,
        status=WorkspaceMembership.Status.ACTIVE,
    ).values("workspace_id")


class WorkspaceScopedQuerySet(models.QuerySet):
    """
    Base queryset that filters rows to the requesting user's ACTIVE memberships.

    Subclasses set ``workspace_filter`` to the ORM path that reaches Workspace.id
    (e.g. ``"id"`` for Workspace, ``"workspace_id"`` for Project,
    ``"project__workspace_id"`` for Task).
    """

    workspace_filter = "workspace_id"

    def for_user(self, user):
        if not user or not getattr(user, "is_authenticated", False):
            return self.none()
        return self.filter(
            **{f"{self.workspace_filter}__in": active_membership_workspace_ids(user)}
        )


class WorkspaceQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "id"


class ProjectScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "workspace_id"


class TaskScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "project__workspace_id"


class CommentScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "task__project__workspace_id"


class ActivityScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "workspace_id"


class MembershipScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "workspace_id"


class NotificationScopedQuerySet(WorkspaceScopedQuerySet):
    workspace_filter = "workspace_id"


class ProjectChildScopedQuerySet(WorkspaceScopedQuerySet):
    """Sprint, Release, Component, WorkflowStatus, etc."""

    workspace_filter = "project__workspace_id"
