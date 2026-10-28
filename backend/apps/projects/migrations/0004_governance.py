import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_rename_projects_sp_project_status_idx_projects_sp_project_b718db_idx"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("workspaces", "0002_workspace_team_type_timezone"),
    ]

    operations = [
        migrations.CreateModel(
            name="Release",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("unreleased", "Unreleased"), ("released", "Released"), ("archived", "Archived")], default="unreleased", max_length=16)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("release_date", models.DateField(blank=True, null=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="releases", to="projects.project")),
            ],
            options={"ordering": ["-release_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="Component",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("default_assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="default_component_assignee", to=settings.AUTH_USER_MODEL)),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="led_components", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="components", to="projects.project")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ProjectMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("admin", "Project Admin"), ("member", "Member"), ("viewer", "Viewer")], default="member", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="projects.project")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("assigned", models.BooleanField(default=True)),
                ("mentioned", models.BooleanField(default=True)),
                ("status_on_watched", models.BooleanField(default=True)),
                ("comment_on_watched", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_prefs", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("assigned", "Assigned"), ("mentioned", "Mentioned"), ("status_changed", "Status changed"), ("comment", "Comment on watched")], max_length=32)),
                ("dedupe_key", models.CharField(blank=True, default="", max_length=191)),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField(blank=True, default="")),
                ("link", models.CharField(blank=True, default="", max_length=255)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="triggered_notifications", to=settings.AUTH_USER_MODEL)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="workspaces.workspace")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="release",
            constraint=models.UniqueConstraint(fields=("project", "name"), name="uniq_release_name_per_project"),
        ),
        migrations.AddConstraint(
            model_name="component",
            constraint=models.UniqueConstraint(fields=("project", "name"), name="uniq_component_name_per_project"),
        ),
        migrations.AddConstraint(
            model_name="projectmembership",
            constraint=models.UniqueConstraint(fields=("project", "user"), name="uniq_project_membership"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "-created_at"], name="projects_no_recipie_idx"),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                condition=~models.Q(("dedupe_key", "")),
                fields=("recipient", "dedupe_key"),
                name="uniq_notification_dedupe",
            ),
        ),
    ]
