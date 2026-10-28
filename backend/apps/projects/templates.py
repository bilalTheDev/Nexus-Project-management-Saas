"""Load and apply project templates from fixtures/templates.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from apps.projects.workflow_models import IssueType, Transition, WorkflowStatus

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "templates.json"


@lru_cache(maxsize=1)
def load_templates() -> list[dict]:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def get_template(key: str) -> dict | None:
    key = (key or "").strip().lower()
    for tmpl in load_templates():
        if tmpl["key"] == key:
            return tmpl
    return None


def list_templates() -> list[dict]:
    return [
        {
            "key": t["key"],
            "name": t["name"],
            "description": t["description"],
            "includes": t["includes"],
        }
        for t in load_templates()
    ]


def apply_template(project, template_key: str = "scrum") -> dict:
    """Seed issue types, statuses, and transitions for a project. Idempotent per key."""
    tmpl = get_template(template_key) or get_template("scrum")
    assert tmpl is not None

    project.template_key = tmpl["key"]
    project.board_config = {
        "nav": tmpl["includes"].get("nav", []),
        "backlog": tmpl["includes"].get("backlog", False),
        "sprints": tmpl["includes"].get("sprints", False),
        "wip_hints": True,
    }
    project.save(update_fields=["template_key", "board_config", "updated_at"])

    status_by_key: dict[str, WorkflowStatus] = {}
    for idx, spec in enumerate(tmpl["statuses"]):
        status, _ = WorkflowStatus.objects.update_or_create(
            project=project,
            key=spec["key"],
            defaults={
                "name": spec["name"],
                "category": spec["category"],
                "position": spec.get("position", idx),
            },
        )
        status_by_key[spec["key"]] = status

    for idx, spec in enumerate(tmpl["issue_types"]):
        IssueType.objects.update_or_create(
            project=project,
            key=spec["key"],
            defaults={
                "name": spec["name"],
                "hierarchy_level": spec["hierarchy_level"],
                "position": idx,
            },
        )

    for spec in tmpl["transitions"]:
        frm = status_by_key.get(spec["from"])
        to = status_by_key.get(spec["to"])
        if not frm or not to:
            continue
        Transition.objects.update_or_create(
            project=project,
            from_status=frm,
            to_status=to,
            defaults={"name": spec["name"], "validators": []},
        )

    return tmpl
