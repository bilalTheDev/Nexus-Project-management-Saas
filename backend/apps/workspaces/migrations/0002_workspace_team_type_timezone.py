from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspaces", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workspace",
            name="team_type",
            field=models.CharField(
                choices=[
                    ("software", "Software"),
                    ("business", "Business"),
                    ("marketing", "Marketing"),
                    ("other", "Other"),
                ],
                default="software",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="workspace",
            name="timezone",
            field=models.CharField(default="UTC", max_length=64),
        ),
    ]
