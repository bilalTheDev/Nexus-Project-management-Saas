"""Tenant membership helpers and DRF permission classes."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.workspaces.models import WorkspaceMembership

ADMIN_ROLES = {
    WorkspaceMembership.Role.OWNER,
    WorkspaceMembership.Role.ADMIN,
}

MANAGER_ROLES = ADMIN_ROLES | {
    WorkspaceMembership.Role.PROJECT_MANAGER,
}

MUTATING_ROLES = MANAGER_ROLES | {
    WorkspaceMembership.Role.MEMBER,
}


def get_membership(user, workspace) -> WorkspaceMembership | None:
    if not user or not user.is_authenticated:
        return None
    return (
        WorkspaceMembership.objects.select_related("workspace", "user")
        .filter(
            workspace=workspace,
            user=user,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        .first()
    )


def user_workspaces_qs(user):
    return (
        WorkspaceMembership.objects.filter(
            user=user,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        .select_related("workspace")
        .prefetch_related("workspace__memberships")
    )


def default_workspace_slug(user) -> str | None:
    membership = (
        WorkspaceMembership.objects.filter(
            user=user,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        .select_related("workspace")
        .order_by("joined_at", "created_at")
        .first()
    )
    return membership.workspace.slug if membership else None


class IsWorkspaceMember(BasePermission):
    """Requires an active membership on the workspace resolved by the view."""

    def has_permission(self, request, view):
        workspace = getattr(view, "workspace", None)
        if workspace is None:
            return False
        membership = get_membership(request.user, workspace)
        view.membership = membership
        return membership is not None


class IsWorkspaceAdmin(BasePermission):
    def has_permission(self, request, view):
        membership = getattr(view, "membership", None) or get_membership(
            request.user, getattr(view, "workspace", None)
        )
        view.membership = membership
        return bool(membership and membership.role in ADMIN_ROLES)


class CanMutateWorkspaceContent(BasePermission):
    """Viewers are read-only; members+ can mutate content."""

    def has_permission(self, request, view):
        membership = getattr(view, "membership", None) or get_membership(
            request.user, getattr(view, "workspace", None)
        )
        view.membership = membership
        if membership is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return membership.role in MUTATING_ROLES
