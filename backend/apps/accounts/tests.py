from copy import deepcopy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

CSRF_HEADERS = {
    "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
    "HTTP_ORIGIN": "http://localhost:5173",
}

# Do not weaken production rates — only silence shared cache during unit tests.
_RF = deepcopy(settings.REST_FRAMEWORK)
_RF["DEFAULT_THROTTLE_CLASSES"] = ()
_RF["DEFAULT_THROTTLE_RATES"] = {}


@override_settings(REST_FRAMEWORK=_RF, AXES_ENABLED=False)
class AuthCookieFlowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="auth@example.com",
            password="SecurePass12",
            username="authuser",
        )

    def test_login_sets_httponly_refresh_cookie_without_body_refresh(self):
        url = reverse("auth-token")
        response = self.client.post(
            url,
            {"email": "auth@example.com", "password": "SecurePass12"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertIn("nexus_refresh", response.cookies)
        cookie = response.cookies["nexus_refresh"]
        self.assertTrue(cookie["httponly"])

    def test_login_failure_is_generic(self):
        url = reverse("auth-token")
        response = self.client.post(
            url,
            {"email": "auth@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Invalid email or password. Please try again.",
        )

    def test_refresh_requires_csrf_header(self):
        login = self.client.post(
            reverse("auth-token"),
            {"email": "auth@example.com", "password": "SecurePass12"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        denied = self.client.post(reverse("auth-refresh"), format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        ok = self.client.post(
            reverse("auth-refresh"), format="json", **CSRF_HEADERS
        )
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertIn("access", ok.data)
        self.assertNotIn("refresh", ok.data)

    def test_refresh_rejects_untrusted_origin(self):
        self.client.post(
            reverse("auth-token"),
            {"email": "auth@example.com", "password": "SecurePass12"},
            format="json",
        )
        response = self.client.post(
            reverse("auth-refresh"),
            format="json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_blacklists_and_clears_cookie(self):
        login = self.client.post(
            reverse("auth-token"),
            {"email": "auth@example.com", "password": "SecurePass12"},
            format="json",
        )
        raw = login.cookies["nexus_refresh"].value
        logout = self.client.post(
            reverse("auth-logout"), format="json", **CSRF_HEADERS
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(logout.cookies["nexus_refresh"].value, "")

        # Old refresh must no longer mint access.
        self.client.cookies["nexus_refresh"] = raw
        refresh = self.client.post(
            reverse("auth-refresh"), format="json", **CSRF_HEADERS
        )
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_requires_password_length_10(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "new@example.com",
                "password": "Short1Aaa",
                "full_name": "New User",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_is_generic(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "auth@example.com",
                "password": "SecurePass99",
                "full_name": "Dup User",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Unable to create an account with those details.",
        )


@override_settings(REST_FRAMEWORK=_RF, AXES_ENABLED=False)
class PasswordResetSecurityTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="SecurePass12",
            username="resetuser",
        )

    def test_reset_request_is_generic_for_unknown_email(self):
        response = self.client.post(
            reverse("auth-password-reset"),
            {"email": "nobody@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If an account exists, a reset link has been dispatched.",
        )
        self.assertNotIn("debug_token", response.data)

    @override_settings(DEBUG=True, ALLOW_PASSWORD_RESET_DEBUG=False)
    def test_debug_tokens_disabled_even_when_debug(self):
        response = self.client.post(
            reverse("auth-password-reset") + "?debug=1",
            {"email": "reset@example.com"},
            format="json",
        )
        self.assertNotIn("debug_token", response.data)

    def test_password_change_revokes_refresh_tokens(self):
        refresh = RefreshToken.for_user(self.user)
        jti_before = refresh["jti"]

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm = self.client.post(
            reverse("auth-password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "password": "BrandNewPass99",
            },
            format="json",
        )
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=jti_before).exists()
        )

        # Reset token is single-use.
        reuse = self.client.post(
            reverse("auth-password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "password": "AnotherPass99",
            },
            format="json",
        )
        self.assertEqual(reuse.status_code, status.HTTP_400_BAD_REQUEST)
