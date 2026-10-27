from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()


class TenantIsolationTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", password="TestPass1", username="owner"
        )
        self.outsider = User.objects.create_user(
            email="out@example.com", password="TestPass1", username="out"
        )
        self.workspace = Workspace.objects.create(
            name="Alpha", slug="alpha", created_by=self.owner
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name="Web",
            key="WEB",
            created_by=self.owner,
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_outsider_cannot_list_projects(self):
        self._auth(self.outsider)
        url = reverse("project-list", kwargs={"slug": "alpha"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_and_move_task(self):
        self._auth(self.owner)
        create_url = reverse(
            "project-tasks", kwargs={"slug": "alpha", "project_key": "WEB"}
        )
        created = self.client.post(
            create_url, {"title": "Ship drawer", "status": "todo"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        task_id = created.data["id"]
        pos_url = reverse("task-position", kwargs={"task_id": task_id})
        moved = self.client.patch(
            pos_url,
            {"status": "in_progress", "position": 1500},
            format="json",
        )
        self.assertEqual(moved.status_code, status.HTTP_200_OK)
        self.assertEqual(moved.data["status"], "in_progress")
        task = Task.objects.get(pk=task_id)
        self.assertEqual(task.position, 1500)
