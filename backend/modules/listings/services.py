"""Server-authoritative listing transitions with database row locking."""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from modules.accounts.models import SellerProfile

from .models import Listing, ListingEvent


def validate_trade_permissions(listing):
    seller = getattr(listing.seller, "seller_profile", None)
    if seller is None or seller.status != SellerProfile.Status.APPROVED:
        raise ValidationError({"seller": ["Seller must be approved before publication"]})
    if not listing.seller.is_email_verified:
        raise ValidationError({"seller": ["Seller email verification is required"]})
    if not listing.animal.species.trade_enabled:
        raise ValidationError({"species": ["This species is not enabled for trading"]})
    if listing.animal.owner_id != listing.seller_id:
        raise ValidationError({"animal": ["Animal owner must match listing seller"]})


@transaction.atomic
def submit_listing(listing_id, actor):
    listing = Listing.objects.select_for_update().select_related(
        "seller", "animal__species"
    ).get(pk=listing_id, seller=actor)
    if listing.status != Listing.Status.DRAFT:
        raise ValidationError({"status": ["Only draft listings can be submitted"]})
    validate_trade_permissions(listing)
    listing.status = Listing.Status.PENDING
    listing.submitted_at = timezone.now()
    listing.save(update_fields=["status", "submitted_at"])
    ListingEvent.objects.create(listing=listing, actor=actor, from_status="draft", to_status="pending")
    return listing


@transaction.atomic
def approve_listing(listing_id, actor):
    if not actor.is_staff or not actor.has_perm("listings.change_listing"):
        raise ValidationError({"reviewer": ["Authorized moderator permission required"]})
    listing = Listing.objects.select_for_update().select_related(
        "seller", "animal__species"
    ).get(pk=listing_id)
    if listing.status != Listing.Status.PENDING:
        raise ValidationError({"status": ["Only submitted listings can be approved"]})
    validate_trade_permissions(listing)
    listing.status = Listing.Status.ACTIVE
    listing.approved_at = timezone.now()
    listing.save(update_fields=["status", "approved_at"])
    ListingEvent.objects.create(listing=listing, actor=actor, from_status="pending", to_status="active")
    return listing
