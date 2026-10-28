from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.cookies import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    set_refresh_cookie,
)
from apps.accounts.csrf import enforce_cookie_csrf
from apps.accounts.serializers import (
    EmailTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.accounts.tokens import blacklist_all_refresh_tokens

User = get_user_model()

GENERIC_AUTH_FAILURE = "Invalid email or password. Please try again."
GENERIC_RESET_DISPATCH = (
    "If an account exists, a reset link has been dispatched."
)
GENERIC_REGISTER_CONFLICT = "Unable to create an account with those details."


def _axes_credentials(email: str) -> dict:
    return {"username": (email or "").lower().strip()}


def _axes_is_locked(request, email: str) -> bool:
    try:
        from axes.handlers.proxy import AxesProxyHandler

        return AxesProxyHandler.is_locked(request, _axes_credentials(email))
    except Exception:
        # Never block sign-in because lockout bookkeeping failed.
        return False


def _axes_login_failed(request, email: str) -> None:
    try:
        from axes.handlers.proxy import AxesProxyHandler

        AxesProxyHandler.user_login_failed(
            sender=User,
            request=request,
            credentials=_axes_credentials(email),
        )
    except Exception:
        return


def _axes_login_succeeded(request, user) -> None:
    try:
        from axes.handlers.proxy import AxesProxyHandler

        AxesProxyHandler.user_logged_in(
            sender=User,
            request=request,
            user=user,
        )
    except Exception:
        return


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            # Avoid confirming whether an email is already registered.
            email_errors = (exc.detail or {}).get("email") if isinstance(exc.detail, dict) else None
            if email_errors:
                return Response(
                    {"detail": GENERIC_REGISTER_CONFLICT},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        from apps.workspaces.permissions import default_workspace_slug

        response = Response(
            {
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
                "default_workspace": default_workspace_slug(user),
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, refresh)
        return response


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailTokenObtainPairSerializer
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").lower().strip()
        if email and _axes_is_locked(request, email):
            return Response(
                {"detail": GENERIC_AUTH_FAILURE},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (AuthenticationFailed, ValidationError):
            if email:
                _axes_login_failed(request, email)
            return Response(
                {"detail": GENERIC_AUTH_FAILURE},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        _axes_login_succeeded(request, serializer.user)
        refresh = data["refresh"]
        response = Response(
            {
                "access": data["access"],
                "user": data["user"],
                "default_workspace": data.get("default_workspace"),
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        enforce_cookie_csrf(request)
        raw = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if raw:
            try:
                token = RefreshToken(raw)
                token.blacklist()
            except (TokenError, AttributeError):
                pass
        response = Response({"detail": "Signed out."}, status=status.HTTP_200_OK)
        clear_refresh_cookie(response)
        return response


class CookieTokenRefreshView(APIView):
    """Rotate refresh tokens and rewrite the HttpOnly cookie."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        enforce_cookie_csrf(request)
        raw = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not raw:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(raw)
            access = str(refresh.access_token)

            if django_settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                if django_settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION", False):
                    try:
                        refresh.blacklist()
                    except AttributeError:
                        pass
                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()

            response = Response({"access": access}, status=status.HTTP_200_OK)
            set_refresh_cookie(response, refresh)
            return response
        except TokenError:
            response = Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        # Always return the same body. Debug tokens only when explicitly enabled.
        allow_debug = (
            django_settings.DEBUG
            and django_settings.ALLOW_PASSWORD_RESET_DEBUG
            and request.query_params.get("debug") == "1"
        )
        if user and allow_debug:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            return Response(
                {
                    "detail": GENERIC_RESET_DISPATCH,
                    "debug_uid": uid,
                    "debug_token": token,
                }
            )
        return Response({"detail": GENERIC_RESET_DISPATCH})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = serializer.validated_data["token"]
        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        # Single-use token is consumed by password change; also revoke sessions.
        blacklist_all_refresh_tokens(user)
        return Response({"detail": "Password updated successfully."})
