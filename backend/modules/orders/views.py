"""Authenticated pre-checkout order receipts only; not a payment API."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import OrderIntent
from .serializers import (
    OrderIntentCancelSerializer, OrderIntentCreateSerializer, OrderIntentReadSerializer,
)
from .services import cancel_order_intent, create_order_intent


class OrderIntentsView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderIntentReadSerializer
    throttle_scope = "order_intent_create"

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return OrderIntent.objects.filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        ).select_related("buyer", "seller").order_by("-created_at", "-id")

    def create(self, request, *args, **kwargs):
        form = OrderIntentCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        order, created = create_order_intent(
            accepted_offer_id=form.validated_data["accepted_offer_id"],
            buyer=request.user,
            request_nonce=form.validated_data["request_nonce"],
        )
        return Response(
            OrderIntentReadSerializer(order).data, status=201 if created else 200,
        )


class OrderIntentDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderIntentReadSerializer

    def get_queryset(self):
        return OrderIntent.objects.filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        ).select_related("buyer", "seller")

    lookup_url_kwarg = "intent_id"


class OrderIntentCancelView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "order_intent_cancel"

    def post(self, request, intent_id):
        item = get_object_or_404(
            OrderIntent.objects.filter(
                Q(buyer=request.user) | Q(seller=request.user)
            ), pk=intent_id,
        )
        form = OrderIntentCancelSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        order, _ = cancel_order_intent(
            intent_id=item.pk, actor=request.user,
            reason=form.validated_data["reason"],
        )
        return Response(OrderIntentReadSerializer(order).data)
