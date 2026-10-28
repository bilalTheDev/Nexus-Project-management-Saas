"""DRF exception handler — stable error envelope, no stack traces in responses."""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("nexus.api")


def _code_for_status(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "authentication_failed",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        429: "throttled",
        500: "server_error",
    }
    return mapping.get(status_code, f"http_{status_code}")


def _normalize_details(data) -> dict | list | None:
    if data is None:
        return None
    if isinstance(data, dict):
        # Prefer field errors; flatten DRF's {"detail": "..."} into message-only.
        if set(data.keys()) == {"detail"}:
            return None
        return data
    if isinstance(data, list):
        return data
    return {"non_field_errors": [str(data)]}


def _message_from_data(data, default: str) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if detail is not None:
            return str(detail)
        # First field error as human message
        for key, value in data.items():
            if key == "detail":
                continue
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            if value is not None:
                return f"{key}: {value}"
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, str):
        return data
    return default


def nexus_exception_handler(exc, context):
    """Return {"error": {"code", "message", "details"}} for API errors."""
    response = drf_exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        data = response.data
        code = _code_for_status(status_code)
        if isinstance(exc, APIException) and getattr(exc, "default_code", None):
            # Prefer explicit exception codes (e.g. version_conflict) when useful.
            default_code = exc.default_code
            if isinstance(default_code, str) and default_code not in (
                "error",
                "invalid",
            ):
                code = default_code
        if isinstance(data, dict) and isinstance(data.get("code"), str):
            code = data["code"]

        message = _message_from_data(data, default=getattr(exc, "default_detail", "Error"))
        if not isinstance(message, str):
            message = str(message)
        details = _normalize_details(data)
        # Drop nested code/detail used only for message construction
        if isinstance(details, dict):
            details = {
                k: v
                for k, v in details.items()
                if k not in ("detail", "code") or k == "version"
            }
            if not details:
                details = None

        response.data = {
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        }
        return response

    # Unhandled exception — log server-side; never return a traceback.
    request = context.get("request")
    request_id = getattr(getattr(request, "request_id", None), "__str__", lambda: None)()
    if request is not None:
        request_id = getattr(request, "request_id", None)
    logger.exception(
        "unhandled_api_exception",
        extra={"request_id": request_id, "path": getattr(request, "path", None)},
    )
    return Response(
        {
            "error": {
                "code": "server_error",
                "message": "An unexpected error occurred.",
                "details": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
