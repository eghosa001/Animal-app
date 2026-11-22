"""Fail-closed, idempotent public comments on approved animal videos."""
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from modules.safety.models import UserBlock

from .models import VideoComment, VideoPost
from .serializers import VideoCommentCreateSerializer, VideoCommentSerializer


def visible_video(video_id, user):
    if not settings.VIDEO_DELIVERY_HOST:
        from rest_framework.exceptions import NotFound
        raise NotFound("Video unavailable")
    videos = VideoPost.objects.filter(
        pk=video_id,
        state=VideoPost.State.APPROVED,
        processed_at__isnull=False,
        moderated_at__isnull=False,
        moderated_by__isnull=False,
        creator__is_active=True,
    )
    if user.is_authenticated:
        outgoing = UserBlock.objects.filter(blocker=user).values("blocked_id")
        incoming = UserBlock.objects.filter(blocked=user).values("blocker_id")
        videos = videos.exclude(
            Q(creator_id__in=outgoing) | Q(creator_id__in=incoming)
        )
    return get_object_or_404(videos)


class VideoCommentsView(generics.ListCreateAPIView):
    """Guests read approved comments; verified users submit to staff review."""
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VideoCommentCreateSerializer
        return VideoCommentSerializer

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "video_comment"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        video = visible_video(self.kwargs["video_id"], self.request.user)
        comments = VideoComment.objects.filter(
            video=video, status=VideoComment.Status.APPROVED,
            author__is_active=True,
        ).select_related("author").order_by("-created_at", "-id")
        if self.request.user.is_authenticated:
            outgoing = UserBlock.objects.filter(
                blocker=self.request.user,
            ).values("blocked_id")
            incoming = UserBlock.objects.filter(
                blocked=self.request.user,
            ).values("blocker_id")
            comments = comments.exclude(
                Q(author_id__in=outgoing) | Q(author_id__in=incoming)
            )
        return comments

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise NotAuthenticated("Sign in to comment")
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your active account before commenting")
        video = visible_video(kwargs["video_id"], request.user)
        form = VideoCommentCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        data = form.validated_data
        with transaction.atomic():
            comment, created = VideoComment.objects.get_or_create(
                author=request.user, client_nonce=data["client_nonce"],
                defaults={"video": video, "body": data["body"]},
            )
            if comment.video_id != video.id or comment.body != data["body"]:
                raise ValidationError({"client_nonce": "Nonce already belongs to another comment"})
        return Response({
            "id": str(comment.pk), "status": comment.status,
            "created_at": comment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class VideoCommentDeleteView(APIView):
    """Owner can withdraw any own comment; withdrawal never republishes it."""
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "video_comment"

    def delete(self, request, video_id, comment_id):
        if not request.user.is_active:
            raise PermissionDenied("Active account required")
        comment = get_object_or_404(
            VideoComment, pk=comment_id, video_id=video_id, author=request.user,
        )
        VideoComment.objects.filter(pk=comment.pk).exclude(
            status=VideoComment.Status.REMOVED,
        ).update(status=VideoComment.Status.REMOVED)
        return Response(status=status.HTTP_204_NO_CONTENT)
