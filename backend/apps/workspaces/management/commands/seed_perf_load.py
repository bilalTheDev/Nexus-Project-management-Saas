"""Seed a dedicated perf workspace: >=20 projects and >=2000 tasks."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.projects.models import Project
from apps.projects.templates import apply_template
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()

SLUG = "perf-baseline"
PROJECT_COUNT = 20
TASKS_PER_PROJECT = 100  # 20 * 100 = 2000


class Command(BaseCommand):
    help = (
        "Create/refresh workspace 'perf-baseline' with 20 projects and 2000 tasks "
        "for CaptureQueriesContext / EXPLAIN baselines."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing perf-baseline workspace first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Workspace.objects.filter(slug=SLUG).delete()
            self.stdout.write("Deleted existing perf-baseline workspace.")

        user, _ = User.objects.get_or_create(
            email="perf.baseline@example.com",
            defaults={
                "username": "perf.baseline",
                "first_name": "Perf",
                "last_name": "Baseline",
            },
        )
        if not user.has_usable_password():
            user.set_password("PerfPass1!")  # nosec B105
            user.save(update_fields=["password"])

        workspace, created = Workspace.objects.get_or_create(
            slug=SLUG,
            defaults={"name": "Perf Baseline", "created_by": user},
        )
        WorkspaceMembership.objects.update_or_create(
            workspace=workspace,
            user=user,
            defaults={
                "role": WorkspaceMembership.Role.OWNER,
                "status": WorkspaceMembership.Status.ACTIVE,
                "joined_at": timezone.now(),
            },
        )

        existing_projects = workspace.projects.filter(archived_at__isnull=True).count()
        if existing_projects >= PROJECT_COUNT:
            task_count = Task.objects.filter(
                project__workspace=workspace, archived_at__isnull=True
            ).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Already seeded: {existing_projects} projects, {task_count} tasks "
                    f"(user={user.email} workspace={SLUG})"
                )
            )
            return

        start = existing_projects + 1
        for i in range(start, PROJECT_COUNT + 1):
            key = f"P{i:02d}"
            project = Project.objects.create(
                workspace=workspace,
                name=f"Perf Project {i}",
                key=key,
                created_by=user,
                lead=user,
            )
            apply_template(project, "kanban")
            todo = project.workflow_statuses.filter(key="todo").first()
            doing = project.workflow_statuses.filter(key="in_progress").first()
            done = project.workflow_statuses.filter(key="done").first()
            statuses = [s for s in (todo, doing, done) if s]
            issue_type = project.issue_types.filter(hierarchy_level=0).first()
            batch = []
            for n in range(1, TASKS_PER_PROJECT + 1):
                st = statuses[(n - 1) % len(statuses)] if statuses else None
                batch.append(
                    Task(
                        project=project,
                        number=n,
                        title=f"{key}-{n} baseline task",
                        status=st.key if st else Task.Status.TODO,
                        workflow_status=st,
                        issue_type=issue_type,
                        assignee=user if n % 3 == 0 else None,
                        created_by=user,
                        position=n * 1000,
                        priority=Task.Priority.MEDIUM,
                    )
                )
            Task.objects.bulk_create(batch, batch_size=200)
            log_activity(
                workspace=workspace,
                event_type=ActivityEvent.EventType.PROJECT_CREATED,
                actor=user,
                project=project,
                summary=f"Perf seeded {key}",
            )
            self.stdout.write(f"  seeded {key} ({TASKS_PER_PROJECT} tasks)")

        task_count = Task.objects.filter(
            project__workspace=workspace, archived_at__isnull=True
        ).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. workspace={SLUG} projects={PROJECT_COUNT} tasks={task_count} "
                f"login={user.email} / PerfPass1!"
            )
        )
        if created:
            self.stdout.write("Created new workspace.")
