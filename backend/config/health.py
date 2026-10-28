"""Liveness / readiness probes — no secrets or internal error details."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse


def healthz(_request):
    """Process is alive (no dependency checks)."""
    return JsonResponse({"status": "ok"}, status=200)


def readyz(_request):
    """Database reachable and no pending migrations. Never leaks internals."""
    checks = {"database": "ok", "migrations": "ok"}
    ok = True

    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        checks["database"] = "unavailable"
        ok = False

    if ok:
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                checks["migrations"] = "pending"
                ok = False
        except Exception:
            checks["migrations"] = "unavailable"
            ok = False

    return JsonResponse(
        {"status": "ok" if ok else "not_ready", "checks": checks},
        status=200 if ok else 503,
    )


def health(_request):
    """Legacy readiness under /api/v1/health/ (same shape as before)."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "database": "reachable" if db_ok else "unreachable",
        },
        status=status_code,
    )
