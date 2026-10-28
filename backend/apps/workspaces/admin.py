from django.contrib import admin

from apps.workspaces.models import Workspace, WorkspaceInvite, WorkspaceMembership


class MembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at", "archived_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ("workspace", "user", "role", "status", "joined_at")
    list_filter = ("role", "status")
    search_fields = ("user__email", "workspace__slug")


@admin.register(WorkspaceInvite)
class WorkspaceInviteAdmin(admin.ModelAdmin):
    list_display = ("email", "workspace", "role", "created_at", "expires_at", "accepted_at")
    list_filter = ("role",)
    search_fields = ("email", "workspace__slug", "token")
    readonly_fields = ("token", "created_at")
