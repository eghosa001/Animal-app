"""Public listings, seller drafts, and guarded publication request."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from modules.accounts.models import SellerProfile
from modules.safety.models import UserBlock

from .models import Listing
from .serializers import ListingCreateSerializer, ListingReadSerializer
from .services import submit_listing


class ListingViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        queryset = Listing.objects.select_related("animal__species", "seller")
        if self.action in ("mine", "submit", "partial_update"):
            return queryset.filter(seller=self.request.user) if self.request.user.is_authenticated else queryset.none()
        public = queryset.filter(
            status=Listing.Status.ACTIVE,
            seller__seller_profile__status=SellerProfile.Status.APPROVED,
            seller__is_active=True,
            animal__species__trade_enabled=True,
        )
        if self.request.user.is_authenticated:
            outgoing = UserBlock.objects.filter(
                blocker=self.request.user,
            ).values("blocked_id")
            incoming = UserBlock.objects.filter(
                blocked=self.request.user,
            ).values("blocker_id")
            public = public.exclude(
                Q(seller_id__in=outgoing) | Q(seller_id__in=incoming)
            )
        return public

    def get_serializer_class(self):
        return ListingCreateSerializer if self.action in ("create", "partial_update") else ListingReadSerializer

    def get_permissions(self):
        return [AllowAny()] if self.action in ("list", "retrieve") else [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Creation accepts nested write-only fields; return the public read schema instead.
        return Response(ListingReadSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        listing = get_object_or_404(
            self.get_queryset().filter(status=Listing.Status.DRAFT),
            pk=kwargs.get("pk"),
        )
        serializer = ListingCreateSerializer(
            listing, data=request.data, partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(ListingReadSerializer(updated).data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        if not self.request.user.is_active or not self.request.user.is_email_verified:
            raise PermissionDenied("Verify your email before creating a listing")
        seller = getattr(self.request.user, "seller_profile", None)
        if seller is None or seller.status not in (SellerProfile.Status.PENDING, SellerProfile.Status.APPROVED):
            raise PermissionDenied("Apply as a seller before creating a listing")
        serializer.save(seller=self.request.user)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(ListingReadSerializer(page, many=True).data)
        return Response(ListingReadSerializer(queryset, many=True).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        listing = get_object_or_404(self.get_queryset(), pk=pk)
        updated = submit_listing(listing.id, request.user)
        return Response(ListingReadSerializer(updated).data, status=status.HTTP_200_OK)
