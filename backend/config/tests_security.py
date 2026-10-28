"""Smoke tests for Part D/E hardening (health, error envelope, pagination)."""

from django.test import Client, SimpleTestCase, TestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from config.exceptions import nexus_exception_handler
from config.pagination import NexusPagination
from config.serializers import StrictFieldsMixin


class HealthEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_healthz_alive(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readyz_ok_on_sqlite(self):
        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["checks"]["database"], "ok")
        self.assertEqual(body["checks"]["migrations"], "ok")

    def test_legacy_health(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("database", response.json())

    def test_request_id_header(self):
        response = self.client.get("/healthz", HTTP_X_REQUEST_ID="abc123")
        self.assertEqual(response["X-Request-ID"], "abc123")


class ExceptionEnvelopeTests(SimpleTestCase):
    def test_validation_error_envelope(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/x/")

        class _View(APIView):
            pass

        exc = ValidationError({"title": ["This field is required."]})
        response = nexus_exception_handler(exc, {"request": request, "view": _View()})
        self.assertEqual(response.status_code, 400)
        error = response.data["error"]
        self.assertEqual(error["code"], "bad_request")
        self.assertIn("title", error["message"])
        self.assertEqual(error["details"]["title"], ["This field is required."])


class StrictFieldsTests(SimpleTestCase):
    def test_rejects_unknown_fields(self):
        class S(StrictFieldsMixin, serializers.Serializer):
            name = serializers.CharField()

        ser = S(data={"name": "ok", "evil": 1})
        self.assertFalse(ser.is_valid())
        self.assertIn("evil", ser.errors)


class PaginationCapTests(SimpleTestCase):
    def test_max_page_size(self):
        self.assertEqual(NexusPagination.max_page_size, 100)
