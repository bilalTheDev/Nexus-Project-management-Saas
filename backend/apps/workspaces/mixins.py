"""Shared view mixins for workspace-scoped endpoints."""

from django.http import Http404

from apps.workspaces.models import Workspace
from apps.workspaces.permissions import get_membership


class WorkspaceScopedMixin:
    """
    Resolve workspace via the requesting user's ACTIVE memberships.

    Missing workspace and forbidden (no membership) both surface as 404 so
    tenants cannot probe for foreign workspace existence by slug.
    """

    workspace_url_kwarg = "slug"

    def initial(self, request, *args, **kwargs):
        slug = kwargs.get(self.workspace_url_kwarg) or self.kwargs.get(
            self.workspace_url_kwarg
        )
        workspace = (
            Workspace.objects.for_user(request.user)
            .filter(slug=slug, archived_at__isnull=True)
            .first()
        )
        if workspace is None:
            # Uniform 404 for unknown slug and non-member (hide tenant existence).
            raise Http404("Workspace not found.")
        self.workspace = workspace
        self.membership = get_membership(request.user, self.workspace)
        if self.membership is None:
            raise Http404("Workspace not found.")
        super().initial(request, *args, **kwargs)

    def get_scoped_queryset(self, qs):
        """Apply ``for_user`` when the queryset supports it."""
        if hasattr(qs, "for_user"):
            return qs.for_user(self.request.user)
        return qs
