"""Parametrized coverage of every POLICY action × workspace/project role."""

from django.test import SimpleTestCase

from apps.projects.governance_models import ProjectMembership
from apps.projects.policy import POLICY, can
from apps.workspaces.models import WorkspaceMembership

WS_ROLES = [c.value for c in WorkspaceMembership.Role]
PR_ROLES = [c.value for c in ProjectMembership.Role] + [None]
ACTIONS = list(POLICY.keys())


class PolicyMatrixTests(SimpleTestCase):
    def test_every_action_defined(self):
        required = {
            "project.read",
            "project.write",
            "issue.read",
            "issue.write",
            "issue.transition",
            "sprint.manage",
            "release.manage",
            "workflow.manage",
            "project.admin",
            "workspace.admin",
            "workspace.owner",
            "member.manage",
        }
        self.assertTrue(required.issubset(POLICY.keys()))

    def test_role_action_matrix(self):
        cases = []
        for action in ACTIONS:
            for ws in WS_ROLES:
                for pr in PR_ROLES:
                    cases.append((action, ws, pr, can(action, workspace_role=ws, project_role=pr)))
        self.assertGreaterEqual(len(cases), len(ACTIONS) * len(WS_ROLES))

        # Spot-check invariants the rest of the suite relies on.
        self.assertTrue(
            can("project.read", workspace_role="viewer", project_role="viewer")
        )
        self.assertFalse(
            can("issue.write", workspace_role="viewer", project_role="viewer")
        )
        self.assertTrue(
            can("issue.write", workspace_role="member", project_role=None)
        )
        self.assertFalse(
            can("sprint.manage", workspace_role="member", project_role="member")
        )
        self.assertTrue(
            can("sprint.manage", workspace_role="project_manager", project_role=None)
        )
        # Project admin satisfies sprint.manage even without workspace PM.
        self.assertTrue(
            can("sprint.manage", workspace_role="member", project_role="admin")
        )
        self.assertFalse(
            can("sprint.manage", workspace_role="member", project_role=None)
        )
        self.assertTrue(
            can("workspace.owner", workspace_role="owner", project_role=None)
        )
        self.assertFalse(
            can("workspace.owner", workspace_role="admin", project_role=None)
        )
        self.assertTrue(
            can("member.manage", workspace_role="admin", project_role=None)
        )
        self.assertFalse(
            can("member.manage", workspace_role="member", project_role=None)
        )
        # Owners/admins bypass project-role gates (except workspace.owner).
        self.assertTrue(
            can("workflow.manage", workspace_role="owner", project_role="viewer")
        )
        self.assertTrue(
            can("release.manage", workspace_role="admin", project_role=None)
        )


def load_tests(loader, tests, pattern):
    """Expand into one test method per (action, ws_role, project_role)."""
    from unittest import TestCase, TestSuite

    suite = TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(PolicyMatrixTests))

    class _Generated(TestCase):
        pass

    for action in ACTIONS:
        for ws in WS_ROLES:
            for pr in PR_ROLES:
                expected = can(action, workspace_role=ws, project_role=pr)

                def _make(a=action, w=ws, p=pr, exp=expected):
                    def _test(self):
                        self.assertEqual(
                            can(a, workspace_role=w, project_role=p),
                            exp,
                            msg=f"can({a!r}, ws={w!r}, pr={p!r}) expected {exp}",
                        )

                    return _test

                name = f"test_{action.replace('.', '_')}_{ws}_{pr or 'none'}"
                setattr(_Generated, name, _make())

    suite.addTests(loader.loadTestsFromTestCase(_Generated))
    return suite
