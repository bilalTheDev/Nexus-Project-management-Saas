"""Structured JSON logging with PII / secret redaction."""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import UTC, datetime

_request_id = threading.local()

_SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|authorization|cookie|csrf|"
    r"api[_-]?key|refresh|access[_-]?token|jwt|credential)",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)
_BEARER_RE = re.compile(r"(Bearer\s+)[^\s]+", re.IGNORECASE)


def bind_request_id(request_id: str | None) -> None:
    _request_id.value = request_id


def clear_request_id() -> None:
    _request_id.value = None


def get_request_id() -> str | None:
    return getattr(_request_id, "value", None)


def redact_string(value: str) -> str:
    value = _BEARER_RE.sub(r"\1[REDACTED]", value)
    value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    return value


def redact_value(key: str | None, value):
    if key and _SENSITIVE_KEY_RE.search(str(key)):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: redact_value(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(key, item) for item in value]
    if isinstance(value, str):
        return redact_string(value)
    return value


class RedactingJsonFormatter(logging.Formatter):
    """Emit one JSON object per log record; scrub secrets/emails."""

    RESERVED = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_string(record.getMessage()),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
        }
        for key, value in record.__dict__.items():
            if key in self.RESERVED or key.startswith("_"):
                continue
            if key == "request_id":
                continue
            payload[key] = redact_value(key, value)

        if record.exc_info:
            # Include type/message only — full stack stays in server logs via exc_text
            # when DEBUG handlers need it; still redact emails in the text.
            payload["exc_info"] = redact_string(self.formatException(record.exc_info))

        return json.dumps(payload, default=str, ensure_ascii=False)


def sentry_before_send(event, hint):
    """Scrub PII and secrets from Sentry payloads."""
    if "request" in event:
        request = event["request"]
        headers = request.get("headers") or {}
        for header in list(headers):
            if _SENSITIVE_KEY_RE.search(header) or header.lower() in (
                "cookie",
                "authorization",
                "x-csrftoken",
            ):
                headers[header] = "[REDACTED]"
        if "cookies" in request:
            request["cookies"] = "[REDACTED]"
        if "data" in request:
            request["data"] = redact_value("data", request["data"])
        if "query_string" in request and isinstance(request["query_string"], str):
            request["query_string"] = redact_string(request["query_string"])

    if "user" in event:
        user = event["user"]
        if "email" in user:
            user["email"] = "[REDACTED_EMAIL]"
        if "ip_address" in user:
            user.pop("ip_address", None)

    if "extra" in event:
        event["extra"] = redact_value("extra", event["extra"])

    if "exception" in event:
        values = event["exception"].get("values") or []
        for item in values:
            if "value" in item and isinstance(item["value"], str):
                item["value"] = redact_string(item["value"])

    return event
