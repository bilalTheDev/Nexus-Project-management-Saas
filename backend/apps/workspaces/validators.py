"""Shared serializer validators for same-workspace FK integrity."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.projects.models import Project
from apps.projects.sprint_models import Sprint
from apps.tasks.models import Task
from apps.workspaces.models import WorkspaceMembership

User = get_user_model()


def require_workspace(context) -> "object":
    workspace = context.get("workspace")
    if workspace is not None:
        return workspace
    project = context.get("project")
    if project is not None:
        return project.workspace
    task = context.get("task")
    if task is not None:
        return task.project.workspace
    raise serializers.ValidationError(
        "Workspace context is required for cross-tenant FK validation."
    )


def validate_assignee_in_workspace(assignee_id, workspace):
    """Assignee must be an ACTIVE member of the same workspace (User PK is int)."""
    if assignee_id is None:
        return None
    try:
        user_id = int(assignee_id)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError(
            {"assignee_id": "Invalid user id."}
        ) from exc
    ok = WorkspaceMembership.objects.filter(
        workspace=workspace,
        user_id=user_id,
        status=WorkspaceMembership.Status.ACTIVE,
    ).exists()
    if not ok:
        raise serializers.ValidationError(
            {"assignee_id": "Assignee must be an active member of this workspace."}
        )
    return user_id


def validate_user_in_workspace(user_id, workspace, *, field="user_id"):
    if user_id is None:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError({field: "Invalid user id."}) from exc
    ok = WorkspaceMembership.objects.filter(
        workspace=workspace,
        user_id=uid,
        status=WorkspaceMembership.Status.ACTIVE,
    ).exists()
    if not ok:
        raise serializers.ValidationError(
            {field: "User must be an active member of this workspace."}
        )
    return uid


def validate_project_in_workspace(project_id, workspace):
    if project_id is None:
        return None
    project = Project.objects.filter(pk=project_id, workspace=workspace).first()
    if project is None:
        raise serializers.ValidationError(
            {"project_id": "Project must belong to this workspace."}
        )
    return project


def validate_parent_in_workspace(parent_id, workspace, *, project=None):
    if parent_id is None:
        return None
    qs = Task.objects.filter(pk=parent_id, project__workspace=workspace)
    if project is not None:
        qs = qs.filter(project=project)
    parent = qs.first()
    if parent is None:
        raise serializers.ValidationError(
            {"parent_id": "Parent issue must belong to the same workspace."}
        )
    return parent


def validate_sprint_in_workspace(sprint_id, workspace, *, project=None):
    if sprint_id is None:
        return None
    qs = Sprint.objects.filter(pk=sprint_id, project__workspace=workspace)
    if project is not None:
        qs = qs.filter(project=project)
    sprint = qs.first()
    if sprint is None:
        raise serializers.ValidationError(
            {"sprint_id": "Sprint must belong to the same workspace."}
        )
    return sprint


def validate_labels_in_workspace(labels, workspace):
    """
    Labels are free-form strings on Task today; keep hook for future Label model.
    Reject non-list / oversized payloads only.
    """
    if labels is None:
        return None
    if not isinstance(labels, list):
        raise serializers.ValidationError({"labels": "Labels must be a list of strings."})
    cleaned = []
    for item in labels:
        if not isinstance(item, str):
            raise serializers.ValidationError({"labels": "Each label must be a string."})
        text = item.strip()
        if text:
            cleaned.append(text[:64])
    return cleaned


def validate_same_workspace_fks(attrs, context, *, project=None):
    """
    Validate every tenant FK present in ``attrs`` belongs to the same workspace.

    Covers: assignee_id, reporter_id, lead_id, default_assignee_id,
    parent_id, sprint_id, project_id, and labels.
    """
    workspace = require_workspace(context)
    project = project or context.get("project")

    if "assignee_id" in attrs:
        attrs["assignee_id"] = validate_assignee_in_workspace(
            attrs.get("assignee_id"), workspace
        )
    for field in ("reporter_id", "lead_id", "default_assignee_id"):
        if field in attrs:
            attrs[field] = validate_user_in_workspace(
                attrs.get(field), workspace, field=field
            )
    if "parent_id" in attrs:
        parent = validate_parent_in_workspace(
            attrs.get("parent_id"), workspace, project=project
        )
        # Keep id form for callers that pop parent_id
        if parent is not None:
            attrs["parent_id"] = parent.pk
    if "sprint_id" in attrs:
        sprint = validate_sprint_in_workspace(
            attrs.get("sprint_id"), workspace, project=project
        )
        if sprint is not None:
            attrs["sprint_id"] = sprint.pk
    if "project_id" in attrs:
        validate_project_in_workspace(attrs.get("project_id"), workspace)
    if "labels" in attrs:
        attrs["labels"] = validate_labels_in_workspace(attrs.get("labels"), workspace)
    return attrs
