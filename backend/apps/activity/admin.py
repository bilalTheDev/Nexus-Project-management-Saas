from django.contrib import admin

from apps.activity.models import ActivityEvent


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "workspace", "actor", "summary", "created_at")
    list_filter = ("event_type",)
    search_fields = ("summary",)
