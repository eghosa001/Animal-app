"""Authenticated, listing-linked and fully participant-scoped chat HTTP API."""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from modules.accounts.models import SellerProfile
from modules.listings.models import Listing

from .models import ChatMessage, Conversation
from .serializers import (
    ChatMessageCreateSerializer, ChatMessageReadSerializer,
    ConversationReadSerializer, ConversationStartSerializer, chat_is_writable,
)


class ParticipantThrottleMixin:
    """Write-specific throttles without starving inbox refresh or message reads."""
    throttle_scope = None

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()


class ConversationsView(ParticipantThrottleMixin, generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConversationReadSerializer
    throttle_scope = "chat_start"

    def get_queryset(self):
        return (
            Conversation.objects.filter(
                Q(buyer=self.request.user) | Q(seller=self.request.user),
            ).select_related(
                "buyer", "seller", "seller__seller_profile",
                "listing", "listing__animal__species",
            ).order_by("-updated_at", "-id")
        )

    def create(self, request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your email before contacting a seller")
        data = ConversationStartSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        listing = get_object_or_404(
            Listing.objects.select_related(
                "seller", "seller__seller_profile", "animal__species",
            ).filter(
                status=Listing.Status.ACTIVE,
                seller__is_active=True,
                seller__seller_profile__status=SellerProfile.Status.APPROVED,
                animal__species__trade_enabled=True,
            ),
            pk=data.validated_data["listing_id"],
        )
        if listing.seller_id == request.user.pk:
            raise ValidationError({"listing_id": "Cannot message your own listing"})
        with transaction.atomic():
            conversation, created = Conversation.objects.get_or_create(
                listing=listing, buyer=request.user,
                defaults={"seller": listing.seller},
            )
        serializer = ConversationReadSerializer(
            conversation, context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=201 if created else 200)


class ConversationMessagesView(
    ParticipantThrottleMixin, generics.ListCreateAPIView,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatMessageReadSerializer
    throttle_scope = "chat_send"

    def _conversation(self):
        if not hasattr(self, "_selected_conversation"):
            self._selected_conversation = get_object_or_404(
                Conversation.objects.select_related(
                    "buyer", "seller", "seller__seller_profile",
                    "listing", "listing__animal__species",
                ).filter(
                    Q(buyer=self.request.user) | Q(seller=self.request.user),
                ),
                pk=self.kwargs["conversation_id"],
            )
        return self._selected_conversation

    def get_queryset(self):
        return ChatMessage.objects.filter(
            conversation=self._conversation(),
        ).select_related("sender").order_by("-created_at", "-id")

    def create(self, request, *args, **kwargs):
        conversation = self._conversation()
        if not request.user.is_active or not request.user.is_email_verified:
            raise PermissionDenied("Verify your email before sending messages")
        if not chat_is_writable(conversation):
            raise PermissionDenied("This animal listing is no longer available for messaging")
        form = ChatMessageCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        payload = form.validated_data
        with transaction.atomic():
            # Validate again while holding the conversation lock, preventing
            # concurrent message writes from racing status changes.
            locked = Conversation.objects.select_for_update(of=("self",)).select_related(
                "buyer", "seller", "seller__seller_profile",
                "listing", "listing__animal__species",
            ).get(pk=conversation.pk)
            if not chat_is_writable(locked):
                raise PermissionDenied("This listing is no longer available for messaging")
            msg, created = ChatMessage.objects.get_or_create(
                conversation=locked, sender=request.user,
                client_nonce=payload["client_nonce"],
                defaults={"body": payload["body"]},
            )
            if not created and msg.body != payload["body"]:
                raise ValidationError({"client_nonce": "Reused idempotency ID with different text"})
            if created:
                locked.updated_at = timezone.now()
                locked.save(update_fields=("updated_at",))
        return Response(
            ChatMessageReadSerializer(msg).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
