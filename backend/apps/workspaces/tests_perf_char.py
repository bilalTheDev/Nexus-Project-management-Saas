"""Characterisation baselines for hot read paths (query counts).

These assert upper bounds so Phase 3 refactors cannot silently regress.
Counts measured on SQLite with a small fixture — Neon baselines live in
docs/PERF_BASELINE.md under seeded load.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.projects.templates import apply_template
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()


class HotPathQueryCharacterisationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="perfowner@example.com",
            password="TestPass1",
            username="perfowner",
        )
        cls.workspace = Workspace.objects.create(
            name="Perf Char", slug="perf-char", created_by=cls.owner
        )
        WorkspaceMembership.objects.create(
            workspace=cls.workspace,
            user=cls.owner,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        cls.project = Project.objects.create(
            workspace=cls.workspace,
            name="Char Board",
            key="CHR",
            created_by=cls.owner,
        )
        apply_template(cls.project, "kanban")
        todo = cls.project.workflow_statuses.get(key="todo")
        issue_type = cls.project.issue_types.filter(hierarchy_level=0).first()
        tasks = []
        for i in range(1, 31):
            tasks.append(
                Task(
                    project=cls.project,
                    number=i,
                    title=f"Char task {i}",
                    status=Task.Status.TODO,
                    workflow_status=todo,
                    issue_type=issue_type,
                    assignee=cls.owner if i % 2 == 0 else None,
                    created_by=cls.owner,
                    position=i * 1000,
                )
            )
        Task.objects.bulk_create(tasks)
        for i in range(5):
            log_activity(
                workspace=cls.workspace,
                event_type=ActivityEvent.EventType.TASK_CREATED,
                actor=cls.owner,
                project=cls.project,
                summary=f"Seed activity {i}",
            )

    def setUp(self):
        self.client = APIClient()
        token = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _get(self, name, **kwargs):
        return self.client.get(reverse(name, kwargs=kwargs))

    def test_dashboard_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self._get("workspace-dashboard", slug="perf-char")
        self.assertEqual(response.status_code, 200)
        # Characterisation ceiling — tighten in Phase 3 after aggregate rewrite.
        self.assertLessEqual(len(ctx), 40, f"dashboard queries={len(ctx)}")

    def test_project_list_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self._get("project-list", slug="perf-char")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 20, f"project-list queries={len(ctx)}")

    def test_board_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self._get(
                "project-board", slug="perf-char", project_key="CHR"
            )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 25, f"board queries={len(ctx)}")

    def test_my_tasks_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self._get("my-tasks", slug="perf-char")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 25, f"my-tasks queries={len(ctx)}")

    def test_activity_query_budget(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self._get("workspace-activity", slug="perf-char")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 20, f"activity queries={len(ctx)}")

    def test_task_position_still_moves(self):
        task = Task.objects.filter(project=self.project).first()
        from apps.projects.workflow_models import Transition

        transition = Transition.objects.filter(
            project=self.project, from_status=task.workflow_status
        ).first()
        self.assertIsNotNone(transition)
        response = self.client.patch(
            reverse("task-position", kwargs={"task_id": task.id}),
            {
                "transition_id": str(transition.id),
                "position": 9999,
                "version": task.version,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        task.refresh_from_db()
        self.assertEqual(task.position, 9999)
