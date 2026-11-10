"""Guest-readable feed; only operator-approved and processed animal videos."""
from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import VideoPost
from .serializers import VideoPostSerializer


class PublicVideoFeedView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = VideoPostSerializer

    def get_queryset(self):
        # Without a trusted delivery domain, never advertise unplayable clips.
        if not settings.VIDEO_DELIVERY_HOST:
            return VideoPost.objects.none()
        return (
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
