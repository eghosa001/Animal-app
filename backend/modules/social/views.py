"""Guest-readable feed; only operator-approved and processed animal videos."""
from django.conf import settings
from django.db.models import Count, Exists, OuterRef, Q
from modules.safety.models import UserBlock
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .models import VideoLike, VideoPost
from .serializers import VideoPostSerializer


class PublicVideoFeedView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = VideoPostSerializer

    def get_queryset(self):
        # Without a trusted delivery domain, never advertise unplayable clips.
        if not settings.VIDEO_DELIVERY_HOST:
            return VideoPost.objects.none()
        queryset = (
            VideoPost.objects.filter(
                state=VideoPost.State.APPROVED,
                processed_at__isnull=False,
                moderated_at__isnull=False,
                moderated_by__isnull=False,
                creator__is_active=True,
            )
            .select_related(
                "creator", "listing__seller__seller_profile",
                "listing__animal__species",
            )
            .order_by("-created_at", "-id")
        )
        queryset = queryset.annotate(
            active_likes_count=Count(
                "likes", filter=Q(likes__user__is_active=True), distinct=True,
            ),
            approved_comments_count=Count(
                "comments", filter=Q(
                    comments__status="approved", comments__author__is_active=True,
                ), distinct=True,
            )
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                viewer_has_liked=Exists(VideoLike.objects.filter(
                    video=OuterRef("pk"), user=self.request.user,
                ))
            )
            outgoing = UserBlock.objects.filter(blocker=self.request.user).values("blocked_id")
            incoming = UserBlock.objects.filter(blocked=self.request.user).values("blocker_id")
            queryset = queryset.exclude(
                Q(creator_id__in=outgoing) | Q(creator_id__in=incoming)
            )
        return queryset


class VideoLikeView(APIView):
    """Idempotent per-user like/unlike; no public liker identity endpoint."""

    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "video_reaction"

    def _video(self, request, video_id):
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your active account before reacting")
        if not settings.VIDEO_DELIVERY_HOST:
            from rest_framework.exceptions import NotFound
            raise NotFound("Video unavailable")
        outgoing = UserBlock.objects.filter(blocker=request.user).values("blocked_id")
        incoming = UserBlock.objects.filter(blocked=request.user).values("blocker_id")
        return get_object_or_404(
            VideoPost.objects.filter(
                state=VideoPost.State.APPROVED,
                processed_at__isnull=False,
                moderated_at__isnull=False,
                moderated_by__isnull=False,
                creator__is_active=True,
            ).exclude(
                Q(creator_id__in=outgoing) | Q(creator_id__in=incoming)
            ),
            pk=video_id,
        )

    @staticmethod
    def _response(video, liked):
        return Response({
            "video_id": str(video.pk),
            "is_liked": liked,
            "likes_count": VideoLike.objects.filter(
                video=video, user__is_active=True,
            ).count(),
        })

    def put(self, request, video_id):
        video = self._video(request, video_id)
        VideoLike.objects.get_or_create(user=request.user, video=video)
        return self._response(video, True)

    def delete(self, request, video_id):
        video = self._video(request, video_id)
        VideoLike.objects.filter(user=request.user, video=video).delete()
        return self._response(video, False)
