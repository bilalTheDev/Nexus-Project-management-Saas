"""Workspace email invites — create, mail, and accept."""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.workspaces.models import WorkspaceInvite, WorkspaceMembership

logger = logging.getLogger("nexus.invites")
User = get_user_model()

INVITE_TTL_DAYS = 7


def invite_frontend_url(token: str) -> str:
    base = getattr(settings, "FRONTEND_ORIGIN", "http://127.0.0.1:5173").rstrip("/")
    return f"{base}/invite/{token}"


def _new_token() -> str:
    return secrets.token_urlsafe(32)


@transaction.atomic
def create_or_refresh_invite(*, workspace, email: str, role: str, invited_by) -> WorkspaceInvite:
    email = email.lower().strip()
    if role == WorkspaceMembership.Role.OWNER:
        raise ValidationError({"role": "Cannot invite someone as owner."})

    existing_member = (
        WorkspaceMembership.objects.select_related("user")
        .filter(workspace=workspace, user__email__iexact=email)
        .exclude(status=WorkspaceMembership.Status.REMOVED)
        .first()
    )
    if existing_member and existing_member.status == WorkspaceMembership.Status.ACTIVE:
        raise ValidationError({"email": "This user is already an active member."})

    invite = (
        WorkspaceInvite.objects.select_for_update()
        .filter(workspace=workspace, email__iexact=email, accepted_at__isnull=True)
        .first()
    )
    expires = timezone.now() + timedelta(days=INVITE_TTL_DAYS)
    if invite:
        invite.role = role
        invite.token = _new_token()
        invite.invited_by = invited_by
        invite.expires_at = expires
        invite.save(
            update_fields=["role", "token", "invited_by", "expires_at"]
        )
    else:
        invite = WorkspaceInvite.objects.create(
            workspace=workspace,
            email=email,
            role=role,
            token=_new_token(),
            invited_by=invited_by,
            expires_at=expires,
        )
    return invite


def send_invite_email(*, invite: WorkspaceInvite) -> bool:
    """Send invite email. Returns True if Django accepted the message for delivery."""
    url = invite_frontend_url(invite.token)
    subject = f"You're invited to {invite.workspace.name} on Nexus"
    body = (
        f"Hi,\n\n"
        f"{invite.invited_by.get_full_name() or invite.invited_by.email} "
        f"invited you to join the workspace \"{invite.workspace.name}\" "
        f"as {invite.get_role_display()}.\n\n"
        f"Accept the invite:\n{url}\n\n"
        f"This link expires on {invite.expires_at:%Y-%m-%d %H:%M UTC}.\n\n"
        f"- Nexus\n"
    )
    try:
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            fail_silently=False,
        )
        return bool(sent)
    except Exception:
        logger.exception("invite_email_failed", extra={"invite_id": str(invite.id)})
        return False


@transaction.atomic
def accept_invite(*, token: str, user) -> WorkspaceMembership:
    invite = (
        WorkspaceInvite.objects.select_for_update()
        .select_related("workspace")
        .filter(token=token)
        .first()
    )
    if invite is None or not invite.is_open:
        raise ValidationError({"detail": "This invite is invalid or has expired."})

    if user.email.lower() != invite.email.lower():
        raise ValidationError(
            {
                "detail": (
                    f"Sign in as {invite.email} to accept this invite "
                    "(or create an account with that email)."
                )
            }
        )

    membership = WorkspaceMembership.objects.filter(
        workspace=invite.workspace, user=user
    ).first()
    if membership is None:
        membership = WorkspaceMembership.objects.create(
            workspace=invite.workspace,
            user=user,
            role=invite.role,
            status=WorkspaceMembership.Status.ACTIVE,
            joined_at=timezone.now(),
        )
    else:
        membership.role = invite.role
        membership.status = WorkspaceMembership.Status.ACTIVE
        membership.joined_at = timezone.now()
        membership.save(update_fields=["role", "status", "joined_at"])

    invite.accepted_at = timezone.now()
    invite.save(update_fields=["accepted_at"])
    return membership
