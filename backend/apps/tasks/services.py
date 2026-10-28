"""Issue mutations: transitions, history, links, concurrency."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.workflow_models import Transition
from apps.tasks.models import IssueChange, IssueLink, Task


TRACKED_FIELDS = (
    "title",
    "description",
    "status",
    "priority",
    "assignee_id",
    "reporter_id",
    "due_date",
    "labels",
    "resolution",
    "sprint_id",
    "parent_id",
    "issue_type_id",
    "workflow_status_id",
    "story_points",
)


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        import json

        return json.dumps(value, default=str, sort_keys=True)
    return str(value)


def record_changes(*, issue: Task, actor, before: dict, after: dict) -> list[IssueChange]:
    rows = []
    for field in TRACKED_FIELDS:
        old = before.get(field)
        new = after.get(field)
        if _stringify(old) == _stringify(new):
            continue
        rows.append(
            IssueChange(
                issue=issue,
                field=field,
                old_value=_stringify(old)[:4000],
                new_value=_stringify(new)[:4000],
                actor=actor,
            )
        )
    if rows:
        IssueChange.objects.bulk_create(rows)
    return rows


def snapshot_issue(issue: Task) -> dict:
    return {field: getattr(issue, field, None) for field in TRACKED_FIELDS}


def allowed_transitions(issue: Task) -> list[Transition]:
    if not issue.workflow_status_id:
        return []
    return list(
        Transition.objects.filter(
            project=issue.project,
            from_status_id=issue.workflow_status_id,
        ).select_related("from_status", "to_status")
    )


def _run_validators(transition: Transition, issue: Task, *, comment: str | None) -> None:
    for rule in transition.validators or []:
        if rule == Transition.Validator.REQUIRE_ASSIGNEE and not issue.assignee_id:
            raise ValidationError(
                {"detail": "This transition requires an assignee.", "code": "require_assignee"}
            )
        if rule == Transition.Validator.REQUIRE_RESOLUTION and not issue.resolution:
            raise ValidationError(
                {
                    "detail": "This transition requires a resolution.",
                    "code": "require_resolution",
                }
            )
        if rule == Transition.Validator.REQUIRE_COMMENT and not (comment or "").strip():
            raise ValidationError(
                {"detail": "This transition requires a comment.", "code": "require_comment"}
            )


@transaction.atomic
def apply_transition(
    *,
    issue: Task,
    transition_id,
    actor,
    comment: str | None = None,
    expected_version: int | None = None,
) -> Task:
    # Lock the issue row only — nullable FKs cannot be used with FOR UPDATE on Postgres.
    issue = Task.objects.select_for_update().get(pk=issue.pk)
    issue = Task.objects.select_related(
        "project", "project__workspace", "workflow_status", "issue_type"
    ).get(pk=issue.pk)

    if expected_version is not None and issue.version != expected_version:
        raise ValidationError(
            {
                "detail": "This issue changed. Reload?",
                "code": "version_conflict",
                "version": issue.version,
            }
        )

    try:
        transition = Transition.objects.select_related("from_status", "to_status").get(
            pk=transition_id, project=issue.project
        )
    except Transition.DoesNotExist as exc:
        raise ValidationError(
            {"detail": "Unknown transition for this project.", "code": "invalid_transition"}
        ) from exc

    if issue.workflow_status_id != transition.from_status_id:
        from rest_framework.exceptions import APIException

        class Conflict(APIException):
            status_code = 409
            default_detail = "That move is not allowed from the current status."
            default_code = "invalid_transition"

        current = (
            issue.workflow_status.name if issue.workflow_status else issue.status
        )
        raise Conflict(
            detail={
                "detail": (
                    f"Cannot move from {current} to {transition.to_status.name}. "
                    "No matching transition for this project workflow."
                ),
                "code": "invalid_transition",
            }
        )

    _run_validators(transition, issue, comment=comment)

    before = snapshot_issue(issue)
    old_status = issue.status
    issue.workflow_status = transition.to_status
    issue.status = transition.to_status.key
    if transition.to_status.category == "done":
        if not issue.completed_at:
            issue.completed_at = timezone.now()
    else:
        issue.completed_at = None
    issue.version += 1
    issue.save()

    after = snapshot_issue(issue)
    record_changes(issue=issue, actor=actor, before=before, after=after)
    log_activity(
        workspace=issue.project.workspace,
        event_type=ActivityEvent.EventType.TASK_STATUS_CHANGED,
        actor=actor,
        project=issue.project,
        task=issue,
        summary=f"Transitioned {issue.issue_key} via {transition.name}",
        metadata={"from": old_status, "to": issue.status, "transition": transition.name},
    )
    if issue.assignee_id and issue.assignee_id != getattr(actor, "id", None):
        from apps.projects.governance_models import Notification
        from apps.projects.governance_views import notify_once

        # Reload assignee if only id was present.
        recipient = issue.assignee
        if recipient is None and issue.assignee_id:
            from django.contrib.auth import get_user_model

            recipient = get_user_model().objects.filter(pk=issue.assignee_id).first()
        if recipient is not None:
            notify_once(
                workspace=issue.project.workspace,
                recipient=recipient,
                actor=actor,
                kind=Notification.Kind.STATUS_CHANGED,
                title=f"{issue.issue_key} → {transition.to_status.name}",
                body=issue.title,
                link=(
                    f"/app/{issue.project.workspace.slug}/issues/{issue.id}"
                ),
                dedupe_key=(
                    f"status:{issue.id}:{old_status}:{issue.status}:{issue.version}"
                ),
            )
    return issue


@transaction.atomic
def create_issue_link(*, source: Task, target: Task, link_type: str, actor) -> tuple[IssueLink, IssueLink]:
    if source.project_id != target.project_id:
        raise ValidationError({"detail": "Linked issues must share a project."})
    if source.pk == target.pk:
        raise ValidationError({"detail": "An issue cannot link to itself."})
    if link_type not in IssueLink.LinkType.values:
        raise ValidationError({"link_type": "Unsupported link type."})

    forward, _ = IssueLink.objects.get_or_create(
        source=source,
        target=target,
        link_type=link_type,
        defaults={"created_by": actor},
    )
    inverse_type = IssueLink.INVERSE[link_type]
    inverse, _ = IssueLink.objects.get_or_create(
        source=target,
        target=source,
        link_type=inverse_type,
        defaults={"created_by": actor},
    )
    return forward, inverse


def epic_progress(epic: Task) -> dict:
    children = Task.objects.filter(parent=epic, archived_at__isnull=True)
    total = children.count()
    done = children.filter(
        workflow_status__category="done"
    ).count() if total else children.filter(status=Task.Status.DONE).count()
    return {"total": total, "done": done, "label": f"{done} of {total} done"}
