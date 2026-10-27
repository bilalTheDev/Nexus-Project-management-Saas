from django.urls import path

from apps.workspaces.views import (
    MembershipDetailView,
    MembershipListCreateView,
    MembershipStatsView,
    OwnershipTransferView,
    WorkspaceDashboardView,
    WorkspaceDetailView,
    WorkspaceListCreateView,
)

urlpatterns = [
    path("workspaces/", WorkspaceListCreateView.as_view(), name="workspace-list"),
    path(
        "workspaces/<slug:slug>/",
        WorkspaceDetailView.as_view(),
        name="workspace-detail",
    ),
    path(
        "workspaces/<slug:slug>/dashboard/",
        WorkspaceDashboardView.as_view(),
        name="workspace-dashboard",
    ),
    path(
        "workspaces/<slug:slug>/members/",
        MembershipListCreateView.as_view(),
        name="workspace-members",
    ),
    path(
        "workspaces/<slug:slug>/members/stats/",
        MembershipStatsView.as_view(),
        name="workspace-members-stats",
    ),
    path(
        "workspaces/<slug:slug>/members/<uuid:membership_id>/",
        MembershipDetailView.as_view(),
        name="workspace-member-detail",
    ),
    path(
        "workspaces/<slug:slug>/transfer-ownership/",
        OwnershipTransferView.as_view(),
        name="workspace-transfer-ownership",
    ),
]
