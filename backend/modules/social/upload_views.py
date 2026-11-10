"""Direct-upload tickets are private; Stream webhooks never auto-publish videos."""
import json
import re
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from modules.accounts.models import SellerProfile, User
from modules.listings.models import Listing

from .models import VideoPost
from .provider import request_private_upload_ticket, verify_webhook_signature


class TicketSerializer(serializers.Serializer):
    caption = serializers.CharField(min_length=4, max_length=400)
    rights_attested = serializers.BooleanField()
    animal_topic_attested = serializers.BooleanField()
    listing_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs["rights_attested"] or not attrs["animal_topic_attested"]:
            raise serializers.ValidationError(
                "Confirm your rights to the footage and its animal-related topic"
            )
        return attrs


class VideoUploadTicketView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "video_ticket"

    def post(self, request):
        if not settings.STREAM_UPLOADS_ENABLED:
            return Response({"detail": "Video uploads are not enabled"}, status=503)
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your email to post animal videos")
        form = TicketSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        linked_listing = None
        if form.validated_data.get("listing_id"):
            linked_listing = get_object_or_404(
                Listing.objects.filter(
                    seller=request.user, seller__is_active=True,
                    seller__seller_profile__status=SellerProfile.Status.APPROVED,
                    status=Listing.Status.ACTIVE,
                    animal__species__trade_enabled=True,
                ),
                pk=form.validated_data["listing_id"],
            )
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            # Keep a hard per-account cap in addition to distributed IP/user throttles.
            recent = VideoPost.objects.filter(
                creator=request.user, created_at__gte=timezone.now() - timedelta(hours=24),
            ).count()
            if recent >= 8:
                raise Throttled(wait=3600, detail="Daily video upload limit reached")
            uid, upload_url, expires_at = request_private_upload_ticket(request.user.pk)
            post = VideoPost.objects.create(
                creator=request.user,
                caption=form.validated_data["caption"],
                video_uid=uid,
                listing=linked_listing,
                rights_attested=True,
                animal_topic_attested=True,
                upload_expires_at=expires_at,
            )
        return Response({
            "id": str(post.pk),
            "upload_url": upload_url,
            "expires_at": expires_at.isoformat(),
            "status": post.state,
        }, status=status.HTTP_201_CREATED)


class StreamWebhookView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        raw_body = request.body
        if len(raw_body) > 64 * 1024:
            return Response({"detail": "Body too large"}, status=413)
        verify_webhook_signature(raw_body, request.headers.get("Webhook-Signature", ""))
        try:
            payload = json.loads(raw_body)
        except (ValueError, UnicodeDecodeError):
            raise ValidationError("Malformed Stream webhook") from None
        uid = payload.get("uid") if isinstance(payload, dict) else None
        if not isinstance(uid, str) or not re.fullmatch(r"[a-fA-F0-9]{32}", uid):
            raise ValidationError("Invalid Stream video UID")
        with transaction.atomic():
            post = VideoPost.objects.select_for_update().filter(video_uid=uid).first()
            if post is None or post.state != VideoPost.State.PENDING:
                return HttpResponse(status=204)
            state = payload.get("status")
            if not isinstance(state, dict):
                raise ValidationError("Invalid Stream processing state")
            if state.get("state") == "error":
                code = state.get("errReasonCode", "processing_failed")
                post.state = VideoPost.State.REJECTED
                post.processing_error = str(code)[:80]
                post.save(update_fields=("state", "processing_error"))
            elif state.get("state") == "ready" and payload.get("readyToStream") is True:
                try:
                    pct = float(state.get("pctComplete", 0))
                    duration = float(payload.get("duration", 0))
                except (ValueError, TypeError):
                    raise ValidationError("Invalid Stream duration or progress") from None
                if duration <= 0 or duration > 60:
                    post.state = VideoPost.State.REJECTED
                    post.processing_error = "duration_not_allowed"
                    post.save(update_fields=("state", "processing_error"))
                elif pct >= 100:
                    post.processed_at = timezone.now()
                    post.processing_error = ""
                    post.save(update_fields=("processed_at", "processing_error"))
            # Upload completion changes processing state only, never public approval.
        return HttpResponse(status=204)


class VideoUploadCapabilitiesView(APIView):
    """Public feature flag prevents wasted video selection in disabled environments."""
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return Response({
            "enabled": bool(settings.STREAM_UPLOADS_ENABLED),
            "max_duration_seconds": 60,
            "max_file_bytes": 200_000_000,
        })


class MyVideoStatusSerializer(serializers.ModelSerializer):
    processed = serializers.SerializerMethodField()

    class Meta:
        model = VideoPost
        fields = ("id", "caption", "state", "processed", "created_at")
        read_only_fields = fields

    def get_processed(self, obj):
        return obj.processed_at is not None


class MyVideoPostsView(ListAPIView):
    """Private, per-owner processing status, never provider UID or upload token."""
    permission_classes = (IsAuthenticated,)
    serializer_class = MyVideoStatusSerializer

    def get_queryset(self):
        return VideoPost.objects.filter(
            creator=self.request.user,
        ).order_by("-created_at", "-id")
