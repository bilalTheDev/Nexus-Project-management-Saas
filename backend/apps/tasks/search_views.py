from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.tasks.querylang import parse_query
from apps.tasks.serializers import TaskListSerializer
from apps.workspaces.mixins import WorkspaceScopedMixin
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.permissions import IsWorkspaceMember


class IssueNavigatorView(WorkspaceScopedMixin, APIView):
    """Filter bar + optional query language. Filter state lives in the URL query string."""

    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        project_key = request.query_params.get("project")
        qs = Task.objects.filter(
            project__workspace=self.workspace, archived_at__isnull=True
        ).select_related(
            "project",
            "assignee",
            "workflow_status",
            "issue_type",
            "sprint",
        )

        if project_key:
            qs = qs.filter(project__key__iexact=project_key)

        for param, field in (
            ("type", "issue_type__key"),
            ("status", "workflow_status__key"),
            ("assignee", "assignee_id"),
            ("priority", "priority"),
            ("sprint", "sprint_id"),
        ):
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{field: value})

        label = request.query_params.get("label")
        if label:
            qs = qs.filter(labels__contains=[label])

        text = request.query_params.get("text")
        if text:
            qs = qs.filter(Q(title__icontains=text) | Q(description__icontains=text))

        created_from = request.query_params.get("created_from")
        created_to = request.query_params.get("created_to")
        if created_from:
            qs = qs.filter(created_at__date__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__date__lte=created_to)

        order = ["-updated_at"]
        jql = request.query_params.get("q")
        if jql:
            q_obj, order_by = parse_query(
                jql, current_user_email=request.user.email
            )
            qs = qs.filter(q_obj)
            if order_by:
                order = order_by

        qs = qs.order_by(*order)

        try:
            page_size = min(int(request.query_params.get("page_size", 50)), 100)
        except ValueError:
            page_size = 50
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        items = list(qs[start:end])
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": TaskListSerializer(items, many=True).data,
            }
        )


class GlobalSearchView(WorkspaceScopedMixin, APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, *args, **kwargs):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"issues": [], "projects": [], "people": []})

        issue_filter = Q(title__icontains=q)
        if q.isdigit():
            issue_filter = issue_filter | Q(number=int(q))

        issues = (
            Task.objects.filter(
                project__workspace=self.workspace,
                archived_at__isnull=True,
            )
            .filter(issue_filter)
            .select_related("project")[:10]
        )

        projects = Project.objects.filter(
            workspace=self.workspace, archived_at__isnull=True
        ).filter(Q(name__icontains=q) | Q(key__icontains=q))[:8]

        people = (
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                status=WorkspaceMembership.Status.ACTIVE,
            )
            .filter(
                Q(user__email__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
            )
            .select_related("user")[:8]
        )

        return Response(
            {
                "issues": [
                    {
                        "id": str(i.id),
                        "key": i.issue_key,
                        "title": i.title,
                        "project_key": i.project.key,
                    }
                    for i in issues
                ],
                "projects": [
                    {"id": str(p.id), "key": p.key, "name": p.name} for p in projects
                ],
                "people": [
                    {
                        "id": str(m.user_id),
                        "email": m.user.email,
                        "name": m.user.full_name,
                    }
                    for m in people
                ],
            }
        )
