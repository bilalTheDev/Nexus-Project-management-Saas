import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0001_initial"),
        ("projects", "0002_project_template_workflow"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="workflow_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="issues",
                to="projects.workflowstatus",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="issue_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="issues",
                to="projects.issuetype",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="tasks.task",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="sprint",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="issues",
                to="projects.sprint",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="rank",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="task",
            name="story_points",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="resolution",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="task",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["project", "rank"],
                name="tasks_task_project_rank_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["sprint", "rank"],
                name="tasks_task_sprint_rank_idx",
            ),
        ),
        migrations.CreateModel(
            name="IssueChange",
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
                ("field", models.CharField(max_length=64)),
                ("old_value", models.TextField(blank=True, default="")),
                ("new_value", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="issue_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "issue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="changes",
                        to="tasks.task",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="IssueLink",
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
                (
                    "link_type",
                    models.CharField(
                        choices=[
                            ("blocks", "Blocks"),
                            ("is_blocked_by", "Is blocked by"),
                            ("relates_to", "Relates to"),
                            ("duplicates", "Duplicates"),
                            ("is_duplicated_by", "Is duplicated by"),
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_issue_links",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outward_links",
                        to="tasks.task",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inward_links",
                        to="tasks.task",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="issuechange",
            index=models.Index(
                fields=["issue", "-created_at"],
                name="tasks_issue_issue_created_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="issuelink",
            constraint=models.UniqueConstraint(
                fields=("source", "target", "link_type"),
                name="uniq_issue_link_direction",
            ),
        ),
    ]
