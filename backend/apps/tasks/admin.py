from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "project", "status", "priority", "assignee")
    list_filter = ("status", "priority")
    search_fields = ("title",)
