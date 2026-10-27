"""Seed portfolio demo evaluator accounts used on the login page."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create demo evaluator accounts and Northstar Studio seed data."

    def handle(self, *args, **options):
        call_command("seed_northstar")
