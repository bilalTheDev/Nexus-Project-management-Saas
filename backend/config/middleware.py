"""Request ID + structured access logging."""

from __future__ import annotations

import logging
import time
import uuid

from config.logging_utils import bind_request_id, clear_request_id

logger = logging.getLogger("nexus.request")


class RequestIdMiddleware:
    """Attach X-Request-ID and emit a redacted structured access log line."""

    HEADER = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get(self.HEADER, "").strip()
        request_id = incoming if incoming and len(incoming) <= 64 else uuid.uuid4().hex
        request.request_id = request_id
        bind_request_id(request_id)

        started = time.perf_counter()
        try:
            response = self.get_response(request)
        except Exception:
            clear_request_id()
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response["X-Request-ID"] = request_id

        user = getattr(request, "user", None)
        user_id = None
        if user is not None and getattr(user, "is_authenticated", False):
            user_id = str(getattr(user, "pk", None))

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            },
        )
        clear_request_id()
        return response
