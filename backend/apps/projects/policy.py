"""Action → minimum role mapping (workspace + project)."""

from apps.projects.governance_models import ProjectMembership
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.permissions import ADMIN_ROLES, MANAGER_ROLES, MUTATING_ROLES

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

# action → (min_workspace_role, min_project_role or None)
POLICY = {
    "project.read": (WorkspaceMembership.Role.VIEWER, ProjectMembership.Role.VIEWER),
    "project.write": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "issue.read": (WorkspaceMembership.Role.VIEWER, ProjectMembership.Role.VIEWER),
    "issue.write": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "issue.transition": (WorkspaceMembership.Role.MEMBER, ProjectMembership.Role.MEMBER),
    "sprint.manage": (WorkspaceMembership.Role.PROJECT_MANAGER, ProjectMembership.Role.ADMIN),
    "release.manage": (WorkspaceMembership.Role.PROJECT_MANAGER, ProjectMembership.Role.ADMIN),
    "workflow.manage": (WorkspaceMembership.Role.PROJECT_MANAGER, ProjectMembership.Role.ADMIN),
    "project.admin": (WorkspaceMembership.Role.ADMIN, ProjectMembership.Role.ADMIN),
}


def effective_permissions(*, workspace_role: str, project_role: str | None = None) -> dict:
    result = {}
    ws = WS_RANK.get(workspace_role, 0)
    pr = PR_RANK.get(project_role, 0) if project_role else 0
    for action, (min_ws, min_pr) in POLICY.items():
        ok_ws = ws >= WS_RANK.get(min_ws, 99)
        ok_pr = True
        if project_role is not None and min_pr is not None:
            ok_pr = pr >= PR_RANK.get(min_pr, 99)
        # Workspace admins/owners always allowed; else both checks
        if workspace_role in ADMIN_ROLES:
            result[action] = True
        else:
            result[action] = ok_ws and ok_pr
    result["can_mutate"] = workspace_role in MUTATING_ROLES and (
        project_role is None or project_role != ProjectMembership.Role.VIEWER
    )
    result["workspace_role"] = workspace_role
    result["project_role"] = project_role
    return result


def get_project_role(user, project) -> str | None:
    m = (
        ProjectMembership.objects.filter(project=project, user=user)
        .values_list("role", flat=True)
        .first()
    )
    return m
