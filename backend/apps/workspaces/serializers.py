from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.workspaces.permissions import ADMIN_ROLES

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


class WorkspaceCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    slug = serializers.SlugField(max_length=80, required=False, allow_blank=True)

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
        if not slug:
            raise serializers.ValidationError({"slug": "Could not derive a valid slug."})
        base = slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1

        workspace = Workspace.objects.create(name=name, slug=slug, created_by=user)
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceMembership.Role.OWNER,
            status=WorkspaceMembership.Status.ACTIVE,
            joined_at=timezone.now(),
        )
        return workspace


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(write_only=True, required=False)
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

    def validate_role(self, value):
        if value == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError(
                "Use ownership transfer to assign the owner role."
            )
        return value

    def create(self, validated_data):
        workspace = self.context["workspace"]
        email = (validated_data.pop("email", "") or "").lower().strip()
        if not email:
            raise serializers.ValidationError({"email": "Email is required."})
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            raise serializers.ValidationError(
                {"email": "No registered account exists for this email."}
            )
        existing = WorkspaceMembership.objects.filter(
            workspace=workspace, user=user
        ).first()
        if existing and existing.status != WorkspaceMembership.Status.REMOVED:
            raise serializers.ValidationError(
                {"email": "This user is already a member of the workspace."}
            )
        role = validated_data.get("role", WorkspaceMembership.Role.MEMBER)
        if existing:
            existing.role = role
            existing.status = WorkspaceMembership.Status.ACTIVE
            existing.joined_at = timezone.now()
            existing.save()
            return existing
        return WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=role,
            status=WorkspaceMembership.Status.ACTIVE,
            joined_at=timezone.now(),
        )


class MembershipRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMembership
        fields = ("role",)

    def validate_role(self, value):
        if value == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError(
                "Use ownership transfer to assign the owner role."
            )
        return value


class OwnershipTransferSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()
