"""Action → minimum role mapping (workspace + project)."""

from apps.projects.governance_models import ProjectMembership
from apps.workspaces.models import WorkspaceMembership

# Workspace role ranks
WS_RANK = {
    WorkspaceMembership.Role.VIEWER: 10,
    WorkspaceMembership.Role.MEMBER: 20,
    WorkspaceMembership.Role.PROJECT_MANAGER: 30,
    WorkspaceMembership.Role.ADMIN: 40,
    WorkspaceMembership.Role.OWNER: 50,
}

# Project role ranks
PR_RANK = {
    ProjectMembership.Role.VIEWER: 10,
    ProjectMembership.Role.MEMBER: 20,
    ProjectMembership.Role.ADMIN: 30,
}

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

# action → (min_workspace_role, min_project_role or None)
POLICY = {
    "project.read": (WorkspaceMembership.Role.VIEWER, ProjectMembership.Role.VIEWER),
    "project.write": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "issue.read": (WorkspaceMembership.Role.VIEWER, ProjectMembership.Role.VIEWER),
    "issue.write": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "issue.transition": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "sprint.manage": (
        WorkspaceMembership.Role.PROJECT_MANAGER,
        ProjectMembership.Role.ADMIN,
    ),
    "release.manage": (
        WorkspaceMembership.Role.PROJECT_MANAGER,
        ProjectMembership.Role.ADMIN,
    ),
    "workflow.manage": (
        WorkspaceMembership.Role.PROJECT_MANAGER,
        ProjectMembership.Role.ADMIN,
    ),
    "project.admin": (WorkspaceMembership.Role.ADMIN, ProjectMembership.Role.ADMIN),
    "workspace.admin": (WorkspaceMembership.Role.ADMIN, None),
    "workspace.owner": (WorkspaceMembership.Role.OWNER, None),
    "member.manage": (WorkspaceMembership.Role.ADMIN, None),
}


def can(
    action: str,
    *,
    workspace_role: str,
    project_role: str | None = None,
) -> bool:
    """Return whether the given roles may perform ``action`` per POLICY."""
    if action not in POLICY:
        return False
    min_ws, min_pr = POLICY[action]
    ws = WS_RANK.get(workspace_role, 0)
    if workspace_role in ADMIN_ROLES and action != "workspace.owner":
        if min_ws == WorkspaceMembership.Role.OWNER:
            return workspace_role == WorkspaceMembership.Role.OWNER
        return True
    if ws < WS_RANK.get(min_ws, 99):
        return False
    if min_pr is None:
        return True
    if project_role is None:
        if min_pr == ProjectMembership.Role.VIEWER:
            return True
        if min_pr == ProjectMembership.Role.MEMBER:
            return workspace_role in MUTATING_ROLES
        return ws >= WS_RANK.get(WorkspaceMembership.Role.PROJECT_MANAGER, 99)
    pr = PR_RANK.get(project_role, 0)
    return pr >= PR_RANK.get(min_pr, 99)


def effective_permissions(*, workspace_role: str, project_role: str | None = None) -> dict:
    result = {}
    for action in POLICY:
        result[action] = can(
            action, workspace_role=workspace_role, project_role=project_role
        )
    result["can_mutate"] = workspace_role in MUTATING_ROLES and (
        project_role is None or project_role != ProjectMembership.Role.VIEWER
    )
    result["workspace_role"] = workspace_role
    result["project_role"] = project_role
    return result


def get_project_role(user, project) -> str | None:
    if project is None or user is None:
        return None
    return (
        ProjectMembership.objects.filter(project=project, user=user)
        .values_list("role", flat=True)
        .first()
    )
