"""Measure SQL query counts/time for hot endpoints against seeded load."""

from __future__ import annotations

import json
import time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, reset_queries
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from apps.activity.views import ActivityFeedView
from apps.tasks.views import BoardTasksView, MyTasksView, ProjectTaskListCreateView
from apps.workspaces.models import Workspace
from apps.workspaces.views import WorkspaceDashboardView
from apps.projects.views import ProjectListCreateView

User = get_user_model()
SLUG = "perf-baseline"


class Command(BaseCommand):
    help = "Capture query counts and wall time for dashboard/board/list/activity/my-tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="docs/perf_query_capture.json",
            help="Relative to repo root.",
        )

    def handle(self, *args, **options):
        workspace = Workspace.objects.filter(slug=SLUG).first()
        if workspace is None:
            raise CommandError("Run seed_perf_load first.")

        user = User.objects.filter(email="perf.baseline@example.com").first()
        if user is None:
            raise CommandError("perf.baseline@example.com missing — re-run seed_perf_load.")

        project = workspace.projects.filter(archived_at__isnull=True).order_by("key").first()
        if project is None:
            raise CommandError("No projects in perf-baseline.")

        factory = APIRequestFactory()
        results = {}

        def measure(label, view_cls, method, path_name, kwargs, query_params=None):
            path = reverse(path_name, kwargs=kwargs)
            request = factory.generic(
                method,
                path,
                data=query_params,
                HTTP_HOST="127.0.0.1",
            )
            force_authenticate(request, user=user)
            token = RefreshToken.for_user(user)
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token.access_token}"
            view = view_cls.as_view()
            reset_queries()
            with CaptureQueriesContext(connection) as ctx:
                t0 = time.perf_counter()
                response = view(request, **kwargs)
                if hasattr(response, "render"):
                    response.render()
                elapsed_ms = (time.perf_counter() - t0) * 1000
            # Django stores time as seconds string
            sql_time_ms = sum(float(q["time"]) * 1000 for q in ctx.captured_queries)
            top = sorted(
                ctx.captured_queries,
                key=lambda q: float(q["time"]),
                reverse=True,
            )[:5]
            results[label] = {
                "status": getattr(response, "status_code", None),
                "query_count": len(ctx),
                "wall_ms": round(elapsed_ms, 2),
                "sql_ms": round(sql_time_ms, 2),
                "top_queries": [
                    {"time_ms": round(float(q["time"]) * 1000, 2), "sql": q["sql"][:500]}
                    for q in top
                ],
            }
            self.stdout.write(
                f"{label}: status={results[label]['status']} "
                f"queries={results[label]['query_count']} "
                f"wall={results[label]['wall_ms']}ms "
                f"sql={results[label]['sql_ms']}ms"
            )

        # DEBUG must be True for connection.queries; CaptureQueriesContext forces it.
        measure(
            "dashboard",
            WorkspaceDashboardView,
            "GET",
            "workspace-dashboard",
            {"slug": SLUG},
        )
        measure(
            "project_list",
            ProjectListCreateView,
            "GET",
            "project-list",
            {"slug": SLUG},
        )
        measure(
            "board",
            BoardTasksView,
            "GET",
            "project-board",
            {"slug": SLUG, "project_key": project.key},
        )
        measure(
            "task_list",
            ProjectTaskListCreateView,
            "GET",
            "project-tasks",
            {"slug": SLUG, "project_key": project.key},
        )
        measure(
            "my_tasks",
            MyTasksView,
            "GET",
            "my-tasks",
            {"slug": SLUG},
        )
        measure(
            "activity",
            ActivityFeedView,
            "GET",
            "workspace-activity",
            {"slug": SLUG},
        )

        # EXPLAIN ANALYZE for the three slowest SQL statements across captures
        slowest = []
        for label, payload in results.items():
            for q in payload["top_queries"]:
                slowest.append({**q, "endpoint": label})
        slowest.sort(key=lambda x: x["time_ms"], reverse=True)
        explain = []
        for item in slowest[:3]:
            sql = item["sql"]
            entry = {"endpoint": item["endpoint"], "time_ms": item["time_ms"], "sql": sql}
            if connection.vendor == "postgresql":
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS) {sql}")
                        entry["explain"] = "\n".join(row[0] for row in cursor.fetchall())
                except Exception as exc:  # noqa: BLE001 — baseline capture must not abort
                    entry["explain_error"] = str(exc)
            else:
                entry["explain"] = (
                    f"skipped: vendor={connection.vendor} "
                    "(re-run against Neon Postgres for EXPLAIN ANALYZE)"
                )
            explain.append(entry)

        out = {
            "workspace": SLUG,
            "project_key": project.key,
            "db_vendor": connection.vendor,
            "endpoints": results,
            "explain_top3": explain,
        }
        repo_root = Path(__file__).resolve().parents[5]
        out_path = repo_root / options["out"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {out_path}"))
