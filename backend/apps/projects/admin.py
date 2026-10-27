from django.contrib import admin

from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "workspace", "status", "lead", "archived_at")
    list_filter = ("status",)
    search_fields = ("name", "key")
