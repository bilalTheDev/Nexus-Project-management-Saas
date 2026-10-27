from django.urls import path

from apps.comments.views import CommentDetailView, TaskCommentListCreateView

urlpatterns = [
    path(
        "tasks/<uuid:task_id>/comments/",
        TaskCommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "comments/<uuid:comment_id>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),
]
