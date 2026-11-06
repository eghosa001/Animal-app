"""Media operations: enforce ownership, usage limits and immutable moderator audit."""
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from modules.accounts.models import SellerProfile
from modules.listings.models import Listing

from .images import MAX_EVIDENCE_BYTES, MAX_LISTING_BYTES, sanitize_image
from .models import MediaAsset, MediaReviewEvent
from .storage import delete_object, put_object

MAX_LISTING_PHOTOS = 8
MAX_SELLER_EVIDENCE = 8


def _ensure_verified_seller(user):
    if not user.is_authenticated or not user.is_active or not user.is_email_verified:
        raise PermissionDenied("A verified, active seller account is required")
    seller = getattr(user, "seller_profile", None)
    if seller is None or seller.status not in (
        SellerProfile.Status.PENDING, SellerProfile.Status.APPROVED
    ):
        raise PermissionDenied("An eligible seller application is required")
    return seller


@transaction.atomic
def create_listing_photo(*, user, listing_id, upload):
    _ensure_verified_seller(user)
    listing = Listing.objects.select_for_update().filter(pk=listing_id, seller=user).first()
    if listing is None:
        # Do not disclose another seller's listing existence.
        raise PermissionDenied("The requested draft listing is unavailable")
    if listing.status != Listing.Status.DRAFT:
        raise ValidationError({"listing_id": ["Only draft listings can receive new photos"]})
    if MediaAsset.objects.filter(listing=listing, kind=MediaAsset.Kind.LISTING_PHOTO).count() >= MAX_LISTING_PHOTOS:
        raise ValidationError({"file": ["The listing photo limit has been reached"]})
    image = sanitize_image(upload, max_bytes=MAX_LISTING_BYTES)
    asset_id = uuid.uuid4()
    key = f"listing-photos/{asset_id.hex}.jpg"
    put_object(kind=MediaAsset.Kind.LISTING_PHOTO, key=key, body=image.body)
    try:
        return MediaAsset.objects.create(
            id=asset_id, owner=user, listing=listing, kind=MediaAsset.Kind.LISTING_PHOTO,
            storage_key=key, content_type="image/jpeg", size_bytes=len(image.body),
            width=image.width, height=image.height, sha256=image.sha256,
        )
    except Exception:
        delete_object(kind=MediaAsset.Kind.LISTING_PHOTO, key=key)
        raise


@transaction.atomic
def create_seller_evidence(*, user, upload, evidence_type, consent):
    if consent is not True:
        raise ValidationError({"consent": ["Consent to private verification document processing is required"]})
    _ensure_verified_seller(user)
    SellerProfile.objects.select_for_update().get(user=user)
    if MediaAsset.objects.filter(owner=user, kind=MediaAsset.Kind.SELLER_EVIDENCE).count() >= MAX_SELLER_EVIDENCE:
        raise ValidationError({"file": ["The verification evidence limit has been reached"]})
    image = sanitize_image(upload, max_bytes=MAX_EVIDENCE_BYTES)
    asset_id = uuid.uuid4()
    key = f"seller-evidence/{asset_id.hex}.jpg"
    put_object(kind=MediaAsset.Kind.SELLER_EVIDENCE, key=key, body=image.body)
    try:
        return MediaAsset.objects.create(
            id=asset_id, owner=user, kind=MediaAsset.Kind.SELLER_EVIDENCE,
            evidence_type=evidence_type, storage_key=key, content_type="image/jpeg",
            size_bytes=len(image.body), width=image.width, height=image.height,
            sha256=image.sha256,
        )
    except Exception:
        delete_object(kind=MediaAsset.Kind.SELLER_EVIDENCE, key=key)
        raise


@transaction.atomic
def review_listing_photo(*, asset_id, reviewer, decision, reason):
    if not reviewer.is_authenticated or not reviewer.is_active or not reviewer.is_staff or not reviewer.has_perm(
        "animal_media.review_mediaasset"
    ):
        raise PermissionDenied("Media review permission is required")
    if decision not in ("approve", "reject"):
        raise ValidationError({"decision": ["Invalid review decision"]})
    reason = str(reason or "").strip()
    if not 20 <= len(reason) <= 500:
        raise ValidationError({"reason": ["Review reason must be 20–500 characters"]})
    asset = MediaAsset.objects.select_for_update().select_related(
        "listing__animal__species", "listing__seller", "owner"
    ).get(pk=asset_id, kind=MediaAsset.Kind.LISTING_PHOTO)
    if reviewer.pk == asset.owner_id:
        raise PermissionDenied("Cannot moderate your own photograph")
    if asset.state != MediaAsset.State.PENDING:
        raise ValidationError({"decision": ["Photograph is already reviewed"]})
    if decision == "approve":
        listing = asset.listing
        seller = listing.seller
        seller_profile = getattr(seller, "seller_profile", None)
        if seller_profile is None or seller_profile.status != SellerProfile.Status.APPROVED:
            raise ValidationError({"seller": ["Only approved sellers may publish photographs"]})
        if not seller.is_active or not seller.is_email_verified or not listing.animal.species.trade_enabled:
            raise ValidationError({"listing": ["Seller or species is ineligible for publication"]})
        if listing.status not in (Listing.Status.DRAFT, Listing.Status.PENDING, Listing.Status.ACTIVE):
            raise ValidationError({"listing": ["Listing is not eligible for photo publication"]})
    asset.state = MediaAsset.State.APPROVED if decision == "approve" else MediaAsset.State.REJECTED
    asset.reviewed_at = timezone.now()
    asset.reviewed_by = reviewer
    asset.review_note = reason
    asset.save(update_fields=("state", "reviewed_at", "reviewed_by", "review_note"))
    MediaReviewEvent.objects.create(asset=asset, actor=reviewer, decision=decision, reason=reason)
    return asset
