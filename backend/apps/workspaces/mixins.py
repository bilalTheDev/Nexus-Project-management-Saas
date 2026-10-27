"""Shared view mixins for workspace-scoped endpoints."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from apps.workspaces.models import Workspace
from apps.workspaces.permissions import get_membership


class WorkspaceScopedMixin:
    """Resolve workspace membership before DRF permission checks."""

    workspace_url_kwarg = "slug"

    def initial(self, request, *args, **kwargs):
        slug = kwargs.get(self.workspace_url_kwarg) or self.kwargs.get(
            self.workspace_url_kwarg
        )
        self.workspace = get_object_or_404(Workspace, slug=slug, archived_at__isnull=True)
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise PermissionDenied("You are not a member of this workspace.")
        super().initial(request, *args, **kwargs)
