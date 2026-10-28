from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.projects.models import Project
from apps.projects.templates import apply_template, list_templates
from apps.projects.workflow_models import Transition
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()


class TemplateAndWorkflowTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", password="TestPass1", username="owner"
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
        token = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_templates_fixture_lists_three(self):
        templates = list_templates()
        keys = {t["key"] for t in templates}
        self.assertEqual(keys, {"scrum", "kanban", "bug_tracking"})
        url = reverse("project-templates")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_create_scrum_project_applies_template(self):
        url = reverse("project-list", kwargs={"slug": "alpha"})
        response = self.client.post(
            url,
            {
                "name": "Delivery",
                "key": "DEL",
                "template_key": "scrum",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(key="DEL")
        self.assertEqual(project.template_key, "scrum")
        self.assertTrue(project.issue_types.filter(key="epic").exists())
        self.assertTrue(project.workflow_statuses.filter(key="todo").exists())
        self.assertTrue(project.transitions.exists())
        self.assertTrue(project.board_config.get("sprints"))

    def test_hierarchy_rules_and_epic_progress(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name="Web",
            key="WEB",
            created_by=self.owner,
        )
        apply_template(project, "scrum")
        epic_type = project.issue_types.get(key="epic")
        story_type = project.issue_types.get(key="story")
        todo = project.workflow_statuses.get(key="todo")
        done = project.workflow_statuses.get(key="done")

        create_url = reverse(
            "project-issues", kwargs={"slug": "alpha", "project_key": "WEB"}
        )
        epic = self.client.post(
            create_url,
            {
                "title": "Platform epic",
                "issue_type_id": str(epic_type.id),
                "workflow_status_id": str(todo.id),
            },
            format="json",
        )
        self.assertEqual(epic.status_code, status.HTTP_201_CREATED)
        epic_id = epic.data["id"]

        story_a = self.client.post(
            create_url,
            {
                "title": "Story A",
                "issue_type_id": str(story_type.id),
                "parent_id": epic_id,
                "workflow_status_id": str(todo.id),
            },
            format="json",
        )
        story_b = self.client.post(
            create_url,
            {
                "title": "Story B",
                "issue_type_id": str(story_type.id),
                "parent_id": epic_id,
                "workflow_status_id": str(todo.id),
            },
            format="json",
        )
        self.assertEqual(story_a.status_code, status.HTTP_201_CREATED)
        self.assertEqual(story_b.status_code, status.HTTP_201_CREATED)

        detail = self.client.get(reverse("issue-detail", kwargs={"task_id": epic_id}))
        self.assertEqual(detail.data["epic_progress"]["total"], 2)
        self.assertEqual(detail.data["epic_progress"]["done"], 0)

        # Complete story A via allowed transition path
        story = Task.objects.get(pk=story_a.data["id"])
        # Move todo -> in_progress -> in_review -> done
        for to_key in ("in_progress", "in_review", "done"):
            transition = Transition.objects.get(
                project=project,
                from_status=story.workflow_status,
                to_status__key=to_key,
            )
            moved = self.client.post(
                reverse("issue-transitions", kwargs={"task_id": story.id}),
                {"transition_id": str(transition.id), "version": story.version},
                format="json",
            )
            self.assertEqual(moved.status_code, status.HTTP_200_OK, moved.data)
            story.refresh_from_db()

        detail = self.client.get(reverse("issue-detail", kwargs={"task_id": epic_id}))
        self.assertEqual(detail.data["epic_progress"]["done"], 1)
        self.assertEqual(detail.data["epic_progress"]["total"], 2)

    def test_invalid_transition_returns_409(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name="Ops",
            key="OPS",
            created_by=self.owner,
        )
        apply_template(project, "scrum")
        todo = project.workflow_statuses.get(key="todo")
        done = project.workflow_statuses.get(key="done")
        issue = Task.objects.create(
            project=project,
            number=1,
            title="Blocked jump",
            created_by=self.owner,
            workflow_status=todo,
            status=todo.key,
            issue_type=project.issue_types.get(key="task"),
        )
        # Fabricate a transition id that doesn't match current from_status
        bogus = Transition.objects.filter(
            project=project, from_status=done, to_status=todo
        ).first()
        self.assertIsNotNone(bogus)
        response = self.client.post(
            reverse("issue-transitions", kwargs={"task_id": issue.id}),
            {"transition_id": str(bogus.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_sprint_lifecycle_moves_incomplete(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name="Ship",
            key="SHIP",
            created_by=self.owner,
        )
        apply_template(project, "scrum")
        todo = project.workflow_statuses.get(key="todo")
        sprint_url = reverse(
            "project-sprints", kwargs={"slug": "alpha", "project_key": "SHIP"}
        )
        created = self.client.post(sprint_url, {"name": "Sprint 1"}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        sprint_id = created.data["id"]

        issue = Task.objects.create(
            project=project,
            number=1,
            title="Carry over",
            created_by=self.owner,
            workflow_status=todo,
            status=todo.key,
            issue_type=project.issue_types.get(key="story"),
            sprint_id=sprint_id,
        )
        start = self.client.post(
            reverse(
                "project-sprint-start",
                kwargs={
                    "slug": "alpha",
                    "project_key": "SHIP",
                    "sprint_id": sprint_id,
                },
            ),
            {"goal": "Ship MVP"},
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        self.assertEqual(start.data["status"], "active")

        complete = self.client.post(
            reverse(
                "project-sprint-complete",
                kwargs={
                    "slug": "alpha",
                    "project_key": "SHIP",
                    "sprint_id": sprint_id,
                },
            ),
            {"move_incomplete_to": "backlog"},
            format="json",
        )
        self.assertEqual(complete.status_code, status.HTTP_200_OK)
        issue.refresh_from_db()
        self.assertIsNone(issue.sprint_id)

    def test_version_conflict_on_patch(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name="Sync",
            key="SYNC",
            created_by=self.owner,
        )
        apply_template(project, "kanban")
        issue = Task.objects.create(
            project=project,
            number=1,
            title="Conflict me",
            created_by=self.owner,
            workflow_status=project.workflow_statuses.get(key="todo"),
            status="todo",
            issue_type=project.issue_types.get(key="task"),
            version=1,
        )
        url = reverse("issue-detail", kwargs={"task_id": issue.id})
        first = self.client.patch(url, {"title": "First", "version": 1}, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        second = self.client.patch(
            url, {"title": "Second", "version": 1}, format="json"
        )
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

    def test_onboarding_ticks_create_project(self):
        url = reverse("project-list", kwargs={"slug": "alpha"})
        self.client.post(
            url,
            {"name": "First", "key": "FST", "template_key": "kanban"},
            format="json",
        )
        onboarding = self.client.get(
            reverse("workspace-onboarding", kwargs={"slug": "alpha"})
        )
        self.assertTrue(onboarding.data["checklist"]["create_project"])
