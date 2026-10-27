"""Seed the Northstar Studio demo workspace used across portfolio screenshots."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.activity.models import ActivityEvent
from apps.activity.services import log_activity
from apps.comments.models import Comment
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()

DEMO_PASSWORD = "DemoPass1"

USERS = [
    {
        "email": "maya@northstar.studio",
        "username": "maya.lin",
        "first_name": "Maya",
        "last_name": "Lin",
        "role": WorkspaceMembership.Role.OWNER,
    },
    {
        "email": "alex@northstar.studio",
        "username": "alex.rivera",
        "first_name": "Alex",
        "last_name": "Rivera",
        "role": WorkspaceMembership.Role.ADMIN,
    },
    {
        "email": "daniel@northstar.studio",
        "username": "daniel.vance",
        "first_name": "Daniel",
        "last_name": "Vance",
        "role": WorkspaceMembership.Role.PROJECT_MANAGER,
    },
    {
        "email": "sara@northstar.studio",
        "username": "sara.chen",
        "first_name": "Sara",
        "last_name": "Chen",
        "role": WorkspaceMembership.Role.MEMBER,
    },
    {
        "email": "marcus@freelance.design",
        "username": "marcus.brody",
        "first_name": "Marcus",
        "last_name": "Brody",
        "role": WorkspaceMembership.Role.VIEWER,
        "status": WorkspaceMembership.Status.PENDING,
    },
]


class Command(BaseCommand):
    help = "Seed Northstar Studio workspace, projects, tasks, and activity."

    def handle(self, *args, **options):
        now = timezone.now()
        # Migrate older demo emails if present
        for old_email, new_email in (
            ("maya@northstar.dev", "maya@northstar.studio"),
            ("daniel@northstar.dev", "daniel@northstar.studio"),
        ):
            old = User.objects.filter(email__iexact=old_email).first()
            new_exists = User.objects.filter(email__iexact=new_email).exists()
            if old and not new_exists:
                old.email = new_email
                old.save(update_fields=["email"])

        users = {}
        for spec in USERS:
            user = User.objects.filter(email__iexact=spec["email"]).first()
            if user is None:
                user = User.objects.filter(username=spec["username"]).first()
            if user is None:
                user = User(
                    email=spec["email"],
                    username=spec["username"],
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    is_active=True,
                )
            user.email = spec["email"]
            user.username = spec["username"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_active = True
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[spec["email"]] = user

        maya = users["maya@northstar.studio"]
        alex = users["alex@northstar.studio"]
        daniel = users["daniel@northstar.studio"]
        sara = users["sara@northstar.studio"]
        marcus = users["marcus@freelance.design"]

        workspace, _ = Workspace.objects.get_or_create(
            slug="northstar-studio",
            defaults={"name": "Northstar Studio", "created_by": maya},
        )
        workspace.name = "Northstar Studio"
        workspace.created_by = maya
        workspace.save()

        for spec in USERS:
            membership, _ = WorkspaceMembership.objects.get_or_create(
                workspace=workspace,
                user=users[spec["email"]],
                defaults={
                    "role": spec["role"],
                    "status": spec.get("status", WorkspaceMembership.Status.ACTIVE),
                    "joined_at": now - timedelta(days=120),
                },
            )
            membership.role = spec["role"]
            membership.status = spec.get("status", WorkspaceMembership.Status.ACTIVE)
            if membership.status == WorkspaceMembership.Status.ACTIVE and not membership.joined_at:
                membership.joined_at = now - timedelta(days=90)
            membership.save()

        project_specs = [
            {
                "key": "NEX-WEB",
                "name": "Website Redesign",
                "description": "Production overhaul of the agency marketing site and client landing templates.",
                "status": Project.Status.ON_TRACK,
                "lead": maya,
                "start_date": now.date() - timedelta(days=16),
                "due_date": now.date() + timedelta(days=18),
                "is_pinned": True,
            },
            {
                "key": "NEX-CP",
                "name": "Client Portal",
                "description": "Authenticated extranet for client deliverable approvals and feedback loops.",
                "status": Project.Status.IN_REVIEW,
                "lead": alex,
                "start_date": now.date() - timedelta(days=10),
                "due_date": now.date() + timedelta(days=33),
                "is_pinned": True,
            },
            {
                "key": "NEX-PL",
                "name": "Product Launch",
                "description": "Public beta release preparation, marketing collateral, and launch checklist.",
                "status": Project.Status.FAST_TRACK,
                "lead": maya,
                "start_date": now.date() - timedelta(days=33),
                "due_date": now.date() + timedelta(days=11),
                "is_pinned": True,
            },
            {
                "key": "NEX-OPS",
                "name": "Internal Operations",
                "description": "CI/CD automation, PostgreSQL database migrations, and tenant isolation hardening.",
                "status": Project.Status.MAINTENANCE,
                "lead": daniel,
                "start_date": now.date() - timedelta(days=40),
                "due_date": now.date() + timedelta(days=34),
                "is_pinned": True,
            },
            {
                "key": "NEX-LEGACY-V1",
                "name": "Brand Assets",
                "description": "Archived brand system deliverables.",
                "status": Project.Status.COMPLETED,
                "lead": alex,
                "archived": True,
                "is_pinned": False,
            },
            {
                "key": "NEX-AUDIT",
                "name": "Security Compliance",
                "description": "Archived SOC2 preparation sprint.",
                "status": Project.Status.COMPLETED,
                "lead": sara,
                "archived": True,
                "is_pinned": False,
            },
        ]

        projects = {}
        for spec in project_specs:
            project, _ = Project.objects.update_or_create(
                workspace=workspace,
                key=spec["key"],
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "status": spec["status"],
                    "lead": spec["lead"],
                    "created_by": maya,
                    "start_date": spec.get("start_date"),
                    "due_date": spec.get("due_date"),
                    "is_pinned": spec.get("is_pinned", False),
                    "archived_at": now - timedelta(days=30) if spec.get("archived") else None,
                },
            )
            projects[spec["key"]] = project

        web = projects["NEX-WEB"]
        cp = projects["NEX-CP"]
        pl = projects["NEX-PL"]
        ops = projects["NEX-OPS"]

        task_specs = [
            # Website Redesign board
            ("NEX-WEB", 101, "Audit semantic headings across landing pages", Task.Status.BACKLOG, Task.Priority.LOW, sara, None),
            ("NEX-WEB", 131, "Prepare release notes & changelog v1.0", Task.Status.BACKLOG, Task.Priority.MEDIUM, alex, None),
            ("NEX-WEB", 136, "Audit external font licensing & CDN fallbacks", Task.Status.BACKLOG, Task.Priority.LOW, daniel, None),
            ("NEX-WEB", 140, "Define localized date formats for EU clients", Task.Status.BACKLOG, Task.Priority.MEDIUM, sara, None),
            ("NEX-WEB", 124, "Implement JWT refresh rotation & cookie fallback", Task.Status.TODO, Task.Priority.HIGH, daniel, now + timedelta(days=5)),
            ("NEX-WEB", 128, "Configure CORS whitelist for Vercel preview URLs", Task.Status.TODO, Task.Priority.MEDIUM, daniel, now + timedelta(days=6)),
            ("NEX-WEB", 132, "Refactor workspace membership queries with prefetch", Task.Status.TODO, Task.Priority.HIGH, sara, now + timedelta(days=7)),
            ("NEX-WEB", 135, "Draft client onboarding email notification templates", Task.Status.TODO, Task.Priority.LOW, alex, now + timedelta(days=9)),
            ("NEX-WEB", 104, "Finalize navigation hierarchy & mobile drawer", Task.Status.IN_PROGRESS, Task.Priority.URGENT, maya, now.replace(hour=17, minute=0, second=0, microsecond=0)),
            ("NEX-WEB", 112, "Build drag-and-drop state reconciliation with optimistic updates", Task.Status.IN_PROGRESS, Task.Priority.HIGH, maya, now + timedelta(days=1)),
            ("NEX-WEB", 115, "Design responsive table row collapse for small viewports", Task.Status.IN_PROGRESS, Task.Priority.MEDIUM, alex, now + timedelta(days=3)),
            ("NEX-WEB", 118, "Review responsive dashboard layout & contrast", Task.Status.IN_REVIEW, Task.Priority.HIGH, maya, now + timedelta(days=1)),
            ("NEX-WEB", 120, "Test PostgreSQL querysets under tenant filters", Task.Status.IN_REVIEW, Task.Priority.MEDIUM, daniel, now + timedelta(days=2)),
            ("NEX-WEB", 90, "Ship marketing hero editorial type ramp", Task.Status.DONE, Task.Priority.MEDIUM, alex, now - timedelta(days=4)),
            ("NEX-WEB", 91, "Tokenize brand teal and surface paper colors", Task.Status.DONE, Task.Priority.MEDIUM, maya, now - timedelta(days=5)),
            # Client Portal
            ("NEX-CP", 118, "Review responsive dashboard layout", Task.Status.IN_REVIEW, Task.Priority.HIGH, maya, now + timedelta(days=1)),
            ("NEX-CP", 80, "Client approval inbox empty state", Task.Status.DONE, Task.Priority.MEDIUM, alex, now - timedelta(days=2)),
            ("NEX-CP", 81, "Deliverable thumbnail grid", Task.Status.TODO, Task.Priority.MEDIUM, alex, now + timedelta(days=4)),
            # Product Launch
            ("NEX-PL", 112, "Audit cookie policies across staging subdomains", Task.Status.IN_PROGRESS, Task.Priority.HIGH, daniel, now + timedelta(days=2)),
            ("NEX-PL", 131, "Prepare launch day rollback checklist", Task.Status.BACKLOG, Task.Priority.URGENT, alex, now + timedelta(days=7)),
            # Ops
            ("NEX-OPS", 135, "Security audit preparation & SOC2 checklist review", Task.Status.TODO, Task.Priority.HIGH, sara, now + timedelta(days=4)),
            ("NEX-OPS", 70, "Partition key resolvers for multi-tenant middleware", Task.Status.DONE, Task.Priority.HIGH, daniel, now - timedelta(days=1)),
        ]

        created_tasks = {}
        position = 1000.0
        for project_key, number, title, status, priority, assignee, due in task_specs:
            project = projects[project_key]
            labels = []
            if number == 104:
                labels = ["Figma Specs v2"]
            if number == 118 and project_key == "NEX-WEB":
                labels = ["PR #42"]
            task, _ = Task.objects.update_or_create(
                project=project,
                number=number,
                defaults={
                    "title": title,
                    "description": self._description_for(number, title),
                    "status": status,
                    "priority": priority,
                    "assignee": assignee,
                    "reporter": alex if assignee != alex else maya,
                    "created_by": maya,
                    "due_date": due,
                    "position": position,
                    "labels": labels,
                    "completed_at": now - timedelta(days=1) if status == Task.Status.DONE else None,
                },
            )
            created_tasks[(project_key, number)] = task
            position += 1000.0

        nex104 = created_tasks[("NEX-WEB", 104)]
        Comment.objects.filter(task=nex104).delete()
        Comment.objects.create(
            task=nex104,
            author=alex,
            body=(
                "Figma UI Specs v2 are locked. Sidebar stays at **246px** on desktop; "
                "below **768px** collapse into an off-canvas drawer with Escape + focus restore."
            ),
        )
        Comment.objects.create(
            task=nex104,
            author=maya,
            body="Working the keyboard trap checklist before handoff to review.",
        )

        ActivityEvent.objects.filter(workspace=workspace).delete()
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.TASK_STATUS_CHANGED,
            actor=maya,
            project=cp,
            task=created_tasks[("NEX-CP", 118)],
            summary="Transitioned NEX-CP-118",
            metadata={"from": "in_progress", "to": "in_review"},
        )
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.SYSTEM,
            actor=daniel,
            project=ops,
            summary="Pushed 3 commits to feature/tenant-isolation",
            metadata={"ci": "Build #482 Passed", "branch": "feature/tenant-isolation"},
        )
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.COMMENT_ADDED,
            actor=alex,
            project=web,
            task=nex104,
            summary="Commented on NEX-WEB-104",
            metadata={"excerpt": "Figma UI Specs v2 are locked."},
        )
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.SYSTEM,
            actor=None,
            project=cp,
            summary="Automated smoke tests passed on main — Vercel Deploy #891",
            metadata={"deploy": "production"},
        )
        log_activity(
            workspace=workspace,
            event_type=ActivityEvent.EventType.PROJECT_UPDATED,
            actor=maya,
            project=web,
            summary="Updated Website Redesign target release to Nov 15",
            metadata={"due_date": str(web.due_date)},
        )

        self.stdout.write(self.style.SUCCESS(
            "Northstar Studio seeded. Demo password for all accounts: DemoPass1"
        ))
        self.stdout.write("Login: maya@northstar.studio / DemoPass1")

    def _description_for(self, number, title):
        if number == 104:
            return (
                "## Acceptance Criteria\n"
                "- Persistent sidebar width: **246px**\n"
                "- Viewports `< 768px`: collapse into off-canvas drawer\n"
                "- Escape key closes drawer and restores focus\n"
                "- Keyboard trap tested for accessibility\n"
            )
        return f"Implementation notes for {title}."
