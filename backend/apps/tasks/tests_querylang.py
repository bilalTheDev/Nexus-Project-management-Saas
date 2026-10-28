from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from apps.tasks.querylang import parse_query


class QueryLangTests(SimpleTestCase):
    def test_basic_and(self):
        q, order = parse_query(
            'project = NEX AND status != done ORDER BY priority DESC',
            current_user_email="a@b.com",
        )
        self.assertTrue(q)
        self.assertEqual(order, ["-priority"])

    def test_current_user(self):
        q, _ = parse_query(
            "assignee = currentUser()", current_user_email="me@nexus.dev"
        )
        self.assertIn("assignee__email", str(q))

    def test_rejects_unknown_field(self):
        with self.assertRaises(ValidationError):
            parse_query('hacked = "x"')

    def test_rejects_injection(self):
        with self.assertRaises(ValidationError):
            parse_query('status = "x" OR 1=1 --')
