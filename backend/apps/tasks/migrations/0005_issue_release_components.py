import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0004_rename_tasks_issue_issue_created_idx_tasks_issue_issue_i_5c68a0_idx_and_more"),
        ("projects", "0004_governance"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="fix_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="issues",
                to="projects.release",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="components",
            field=models.ManyToManyField(
                blank=True,
                related_name="issues",
                to="projects.component",
            ),
        ),
    ]
