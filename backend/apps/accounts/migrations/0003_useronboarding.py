import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_managers"),
        ("workspaces", "0002_workspace_team_type_timezone"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserOnboarding",
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
                ("checklist_dismissed", models.BooleanField(default=False)),
                ("checklist", models.JSONField(blank=True, default=dict)),
                ("tour_completed", models.BooleanField(default=False)),
                ("tour_skipped", models.BooleanField(default=False)),
                ("tour_step", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="onboarding_states",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="onboarding_states",
                        to="workspaces.workspace",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="useronboarding",
            constraint=models.UniqueConstraint(
                fields=("user", "workspace"),
                name="uniq_onboarding_per_user_workspace",
            ),
        ),
    ]
