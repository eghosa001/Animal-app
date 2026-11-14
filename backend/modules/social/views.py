"""Guest-readable feed; only operator-approved and processed animal videos."""
from django.conf import settings
from django.db.models import Q
from modules.safety.models import UserBlock
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
        if self.request.user.is_authenticated:
            outgoing = UserBlock.objects.filter(blocker=self.request.user).values("blocked_id")
            incoming = UserBlock.objects.filter(blocked=self.request.user).values("blocker_id")
            queryset = queryset.exclude(
                Q(creator_id__in=outgoing) | Q(creator_id__in=incoming)
            )
        return queryset
