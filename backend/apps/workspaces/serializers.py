from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.workspaces.models import Workspace, WorkspaceInvite, WorkspaceMembership
from apps.workspaces.permissions import ADMIN_ROLES
from config.serializers import StrictFieldsMixin

User = get_user_model()


class WorkspaceSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "slug",
            "team_type",
            "timezone",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "role",
            "member_count",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "archived_at",
            "role",
            "member_count",
        )

    def get_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = next(
            (
                m
                for m in obj.memberships.all()
                if m.user_id == request.user.id
                and m.status == WorkspaceMembership.Status.ACTIVE
            ),
            None,
        )
        if membership is None:
            membership = WorkspaceMembership.objects.filter(
                workspace=obj,
                user=request.user,
                status=WorkspaceMembership.Status.ACTIVE,
            ).first()
        return membership.role if membership else None

    def get_member_count(self, obj):
        if hasattr(obj, "active_member_count"):
            return obj.active_member_count
        return obj.memberships.filter(status=WorkspaceMembership.Status.ACTIVE).count()


class WorkspaceCreateSerializer(StrictFieldsMixin, serializers.Serializer):
    name = serializers.CharField(max_length=120)
    slug = serializers.SlugField(max_length=80, required=False, allow_blank=True)
    team_type = serializers.ChoiceField(
        choices=Workspace.TeamType.choices,
        required=False,
        default=Workspace.TeamType.SOFTWARE,
    )

    def validate_slug(self, value):
        slug = (value or "").strip().lower()
        if not slug:
            return slug
        if Workspace.objects.filter(slug=slug).exists():
            raise serializers.ValidationError("This workspace URL is already taken.")
        return slug

    def create(self, validated_data):
        user = self.context["request"].user
        name = validated_data["name"].strip()
        slug = validated_data.get("slug") or slugify(name)
        team_type = validated_data.get("team_type") or Workspace.TeamType.SOFTWARE
        if not slug:
            raise serializers.ValidationError({"slug": "Could not derive a valid slug."})
        base = slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1

        workspace = Workspace.objects.create(
            name=name, slug=slug, team_type=team_type, created_by=user
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
            joined_at=timezone.now(),
        )
        from apps.accounts.onboarding import get_or_create_onboarding

        get_or_create_onboarding(user, workspace)
        return workspace


class MembershipSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(write_only=True, required=True)
    project_access_count = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceMembership
        fields = (
            "id",
            "user",
            "email",
            "role",
            "status",
            "joined_at",
            "created_at",
            "project_access_count",
        )
        read_only_fields = ("id", "user", "joined_at", "created_at", "project_access_count")

    def get_project_access_count(self, obj):
        workspace = obj.workspace
        total = workspace.projects.filter(archived_at__isnull=True).count()
        if obj.role in ADMIN_ROLES | {WorkspaceMembership.Role.PROJECT_MANAGER, WorkspaceMembership.Role.MEMBER}:
            return total
        return total

    def validate_email(self, value):
        return (value or "").lower().strip()

    def validate_role(self, value):
        if value == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError(
                "Use ownership transfer to assign the owner role."
            )
        return value


class WorkspaceInviteSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    invite_url = serializers.SerializerMethodField()
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    workspace_slug = serializers.CharField(source="workspace.slug", read_only=True)

    class Meta:
        model = WorkspaceInvite
        fields = (
            "id",
            "email",
            "role",
            "created_at",
            "expires_at",
            "accepted_at",
            "invite_url",
            "workspace_name",
            "workspace_slug",
        )
        read_only_fields = fields

    def get_invite_url(self, obj):
        from apps.workspaces.invites import invite_frontend_url

        return invite_frontend_url(obj.token)


class MembershipRoleUpdateSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMembership
        fields = ("role",)

    def validate_role(self, value):
        if value == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError(
                "Use ownership transfer to assign the owner role."
            )
        return value


class OwnershipTransferSerializer(StrictFieldsMixin, serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()
