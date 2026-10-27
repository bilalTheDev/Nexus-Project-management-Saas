from django.urls import path

from apps.activity.views import ActivityFeedView, ActivityStatsView

urlpatterns = [
    path(
        "workspaces/<slug:slug>/activity/",
        ActivityFeedView.as_view(),
        name="workspace-activity",
    ),
    path(
        "workspaces/<slug:slug>/activity/stats/",
        ActivityStatsView.as_view(),
        name="workspace-activity-stats",
    ),
]
