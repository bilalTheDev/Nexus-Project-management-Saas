"""Helpers to record activity without storing secrets."""

from apps.activity.models import ActivityEvent


_FORBIDDEN_META_KEYS = {
    "password",
    "token",
    "access",
    "refresh",
    "secret",
    "authorization",
    "cookie",
}


def _sanitize_metadata(metadata: dict | None) -> dict:
    if not metadata:
        return {}
    clean = {}
    for key, value in metadata.items():
        if str(key).lower() in _FORBIDDEN_META_KEYS:
            continue
        clean[key] = value
    return clean


def log_activity(
    *,
    workspace,
    event_type: str,
    actor=None,
    project=None,
    task=None,
    summary: str = "",
    metadata: dict | None = None,
) -> ActivityEvent:
    return ActivityEvent.objects.create(
        workspace=workspace,
        actor=actor,
        project=project,
        task=task,
        event_type=event_type,
        summary=summary[:255],
        metadata=_sanitize_metadata(metadata),
    )
