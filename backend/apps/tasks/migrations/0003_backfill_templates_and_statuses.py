"""Backfill template workflow for existing projects and link tasks to statuses."""

from django.db import migrations


def forwards(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    IssueType = apps.get_model("projects", "IssueType")
    WorkflowStatus = apps.get_model("projects", "WorkflowStatus")
    Transition = apps.get_model("projects", "Transition")
    Task = apps.get_model("tasks", "Task")

    from apps.projects.templates import load_templates

    templates = {t["key"]: t for t in load_templates()}
    default = templates.get("scrum") or next(iter(templates.values()))

    for project in Project.objects.all():
        tmpl = templates.get(project.template_key) or default
        project.template_key = tmpl["key"]
        project.board_config = {
            "nav": tmpl["includes"].get("nav", []),
            "backlog": tmpl["includes"].get("backlog", False),
            "sprints": tmpl["includes"].get("sprints", False),
            "wip_hints": True,
        }
        project.save(update_fields=["template_key", "board_config"])

        status_by_key = {}
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

        type_by_key = {}
        for idx, spec in enumerate(tmpl["issue_types"]):
            itype, _ = IssueType.objects.update_or_create(
                project=project,
                key=spec["key"],
                defaults={
                    "name": spec["name"],
                    "hierarchy_level": spec["hierarchy_level"],
                    "position": idx,
                },
            )
            type_by_key[spec["key"]] = itype

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

        default_type = (
            type_by_key.get("task")
            or type_by_key.get("story")
            or type_by_key.get("bug")
            or next(iter(type_by_key.values()), None)
        )
        fallback_status = (
            status_by_key.get("todo")
            or status_by_key.get("backlog")
            or next(iter(status_by_key.values()), None)
        )

        for task in Task.objects.filter(project=project):
            ws = status_by_key.get(task.status) or fallback_status
            updates = []
            if ws and task.workflow_status_id != ws.id:
                task.workflow_status = ws
                updates.append("workflow_status")
            if default_type and task.issue_type_id is None:
                task.issue_type = default_type
                updates.append("issue_type")
            if task.rank == 0 and task.position:
                task.rank = task.position
                updates.append("rank")
            if task.version is None or task.version < 1:
                task.version = 1
                updates.append("version")
            if updates:
                task.save(update_fields=updates)


def backwards(apps, schema_editor):
    # Keep workflow rows; clearing FKs is enough for reverse schema.
    Task = apps.get_model("tasks", "Task")
    Task.objects.all().update(workflow_status=None, issue_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0002_issue_workflow_fields"),
        ("projects", "0002_project_template_workflow"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
