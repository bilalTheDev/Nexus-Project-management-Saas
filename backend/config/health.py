"""Lightweight readiness endpoint — no secrets or internal error details."""

from django.db import connection
from django.http import JsonResponse


def health(_request):
    db_ok = False
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
