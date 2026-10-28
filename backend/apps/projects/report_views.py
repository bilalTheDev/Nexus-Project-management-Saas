from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.projects.reports import (
    breakdown,
    burndown,
    cfd,
    created_vs_resolved,
    project_summary,
    sprint_report,
    velocity,
)
from apps.projects.sprint_models import Sprint
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.permissions import IsWorkspaceMember


class _ProjectReportMixin(WorkspaceScopedMixin):
    permission_classes = [IsWorkspaceMember]

    def get_project(self):
        return get_object_or_404(
            Project,
            workspace=self.workspace,
            key__iexact=self.kwargs["project_key"],
            archived_at__isnull=True,
        )


class BurndownReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        sprint = get_object_or_404(Sprint, project=project, pk=kwargs["sprint_id"])
        return Response(burndown(project, sprint))


class VelocityReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        return Response(velocity(self.get_project()))


class SprintReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        sprint = get_object_or_404(Sprint, project=project, pk=kwargs["sprint_id"])
        return Response(sprint_report(project, sprint))


class CfdReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        return Response(
            cfd(
                project,
                date.fromisoformat(date_from) if date_from else None,
                date.fromisoformat(date_to) if date_to else None,
            )
        )


class CreatedVsResolvedReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        return Response(created_vs_resolved(self.get_project()))


class BreakdownReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        by = request.query_params.get("by", "priority")
        if by not in {"priority", "assignee", "type"}:
            by = "priority"
        return Response(breakdown(self.get_project(), by=by))


class ProjectSummaryReportView(_ProjectReportMixin, APIView):
    def get(self, request, *args, **kwargs):
        return Response(project_summary(self.get_project()))
