from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "body", "created_at", "updated_at")
        read_only_fields = ("id", "task", "author", "created_at", "updated_at")


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body",)

    def create(self, validated_data):
        return Comment.objects.create(
            task=self.context["task"],
            author=self.context["request"].user,
            **validated_data,
        )
