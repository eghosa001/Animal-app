"""Participant-scoped offers; no payment endpoints or custody assertions."""
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from modules.chats.models import Conversation

from .models import AnimalOffer
from .serializers import (
    OfferCreateSerializer, OfferDecisionSerializer, OfferReadSerializer,
)
from .services import decide_offer, propose_offer


class ConversationOffersView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OfferReadSerializer
    throttle_scope = "offer_create"

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def _conversation(self):
        if not hasattr(self, "_selected"):
            self._selected = get_object_or_404(
                Conversation.objects.filter(
                    buyer=self.request.user,
                ) | Conversation.objects.filter(
                    seller=self.request.user,
                ),
                pk=self.kwargs["conversation_id"],
            )
        return self._selected

    def get_queryset(self):
        return AnimalOffer.objects.filter(
            conversation=self._conversation(),
        ).select_related("proposer").order_by("-created_at", "-id")

    def create(self, request, *args, **kwargs):
        conversation = self._conversation()
        form = OfferCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        offer, created = propose_offer(
            conversation_id=conversation.pk,
            actor=request.user, **form.validated_data,
        )
        return Response(
            OfferReadSerializer(offer).data, status=201 if created else 200,
        )


class OfferDecisionView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "offer_decide"

    def post(self, request, offer_id):
        # Query filtering occurs before any expensive row locking and prevents
        # guessing another person's offer status by UUID.
        offer = get_object_or_404(
            AnimalOffer.objects.filter(
                conversation__buyer=request.user,
            ) | AnimalOffer.objects.filter(
                conversation__seller=request.user,
            ),
            pk=offer_id,
        )
        form = OfferDecisionSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        decided = decide_offer(
            offer_id=offer.pk, actor=request.user,
            decision=form.validated_data["decision"],
        )
        return Response(OfferReadSerializer(decided).data)
