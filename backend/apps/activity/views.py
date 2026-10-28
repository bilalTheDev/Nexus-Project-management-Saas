from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import ActivityEvent
from apps.activity.serializers import ActivityEventSerializer
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import IsWorkspaceMember


class ActivityFeedView(WorkspaceScopedMixin, ListAPIView):
    permission_classes = [IsWorkspaceMember]
    serializer_class = ActivityEventSerializer

    def get_queryset(self):
        qs = (
            ActivityEvent.objects.for_user(self.request.user).filter(
                workspace=self.workspace
            )
            .select_related("actor", "project", "task", "task__project")
            .order_by("-created_at")
        )
        event_type = self.request.query_params.get("event_type")
        project = self.request.query_params.get("project")
        search = self.request.query_params.get("search")
        days = self.request.query_params.get("days")
        if event_type:
            qs = qs.filter(event_type=event_type)
        if project:
            qs = qs.filter(project__key__iexact=project)
        if search:
            qs = qs.filter(
                Q(summary__icontains=search)
                | Q(actor__email__icontains=search)
                | Q(actor__first_name__icontains=search)
            )
        if days:
            try:
                qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=int(days)))
            except (TypeError, ValueError):
                pass
        return qs


class ActivityStatsView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        week_ago = timezone.now() - timedelta(days=7)
        events = ActivityEvent.objects.for_user(request.user).filter(
            workspace=self.workspace
        )
        week_count = events.filter(created_at__gte=week_ago).count()
        contributors = (
            events.filter(created_at__gte=week_ago, actor__isnull=False)
            .values("actor__id", "actor__first_name", "actor__last_name", "actor__email")
            .annotate(actions=Count("id"))
            .order_by("-actions")[:5]
        )
        return Response(
            {
                "week_events": week_count,
                "top_contributors": [
                    {
                        "id": c["actor__id"],
                        "full_name": f"{c['actor__first_name']} {c['actor__last_name']}".strip()
                        or c["actor__email"],
                        "email": c["actor__email"],
                        "actions": c["actions"],
                    }
                    for c in contributors
                ],
            }
        )
