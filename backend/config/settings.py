"""
Django settings for Nexus.

Environment-driven configuration for local development and production
(PythonAnywhere + Neon + Vercel). See backend/.env.example.
"""

from datetime import timedelta
from pathlib import Path
import sys

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load Neon-managed vars from repo root (.env.local), then backend/.env overrides.
load_dotenv(REPO_ROOT / ".env.local")
load_dotenv(BASE_DIR / ".env", override=True)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

if not DEBUG and (not SECRET_KEY or SECRET_KEY.startswith("django-insecure")):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a strong unique value when DJANGO_DEBUG=False."
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "corsheaders",
    "csp",
    "django_filters",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "axes",
    # Local apps
    "apps.accounts",
    "apps.workspaces",
    "apps.projects",
    "apps.tasks",
    "apps.comments",
    "apps.activity",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
    "config.middleware.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Neon Postgres: pooled DATABASE_URL for app traffic; direct UNPOOLED for migrations.
# See neon-postgres skill: migrations must use the non-pooler connection.
#
# Pooler-compatible connection settings:
# - Neon *transaction* pooler: prefer CONN_MAX_AGE=0 (pooler owns lifetime).
# - Neon *session* pooler / direct: short CONN_MAX_AGE (e.g. 60–600) + CONN_HEALTH_CHECKS.
# Override with DATABASE_CONN_MAX_AGE (seconds). Default 0 when pooled URL looks like
# a Neon pooler (-pooler.), else 600 for direct hosts.
_migration_cmds = {"migrate", "makemigrations", "showmigrations", "sqlmigrate"}
_is_migration = any(arg in _migration_cmds for arg in sys.argv)
_pooled = os.getenv("DATABASE_URL")
_unpooled = os.getenv("DATABASE_URL_UNPOOLED")
DATABASE_URL = (_unpooled if _is_migration and _unpooled else None) or _pooled or _unpooled
_ssl_require = os.getenv("DATABASE_SSL_REQUIRE", "True").lower() in ("1", "true", "yes")

_conn_max_age_env = os.getenv("DATABASE_CONN_MAX_AGE", "").strip()
if _is_migration:
    _conn_max_age = 0
elif _conn_max_age_env != "":
    _conn_max_age = int(_conn_max_age_env)
elif _pooled and "-pooler." in (_pooled or ""):
    _conn_max_age = 0
else:
    _conn_max_age = 600

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=_conn_max_age,
            conn_health_checks=_conn_max_age > 0,
            ssl_require=_ssl_require,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Reject oversized multipart / memory uploads (bytes).
DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    os.getenv("DATA_UPLOAD_MAX_MEMORY_SIZE", str(2 * 1024 * 1024))
)
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        # Both localhost and 127.0.0.1 — browsers treat them as different origins.
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
# Optional regex list for ephemeral hosts (e.g. Vercel preview URLs).
# Example: ^https://nexus-.*\.vercel\.app$
CORS_ALLOWED_ORIGIN_REGEXES = [
    pattern.strip()
    for pattern in os.getenv("CORS_ALLOWED_ORIGIN_REGEXES", "").split(",")
    if pattern.strip()
]
CORS_ALLOW_CREDENTIALS = True
# Never enable wildcard origins with credentials (browser + security invariant).
CORS_ALLOW_ALL_ORIGINS = False
if CORS_ALLOW_ALL_ORIGINS and CORS_ALLOW_CREDENTIALS:
    raise ImproperlyConfigured(
        "CORS_ALLOW_ALL_ORIGINS cannot be True when CORS_ALLOW_CREDENTIALS is True."
    )
if "*" in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS must not contain '*' when credentials are enabled."
    )

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

_drf_renderers = ["rest_framework.renderers.JSONRenderer"]
if DEBUG:
    _drf_renderers.append("rest_framework.renderers.BrowsableAPIRenderer")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "config.pagination.NexusPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": tuple(_drf_renderers),
    "EXCEPTION_HANDLER": "config.exceptions.nexus_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "300/minute",
        # login, register, password-reset, refresh, logout.
        # Keep production tight; allow denser local demo/sign-in retries.
        "auth": "5/minute" if not DEBUG else "60/minute",
    },
}

# Independent from DJANGO_SECRET_KEY so each can be rotated separately.
_jwt_signing_key = os.getenv("JWT_SIGNING_KEY") or SECRET_KEY

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": _jwt_signing_key,
}

JWT_REFRESH_COOKIE_NAME = "nexus_refresh"
# Empty → Lax when DEBUG, None when not (cross-site Vercel→API). See ADR 0001.
JWT_REFRESH_COOKIE_SAMESITE = os.getenv("JWT_REFRESH_COOKIE_SAMESITE", "").strip() or None

# Password-reset debug tokens (uid/token in JSON) — never enable in production.
ALLOW_PASSWORD_RESET_DEBUG = os.getenv(
    "ALLOW_PASSWORD_RESET_DEBUG", "False"
).lower() in ("1", "true", "yes")

# django-axes: lockout keyed by account + IP
AXES_FAILURE_LIMIT = int(os.getenv("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = timedelta(minutes=int(os.getenv("AXES_COOLOFF_MINUTES", "15")))
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_USERNAME_FORM_FIELD = "email"
AXES_RESET_ON_SUCCESS = True
AXES_VERBOSE = False
# DRF login uses AxesProxyHandler directly; disable double-counting via backend.
AXES_ENABLED = True

SPECTACULAR_SETTINGS = {
    "TITLE": "Nexus API",
    "DESCRIPTION": "Multi-tenant project management SaaS API",
    "VERSION": "1.0.0",
}

# ---------------------------------------------------------------------------
# Content-Security-Policy (API / Django responses via django-csp)
# Frontend CSP is enforced separately via frontend/vercel.json.
# ---------------------------------------------------------------------------
from csp.constants import NONE, SELF  # noqa: E402

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [NONE],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
    },
}

# ---------------------------------------------------------------------------
# Production HTTPS / browser hardening (gated on not DEBUG)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in (
        "1",
        "true",
        "yes",
    )
    # HSTS: enable only after confirming HTTPS works end-to-end.
    # Do NOT submit the host to the HSTS preload list until you are certain
    # every subdomain serves HTTPS permanently — preload is hard to undo.
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS", "True"
    ).lower() in ("1", "true", "yes")
    # Default False — only set SECURE_HSTS_PRELOAD=True after an explicit preload decision.
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

    # PythonAnywhere (and similar) terminate TLS at a reverse proxy and forward
    # HTTP to the app with X-Forwarded-Proto. Enable ONLY when the platform
    # strips/spoofs this header from clients — otherwise attackers can bypass
    # SECURE_SSL_REDIRECT. Documented for PA; set SECURE_PROXY_SSL_HEADER_ENABLED=True.
    if os.getenv("SECURE_PROXY_SSL_HEADER_ENABLED", "False").lower() in (
        "1",
        "true",
        "yes",
    ):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Logging — structured JSON with redaction (see config.logging_utils)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "config.logging_utils.RedactingJsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {"level": "WARNING", "propagate": True},
        "nexus": {"level": "INFO", "propagate": True},
    },
}

# ---------------------------------------------------------------------------
# Optional Sentry (SENTRY_DSN). Never send default PII.
# ---------------------------------------------------------------------------
_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    from config.logging_utils import sentry_before_send

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        send_default_pii=False,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        before_send=sentry_before_send,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production" if not DEBUG else "development"),
    )
