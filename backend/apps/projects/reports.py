"""Server-side aggregates for project reports (Phase 2)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count, Q
from django.db.models.functions import TruncDay, TruncWeek
from django.utils import timezone

from apps.projects.sprint_models import Sprint
from apps.tasks.models import Task


def _tz(workspace) -> ZoneInfo:
    name = getattr(workspace, "timezone", None) or "UTC"
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def _as_local_date(dt: datetime | None, tz: ZoneInfo) -> date | None:
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt.astimezone(tz).date()


def burndown(project, sprint: Sprint) -> dict:
    """Remaining story points per day vs ideal line from sprint start snapshot."""
    tz = _tz(project.workspace)
    start = sprint.start_date or _as_local_date(sprint.started_at, tz) or date.today()
    end = sprint.end_date or _as_local_date(sprint.completed_at, tz) or (start + timedelta(days=14))
    if end < start:
        end = start

    start_ids = set((sprint.start_snapshot or {}).get("issue_ids") or [])
    start_points = float((sprint.start_snapshot or {}).get("points") or 0)
    if not start_ids:
        issues = Task.objects.filter(sprint=sprint, archived_at__isnull=True)
        start_ids = {str(i) for i in issues.values_list("id", flat=True)}
        start_points = sum(i.story_points or 0 for i in issues)

    # Completions: issues that reached done during the sprint window
    done_events = (
        Task.objects.filter(id__in=start_ids, completed_at__isnull=False)
        .values("id", "story_points", "completed_at")
    )
    completions_by_day: dict[date, float] = defaultdict(float)
    for row in done_events:
        d = _as_local_date(row["completed_at"], tz)
        if d and start <= d <= end:
            completions_by_day[d] += float(row["story_points"] or 0)

    days = []
    cursor = start
    remaining = start_points
    total_days = max((end - start).days, 1)
    while cursor <= end:
        remaining -= completions_by_day.get(cursor, 0)
        elapsed = (cursor - start).days
        ideal = start_points * (1 - (elapsed / total_days))
        days.append(
            {
                "date": cursor.isoformat(),
                "remaining": round(max(remaining, 0), 2),
                "ideal": round(max(ideal, 0), 2),
            }
        )
        cursor += timedelta(days=1)

    return {
        "sprint_id": str(sprint.id),
        "sprint_name": sprint.name,
        "start_points": start_points,
        "series": days,
    }


def velocity(project, limit: int = 6) -> dict:
    sprints = list(
        Sprint.objects.filter(project=project, status=Sprint.Status.COMPLETED).order_by(
            "-completed_at"
        )[:limit]
    )
    sprints.reverse()
    bars = []
    for sprint in sprints:
        start = sprint.start_snapshot or {}
        complete = sprint.complete_snapshot or {}
        committed = float(start.get("points") or 0)
        completed_ids = set(complete.get("completed_ids") or [])
        if completed_ids:
            completed = float(
                sum(
                    Task.objects.filter(id__in=completed_ids).values_list(
                        "story_points", flat=True
                    )
                )
                or 0
            )
            # values_list may return None points
            completed = float(
                sum(
                    (p or 0)
                    for p in Task.objects.filter(id__in=completed_ids).values_list(
                        "story_points", flat=True
                    )
                )
            )
        else:
            completed = float(
                sum(
                    (t.story_points or 0)
                    for t in Task.objects.filter(
                        sprint=sprint,
                        archived_at__isnull=True,
                    ).filter(Q(workflow_status__category="done") | Q(status="done"))
                )
            )
        bars.append(
            {
                "sprint_id": str(sprint.id),
                "sprint_name": sprint.name,
                "committed": round(committed, 2),
                "completed": round(completed, 2),
            }
        )
    return {"bars": bars}


def sprint_report(project, sprint: Sprint) -> dict:
    start_ids = set((sprint.start_snapshot or {}).get("issue_ids") or [])
    complete = sprint.complete_snapshot or {}
    completed_ids = set(complete.get("completed_ids") or [])
    incomplete_ids = set(complete.get("incomplete_ids") or [])
    all_end = set(complete.get("issue_ids") or [])
    if not all_end:
        all_end = {
            str(i)
            for i in Task.objects.filter(sprint=sprint).values_list("id", flat=True)
        }

    added = all_end - start_ids
    removed = start_ids - all_end

    def _rows(ids):
        qs = Task.objects.filter(id__in=ids).select_related("workflow_status", "issue_type")
        return [
            {
                "id": str(t.id),
                "key": t.issue_key,
                "title": t.title,
                "status": t.workflow_status.name if t.workflow_status else t.status,
                "points": t.story_points or 0,
            }
            for t in qs
        ]

    return {
        "sprint_id": str(sprint.id),
        "sprint_name": sprint.name,
        "completed": _rows(completed_ids or set()),
        "not_completed": _rows(incomplete_ids or set()),
        "added_mid_sprint": _rows(added),
        "removed": _rows(removed),
        "stacked": [
            {"label": "Completed", "count": len(completed_ids)},
            {"label": "Not completed", "count": len(incomplete_ids)},
            {"label": "Added", "count": len(added)},
            {"label": "Removed", "count": len(removed)},
        ],
    }


def cfd(project, date_from: date | None = None, date_to: date | None = None) -> dict:
    """Approximate CFD from current status + created/completed dates."""
    tz = _tz(project.workspace)
    today = timezone.now().astimezone(tz).date()
    date_to = date_to or today
    date_from = date_from or (date_to - timedelta(days=30))
    statuses = list(project.workflow_statuses.order_by("position"))
    if not statuses:
        return {"from": date_from.isoformat(), "to": date_to.isoformat(), "series": []}

    issues = list(
        Task.objects.filter(project=project, archived_at__isnull=True).select_related(
            "workflow_status"
        )
    )
    series = []
    cursor = date_from
    while cursor <= date_to:
        counts = {s.key: 0 for s in statuses}
        for issue in issues:
            created = _as_local_date(issue.created_at, tz) or date_from
            if created > cursor:
                continue
            completed = _as_local_date(issue.completed_at, tz)
            if completed and completed <= cursor:
                done_key = next((s.key for s in statuses if s.category == "done"), None)
                if done_key:
                    counts[done_key] += 1
                continue
            key = issue.workflow_status.key if issue.workflow_status else issue.status
            if key in counts:
                counts[key] += 1
            else:
                # fallback first todo column
                todo = next((s.key for s in statuses if s.category == "todo"), statuses[0].key)
                counts[todo] += 1
        series.append({"date": cursor.isoformat(), **counts})
        cursor += timedelta(days=1)

    return {
        "from": date_from.isoformat(),
        "to": date_to.isoformat(),
        "statuses": [{"key": s.key, "name": s.name, "category": s.category} for s in statuses],
        "series": series,
    }


def created_vs_resolved(project) -> dict:
    tz = _tz(project.workspace)
    created = (
        Task.objects.filter(project=project, archived_at__isnull=True)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )
    resolved = (
        Task.objects.filter(project=project, completed_at__isnull=False)
        .annotate(week=TruncWeek("completed_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )
    by_week: dict[str, dict] = defaultdict(lambda: {"created": 0, "resolved": 0})
    for row in created:
        if row["week"]:
            key = row["week"].astimezone(tz).date().isoformat()
            by_week[key]["created"] = row["count"]
    for row in resolved:
        if row["week"]:
            key = row["week"].astimezone(tz).date().isoformat()
            by_week[key]["resolved"] = row["count"]
    series = [
        {"week": week, **vals} for week, vals in sorted(by_week.items(), key=lambda x: x[0])
    ]
    return {"series": series}


def breakdown(project, by: str = "priority") -> dict:
    qs = Task.objects.filter(project=project, archived_at__isnull=True)
    if by == "assignee":
        rows = (
            qs.values("assignee_id", "assignee__email", "assignee__first_name", "assignee__last_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        slices = [
            {
                "key": str(r["assignee_id"] or "unassigned"),
                "label": (
                    f"{(r['assignee__first_name'] or '')} {(r['assignee__last_name'] or '')}".strip()
                    or r["assignee__email"]
                    or "Unassigned"
                ),
                "count": r["count"],
            }
            for r in rows
        ]
    elif by == "type":
        rows = (
            qs.values("issue_type__key", "issue_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        slices = [
            {
                "key": r["issue_type__key"] or "unknown",
                "label": r["issue_type__name"] or "Unknown",
                "count": r["count"],
            }
            for r in rows
        ]
    else:
        rows = qs.values("priority").annotate(count=Count("id")).order_by("-count")
        slices = [
            {"key": r["priority"], "label": r["priority"].replace("_", " ").title(), "count": r["count"]}
            for r in rows
        ]
    return {"by": by, "slices": slices}


def project_summary(project) -> dict:
    qs = Task.objects.filter(project=project, archived_at__isnull=True)
    open_count = qs.exclude(Q(workflow_status__category="done") | Q(status="done")).count()
    done_count = qs.filter(Q(workflow_status__category="done") | Q(status="done")).count()
    now = timezone.now()
    overdue = qs.exclude(Q(workflow_status__category="done") | Q(status="done")).filter(
        due_date__lt=now
    ).count()
    week_end = now + timedelta(days=7)
    due_week = qs.exclude(Q(workflow_status__category="done") | Q(status="done")).filter(
        due_date__gte=now, due_date__lte=week_end
    ).count()
    return {
        "open": open_count,
        "done": done_count,
        "overdue": overdue,
        "due_this_week": due_week,
    }
