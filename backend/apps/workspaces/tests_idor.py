"""
Tenant-isolation / IDOR suite generated from the live URL conf.

For every API route that embeds a tenant UUID or workspace slug, a user who
only belongs to workspace B must get 404 when using workspace A's identifiers.
"""

from __future__ import annotations

import re
import uuid
from typing import Iterable

from django.contrib.auth import get_user_model
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.projects.governance_models import Notification, Release
from apps.projects.models import Project
from apps.projects.sprint_models import Sprint
from apps.projects.templates import apply_template
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()

SKIP_NAME_PREFIXES = (
    "auth-",
    "users-me",
    "health",
    "project-templates",
    "me-permissions",
)


def _iter_patterns(patterns=None, prefix="") -> Iterable[tuple[str, URLPattern]]:
    if patterns is None:
        patterns = get_resolver().url_patterns
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _iter_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            yield prefix + str(pattern.pattern), pattern


def _route_has_uuid(route: str) -> bool:
    return "<uuid:" in route


def _route_is_workspace_scoped(route: str) -> bool:
    return "workspaces/<slug:" in route


def _normalize_api_path(path: str) -> str | None:
    if "<" in path:
        return None
    if path.startswith("/admin"):
        return None
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/api/"):
        path = "/api/v1" + path
    path = path.replace("//", "/")
    while path.startswith("/api/v1/api/v1/"):
        path = path[len("/api/v1") :]
    return path


class TenantIdorMatrixTests(APITestCase):
    """Authenticate as workspace-B-only; attack with workspace-A identifiers."""

    @classmethod
    def setUpTestData(cls):
        cls.owner_a = User.objects.create_user(
            email="owner-a@example.com", password="TestPass123!", username="owner_a"
        )
        cls.owner_b = User.objects.create_user(
            email="owner-b@example.com", password="TestPass123!", username="owner_b"
        )
        cls.ws_a = Workspace.objects.create(
            name="Alpha", slug="alpha-idor", created_by=cls.owner_a
        )
        cls.ws_b = Workspace.objects.create(
            name="Beta", slug="beta-idor", created_by=cls.owner_b
        )
        WorkspaceMembership.objects.create(
            workspace=cls.ws_a,
            user=cls.owner_a,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        WorkspaceMembership.objects.create(
            workspace=cls.ws_b,
            user=cls.owner_b,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
        )
        cls.project_a = Project.objects.create(
            workspace=cls.ws_a,
            name="Web",
            key="WEBA",
            created_by=cls.owner_a,
        )
        apply_template(cls.project_a, "scrum")
        cls.task_a = Task.objects.create(
            project=cls.project_a,
            number=1,
            title="Secret issue",
            created_by=cls.owner_a,
            status=Task.Status.TODO,
        )
        cls.comment_a = Comment.objects.create(
            task=cls.task_a, author=cls.owner_a, body="secret note"
        )
        cls.membership_a = WorkspaceMembership.objects.get(
            workspace=cls.ws_a, user=cls.owner_a
        )
        cls.sprint_a = Sprint.objects.create(
            project=cls.project_a, name="Sprint 1", created_by=cls.owner_a
        )
        cls.release_a = Release.objects.create(project=cls.project_a, name="1.0")
        cls.notification_a = Notification.objects.create(
            workspace=cls.ws_a,
            recipient=cls.owner_a,
            kind=Notification.Kind.ASSIGNED,
            title="Ping",
        )

    def setUp(self):
        token = RefreshToken.for_user(self.owner_b)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _uuid_map(self) -> dict[str, str]:
        return {
            "task_id": str(self.task_a.id),
            "comment_id": str(self.comment_a.id),
            "membership_id": str(self.membership_a.id),
            "sprint_id": str(self.sprint_a.id),
            "release_id": str(self.release_a.id),
            "notification_id": str(self.notification_a.id),
        }

    def _fill_route(self, route: str, *, slug: str, project_key: str) -> str | None:
        path = route
        path = path.replace("<slug:slug>", slug)
        path = path.replace("<str:project_key>", project_key)
        for name, value in self._uuid_map().items():
            path = path.replace(f"<uuid:{name}>", value)
        return _normalize_api_path(path)

    def _methods_for(self, pattern: URLPattern) -> list[str]:
        callback = pattern.callback
        view_cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
        if view_cls is None:
            return ["get", "patch", "delete"]
        methods = [
            m
            for m in ("get", "patch", "put", "delete", "post")
            if hasattr(view_cls, m)
        ]
        return methods or ["get"]

    def _assert_cross_tenant_404(self, method: str, path: str, failures: list, name: str):
        kwargs = {}
        if method in ("post", "put", "patch"):
            kwargs = {
                "data": {"title": "x", "name": "x", "body": "x", "email": "x@y.com"},
                "format": "json",
            }
        response = getattr(self.client, method)(path, **kwargs)
        if response.status_code not in (
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ):
            failures.append(
                f"{method.upper()} {path} (name={name}) → {response.status_code}"
            )

    def test_urlconf_idor_matrix(self):
        """
        Walk urlpatterns and hit each tenant route with A's identifiers.

        Cases covered per matching route:
        1. A's slug (+ A's project key / UUIDs as needed)
        2. B's slug + A's project key / UUIDs when the route nests those params
        """
        failures: list[str] = []
        covered = 0

        for route, pattern in _iter_patterns():
            name = pattern.name or ""
            if any(name.startswith(p) or name == p for p in SKIP_NAME_PREFIXES):
                continue
            if not (_route_has_uuid(route) or _route_is_workspace_scoped(route)):
                continue

            methods = self._methods_for(pattern)
            attack_paths: list[str] = []

            # Always try with A's slug when the route is workspace-scoped.
            if _route_is_workspace_scoped(route):
                p = self._fill_route(
                    route, slug=self.ws_a.slug, project_key=self.project_a.key
                )
                if p:
                    attack_paths.append(p)

            # UUID-bearing routes: also try under B's slug with A's UUIDs /
            # project key (nested IDOR while authenticated to a real tenant).
            if _route_has_uuid(route):
                if _route_is_workspace_scoped(route):
                    p = self._fill_route(
                        route, slug=self.ws_b.slug, project_key=self.project_a.key
                    )
                    if p:
                        attack_paths.append(p)
                else:
                    # Global UUID routes (tasks/, comments/, issues/)
                    p = self._fill_route(
                        route, slug=self.ws_b.slug, project_key=self.project_a.key
                    )
                    if p:
                        attack_paths.append(p)

            # Workspace-scoped + project_key but no UUID: B slug + A's project key
            elif _route_is_workspace_scoped(route) and "<str:project_key>" in route:
                p = self._fill_route(
                    route, slug=self.ws_b.slug, project_key=self.project_a.key
                )
                if p:
                    attack_paths.append(p)

            for path in dict.fromkeys(attack_paths):
                for method in methods:
                    covered += 1
                    self._assert_cross_tenant_404(method, path, failures, name)

        self.assertGreater(
            covered, 20, "IDOR matrix produced too few cases — URL walk broken?"
        )
        self.assertEqual(failures, [], msg="IDOR leaks:\n" + "\n".join(failures))

    def test_cross_tenant_task_uuid_is_404(self):
        url = f"/api/v1/tasks/{self.task_a.id}/"
        for method in ("get", "patch", "delete"):
            kwargs = {}
            if method == "patch":
                kwargs = {"data": {"title": "hacked"}, "format": "json"}
            response = getattr(self.client, method)(url, **kwargs)
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                f"{method} task leaked: {response.status_code}",
            )

    def test_cross_tenant_comment_uuid_is_404(self):
        url = f"/api/v1/comments/{self.comment_a.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nested_uuid_under_own_slug_still_404(self):
        url = (
            f"/api/v1/workspaces/{self.ws_b.slug}/projects/{self.project_a.key}/"
            f"sprints/{self.sprint_a.id}/start/"
        )
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_uuid_same_as_forbidden(self):
        missing = uuid.uuid4()
        response = self.client.get(f"/api/v1/tasks/{missing}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_workspace_slug_is_404(self):
        response = self.client.get(f"/api/v1/workspaces/{self.ws_a.slug}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
