import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="template_key",
            field=models.CharField(blank=True, default="scrum", max_length=32),
        ),
        migrations.AddField(
            model_name="project",
            name="board_config",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="project",
            name="default_assignee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="default_assignee_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="IssueType",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("key", models.SlugField(max_length=32)),
                ("name", models.CharField(max_length=80)),
                ("hierarchy_level", models.SmallIntegerField(default=0)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issue_types",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["position", "name"]},
        ),
        migrations.CreateModel(
            name="WorkflowStatus",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("key", models.SlugField(max_length=32)),
                ("name", models.CharField(max_length=80)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("todo", "To Do"),
                            ("in_progress", "In Progress"),
                            ("done", "Done"),
                        ],
                        default="todo",
                        max_length=32,
                    ),
                ),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("wip_limit", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflow_statuses",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "workflow statuses",
                "ordering": ["position", "name"],
            },
        ),
        migrations.CreateModel(
            name="Transition",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=80)),
                ("validators", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "from_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outgoing_transitions",
                        to="projects.workflowstatus",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transitions",
                        to="projects.project",
                    ),
                ),
                (
                    "to_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incoming_transitions",
                        to="projects.workflowstatus",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Sprint",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("goal", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("future", "Future"),
                            ("active", "Active"),
                            ("completed", "Completed"),
                        ],
                        default="future",
                        max_length=16,
                    ),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("start_snapshot", models.JSONField(blank=True, default=dict)),
                ("complete_snapshot", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_sprints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sprints",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="issuetype",
            constraint=models.UniqueConstraint(
                fields=("project", "key"),
                name="uniq_issue_type_key_per_project",
            ),
        ),
        migrations.AddConstraint(
            model_name="workflowstatus",
            constraint=models.UniqueConstraint(
                fields=("project", "key"),
                name="uniq_workflow_status_key_per_project",
            ),
        ),
        migrations.AddConstraint(
            model_name="transition",
            constraint=models.UniqueConstraint(
                fields=("project", "from_status", "to_status"),
                name="uniq_transition_per_status_pair",
            ),
        ),
        migrations.AddIndex(
            model_name="sprint",
            index=models.Index(
                fields=["project", "status"],
                name="projects_sp_project_status_idx",
            ),
        ),
    ]
