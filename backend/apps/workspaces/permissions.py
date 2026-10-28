"""Tenant membership helpers and DRF permission classes."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.projects.policy import (
    ADMIN_ROLES,
    MANAGER_ROLES,
    MUTATING_ROLES,
    PR_RANK,
    WS_RANK,
    can as policy_can,
)
from apps.workspaces.models import WorkspaceMembership

# Re-export role sets for existing imports across the codebase.
__all__ = [
    "ADMIN_ROLES",
    "MANAGER_ROLES",
    "MUTATING_ROLES",
    "get_membership",
    "user_workspaces_qs",
    "default_workspace_slug",
    "IsWorkspaceMember",
    "IsWorkspaceAdmin",
    "CanMutateWorkspaceContent",
    "HasWorkspaceRole",
    "HasProjectRole",
]


def get_membership(user, workspace) -> WorkspaceMembership | None:
    if not user or not user.is_authenticated or workspace is None:
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


def _role_at_least(role: str | None, min_role: str, ranks: dict) -> bool:
    if role is None:
        return False
    return ranks.get(role, 0) >= ranks.get(min_role, 99)


class IsWorkspaceMember(BasePermission):
    """Requires an active membership on the workspace resolved by the view."""

    def has_permission(self, request, view):
        workspace = getattr(view, "workspace", None)
        if workspace is None:
            return False
        membership = getattr(view, "membership", None) or get_membership(
            request.user, workspace
        )
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


def HasWorkspaceRole(min_role: str):
    """Factory: require workspace role rank >= ``min_role``."""

    class _HasWorkspaceRole(BasePermission):
        message = "Insufficient workspace role."

        def has_permission(self, request, view):
            membership = getattr(view, "membership", None) or get_membership(
                request.user, getattr(view, "workspace", None)
            )
            view.membership = membership
            if membership is None:
                return False
            return _role_at_least(membership.role, min_role, WS_RANK)

    _HasWorkspaceRole.__name__ = f"HasWorkspaceRole_{min_role}"
    return _HasWorkspaceRole


def HasProjectRole(min_role: str):
    """
    Factory: require project role rank >= ``min_role``.

    Workspace OWNER/ADMIN always pass. Prefer ``view.policy_action`` when set
    so the POLICY matrix is the single source of truth.
    """

    class _HasProjectRole(BasePermission):
        message = "Insufficient project role."

        def has_permission(self, request, view):
            membership = getattr(view, "membership", None) or get_membership(
                request.user, getattr(view, "workspace", None)
            )
            view.membership = membership
            if membership is None:
                return False
            if membership.role in ADMIN_ROLES:
                return True

            project = getattr(view, "project", None)
            if project is None and hasattr(view, "get_project"):
                try:
                    project = view.get_project()
                    view.project = project
                except Exception:
                    project = None

            from apps.projects.policy import get_project_role

            action = getattr(view, "policy_action", None)
            if action:
                project_role = (
                    get_project_role(request.user, project) if project else None
                )
                return policy_can(
                    action,
                    workspace_role=membership.role,
                    project_role=project_role,
                )

            if project is None:
                return _role_at_least(membership.role, min_role, WS_RANK)

            project_role = get_project_role(request.user, project)
            if project_role is None:
                return membership.role in MUTATING_ROLES and min_role in (
                    "viewer",
                    "member",
                )
            return _role_at_least(project_role, min_role, PR_RANK)

    _HasProjectRole.__name__ = f"HasProjectRole_{min_role}"
    return _HasProjectRole
