"""Seed portfolio demo evaluator accounts used on the login page."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_USERS = [
    {
        "email": "maya@northstar.dev",
        "password": "DemoPass1",
        "first_name": "Maya",
        "last_name": "Lin",
        "username": "maya.lin",
    },
    {
        "email": "daniel@northstar.dev",
        "password": "DemoPass1",
        "first_name": "Daniel",
        "last_name": "Vance",
        "username": "daniel.vance",
    },
]


class Command(BaseCommand):
    help = "Create or reset demo evaluator accounts (Maya Lin, Daniel Vance)."

    def handle(self, *args, **options):
        for demo in DEMO_USERS:
            email = demo["email"].lower()
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": demo["username"],
                    "first_name": demo["first_name"],
                    "last_name": demo["last_name"],
                    "is_active": True,
                },
            )
            user.username = demo["username"]
            user.first_name = demo["first_name"]
            user.last_name = demo["last_name"]
            user.is_active = True
            user.set_password(demo["password"])
            user.save()
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} demo user {email}"))

        self.stdout.write(self.style.SUCCESS("Demo evaluator accounts are ready."))
