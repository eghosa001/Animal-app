"""User-scoped blocking and safe content reports for the moderation queue."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from modules.accounts.models import SellerProfile, User
from modules.chats.models import ChatMessage
from modules.listings.models import Listing
from modules.social.models import VideoPost

from .models import SafetyReport, UserBlock
from .serializers import (
    BlockCreateSerializer, BlockReadSerializer,
    ReportCreateSerializer, ReportReadSerializer,
)


class WriteRateMixin:
    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()


class BlocksView(WriteRateMixin, generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BlockReadSerializer
    throttle_scope = "safety_block"

    def get_queryset(self):
        return UserBlock.objects.filter(
            blocker=self.request.user,
        ).select_related("blocked").order_by("-created_at")

    def create(self, request, *args, **kwargs):
        if not request.user.is_active:
            raise PermissionDenied("Active account required")
        form = BlockCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        target_id = form.validated_data["blocked_user_id"]
        if request.user.pk == target_id:
            raise ValidationError({"blocked_user_id": "Cannot block yourself"})
        target = get_object_or_404(User.objects.filter(is_active=True), pk=target_id)
        block, created = UserBlock.objects.get_or_create(
            blocker=request.user, blocked=target,
        )
        return Response(
            BlockReadSerializer(block).data, status=201 if created else 200,
        )


class UnblockView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, target_id):
        item = get_object_or_404(
            UserBlock.objects.filter(blocker=request.user, blocked_id=target_id),
        )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportsView(WriteRateMixin, generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportReadSerializer
    throttle_scope = "safety_report"

    def get_queryset(self):
        return SafetyReport.objects.filter(
            reporter=self.request.user,
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your email before submitting a report")
        form = ReportCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        attrs = form.validated_data
        target = attrs["target_type"]
        object_id = attrs["target_id"]
        kwargs = {}
        if target == "video":
            video = get_object_or_404(
                VideoPost.objects.filter(
                    state=VideoPost.State.APPROVED,
                    processed_at__isnull=False,
                    creator__is_active=True,
                ), pk=object_id,
            )
            kwargs["video"] = video
        elif target == "listing":
            listing = get_object_or_404(
                Listing.objects.filter(
                    Q(status=Listing.Status.ACTIVE,
                      seller__is_active=True,
                      seller__seller_profile__status=SellerProfile.Status.APPROVED,
                      animal__species__trade_enabled=True)
                    | Q(conversations__buyer=request.user)
                    | Q(seller=request.user),
                ).distinct(),
                pk=object_id,
            )
            kwargs["listing"] = listing
        elif target == "message":
            message = get_object_or_404(
                ChatMessage.objects.filter(
                    Q(conversation__buyer=request.user) |
                    Q(conversation__seller=request.user),
                ), pk=object_id,
            )
            kwargs["message"] = message
        else:
            subject = get_object_or_404(
                User.objects.filter(is_active=True), pk=object_id,
            )
            if subject.pk == request.user.pk:
                raise ValidationError({"target_id": "Cannot report your own account"})
            kwargs["subject_user"] = subject

        item = SafetyReport.objects.create(
            reporter=request.user,
            category=attrs["category"],
            detail=attrs["detail"],
            **kwargs,
        )
        return Response(ReportReadSerializer(item).data, status=201)
