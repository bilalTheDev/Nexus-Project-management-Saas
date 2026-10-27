"""Custom user model — defined at project start before first migration."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Email-first user identity for Nexus authentication."""

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email
