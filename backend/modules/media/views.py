"""Private upload endpoints. No public object-store URLs or arbitrary object keys."""
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from modules.accounts.authentication import CustomerJWTAuthentication, require_staff_mfa
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from modules.accounts.models import SellerProfile
from modules.listings.models import Listing

from .models import MediaAccessEvent, MediaAsset
from .serializers import (
    ListingPhotoUploadSerializer, MediaAssetSerializer,
    MediaReviewSerializer, SellerEvidenceUploadSerializer,
)
from .services import create_listing_photo, create_seller_evidence, remove_draft_photo, review_listing_photo
from .storage import read_object


class ListingPhotoUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "media_upload"

    def post(self, request):
        serializer = ListingPhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = create_listing_photo(
            user=request.user, listing_id=serializer.validated_data["listing_id"],
            upload=serializer.validated_data["file"],
        )
        return Response(MediaAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class SellerEvidenceUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "media_upload"

    def post(self, request):
        serializer = SellerEvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = create_seller_evidence(
            user=request.user,
            upload=serializer.validated_data["file"],
            evidence_type=serializer.validated_data["evidence_type"],
            consent=serializer.validated_data["consent"],
        )
        return Response(MediaAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class MyMediaView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        assets = MediaAsset.objects.filter(owner=request.user).exclude(state=MediaAsset.State.REMOVED)[:100]
        return Response(MediaAssetSerializer(assets, many=True).data)


class MediaFileView(APIView):
    permission_classes = (AllowAny,)
    # Staff using Django Admin session cookies must be able to read assigned evidence.
    authentication_classes = (CustomerJWTAuthentication, SessionAuthentication)

    def get(self, request, asset_id):
        asset = get_object_or_404(
            MediaAsset.objects.select_related(
                "listing__seller__seller_profile", "listing__animal__species"
            ), pk=asset_id,
        )
        if asset.state == MediaAsset.State.REMOVED:
            raise Http404()
        user = request.user
        owner = user.is_authenticated and user.is_active and asset.owner_id == user.pk
        if asset.kind == MediaAsset.Kind.SELLER_EVIDENCE:
            reviewer = (
                user.is_authenticated and user.is_active and user.is_staff
                and user.has_perm("accounts.review_sellerprofile")
                and callable(getattr(user, "is_verified", None)) and user.is_verified()
            )
            if not owner and not reviewer:
                raise Http404()
            audit_purpose = "evidence_owner" if owner else "evidence_review"
        else:
            moderator = (
                user.is_authenticated and user.is_active and user.is_staff
                and user.has_perm("animal_media.review_mediaasset")
                and callable(getattr(user, "is_verified", None)) and user.is_verified()
            )
            seller_profile = getattr(asset.listing.seller, "seller_profile", None)
            public = (
                asset.state == MediaAsset.State.APPROVED
                and asset.listing.status == Listing.Status.ACTIVE
                and asset.listing.seller.is_active
                and seller_profile is not None and seller_profile.status == SellerProfile.Status.APPROVED
                and asset.listing.animal.species.trade_enabled
            )
            if not (public or owner or moderator):
                raise Http404()
            audit_purpose = "photo_owner" if owner else ("photo_review" if moderator else None)

        # Object content is never redirected to a public bucket.
        body = read_object(kind=asset.kind, key=asset.storage_key)
        if audit_purpose:
            MediaAccessEvent.objects.create(asset=asset, actor=user, purpose=audit_purpose)
        response = HttpResponse(body, content_type="image/jpeg")
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        response["Content-Security-Policy"] = "default-src 'none'; sandbox"
        if asset.kind == MediaAsset.Kind.SELLER_EVIDENCE:
            response["Content-Disposition"] = 'attachment; filename="verification-evidence.jpg"'
        else:
            response["Content-Disposition"] = 'inline; filename="animal-photo.jpg"'
        return response


class MediaReviewView(APIView):
    # Human moderation never accepts app JWT, including older staff JWTs.
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, asset_id):
        require_staff_mfa(request.user)
        serializer = MediaReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = get_object_or_404(
            MediaAsset.objects.filter(kind=MediaAsset.Kind.LISTING_PHOTO), pk=asset_id
        )
        reviewed = review_listing_photo(
            asset_id=asset.pk, reviewer=request.user,
            decision=serializer.validated_data["decision"],
            reason=serializer.validated_data["reason"],
        )
        return Response(MediaAssetSerializer(reviewed).data)


class DraftPhotoDeleteView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "media_upload"

    def delete(self, request, asset_id):
        remove_draft_photo(asset_id=asset_id, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
