"""Workspace membership lifecycle services (ownership, last-owner guards)."""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.workspaces.models import WorkspaceMembership


def count_active_owners(workspace) -> int:
    return WorkspaceMembership.objects.filter(
        workspace=workspace,
        role=WorkspaceMembership.Role.OWNER,
        status=WorkspaceMembership.Status.ACTIVE,
    ).count()


def assert_can_remove_membership(*, workspace, membership, actor_membership):
    """Raise if removing this membership would leave the workspace without an owner."""
    if membership.role != WorkspaceMembership.Role.OWNER:
        return
    if membership.status != WorkspaceMembership.Status.ACTIVE:
        return
    if count_active_owners(workspace) <= 1:
        raise ValidationError(
            {"detail": "Cannot remove the final workspace owner."}
        )


def assert_can_demote_owner(*, workspace, membership, new_role):
    if membership.role != WorkspaceMembership.Role.OWNER:
        return
    if new_role == WorkspaceMembership.Role.OWNER:
        return
    if count_active_owners(workspace) <= 1:
        raise ValidationError(
            {"role": "Cannot demote the final workspace owner. Transfer ownership first."}
        )


@transaction.atomic
def transfer_ownership(*, workspace, current_owner_membership, target_email: str, actor):
    """
    Transfer workspace ownership under row locks.

    Locks both membership rows with select_for_update so concurrent transfers
    and last-owner removals cannot race.
    """
    if current_owner_membership.role != WorkspaceMembership.Role.OWNER:
        raise PermissionDenied("Only the current owner can transfer ownership.")

    owner_row = (
        WorkspaceMembership.objects.select_for_update()
        .select_related("user")
        .get(pk=current_owner_membership.pk)
    )
    if owner_row.role != WorkspaceMembership.Role.OWNER:
        raise PermissionDenied("Only the current owner can transfer ownership.")

    target = (
        WorkspaceMembership.objects.select_for_update()
        .select_related("user")
        .filter(
            workspace=workspace,
            user__email__iexact=target_email,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        .first()
    )
    if target is None:
        raise ValidationError({"email": "Target user is not an active member."})
    if target.user_id == actor.id:
        raise ValidationError({"email": "You already own this workspace."})

    owner_row.role = WorkspaceMembership.Role.ADMIN
    owner_row.save(update_fields=["role"])
    target.role = WorkspaceMembership.Role.OWNER
    target.save(update_fields=["role"])

    log_activity(
        workspace=workspace,
        event_type=ActivityEvent.EventType.MEMBER_ROLE_CHANGED,
        actor=actor,
        summary=f"Transferred ownership to {target.user.email}",
    )
    return target


@transaction.atomic
def soft_remove_membership(*, workspace, membership, actor_membership):
    """Mark membership REMOVED with last-owner protection under a row lock."""
    locked = (
        WorkspaceMembership.objects.select_for_update()
        .select_related("user")
        .get(pk=membership.pk, workspace=workspace)
    )
    assert_can_remove_membership(
        workspace=workspace,
        membership=locked,
        actor_membership=actor_membership,
    )
    locked.status = WorkspaceMembership.Status.REMOVED
    locked.save(update_fields=["status"])
    return locked
