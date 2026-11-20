"""Safe, row-locked pre-checkout records; no inventory, payment or custody effect."""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from modules.chats.serializers import chat_is_writable
from modules.listings.models import Listing
from modules.offers.models import AnimalOffer

from .models import OrderIntent, OrderIntentEvent


def _require_verified_buyer(actor):
    if not actor.is_active or not actor.is_email_verified:
        raise PermissionDenied("Active, verified buyer account required")


def _audit(order, actor, before, after, reason):
    OrderIntentEvent.objects.create(
        order=order, actor=actor,
        from_status=before, to_status=after, reason=reason,
    )


@transaction.atomic
def create_order_intent(*, accepted_offer_id, buyer, request_nonce):
    """One listing/offer = at most one intent, no reservation or money movement."""
    _require_verified_buyer(buyer)
    # No privacy disclosure: caller's accepted buyer offer must match before locking.
    offer_stub = AnimalOffer.objects.filter(
        pk=accepted_offer_id,
        status=AnimalOffer.Status.ACCEPTED,
        conversation__buyer=buyer,
    ).values("conversation__listing_id").first()
    if offer_stub is None:
        raise ValidationError("Accepted buyer price agreement is required")

    # Lock the listing even across multiple conversations and concurrent devices.
    listing = Listing.objects.select_for_update(of=("self",)).select_related(
        "animal", "animal__species", "seller", "seller__seller_profile",
    ).get(pk=offer_stub["conversation__listing_id"])
    offer = AnimalOffer.objects.select_related(
        "conversation", "conversation__buyer", "conversation__seller",
        "conversation__seller__seller_profile",
        "conversation__listing", "conversation__listing__animal__species",
    ).get(pk=accepted_offer_id)

    if offer.status != AnimalOffer.Status.ACCEPTED:
        raise ValidationError("The agreed price is no longer accepted")
    if offer.conversation.buyer_id != buyer.pk:
        raise PermissionDenied("Only the agreeing buyer can create an order request")

    existing = OrderIntent.objects.filter(listing=listing).first()
    if existing is not None:
        if (
            existing.buyer_id == buyer.pk
            and existing.accepted_offer_id == offer.pk
            and existing.request_nonce == request_nonce
        ):
            return existing, False
        raise ValidationError("A checkout request already exists for this animal")

    nonce_used = OrderIntent.objects.filter(buyer=buyer, request_nonce=request_nonce).exists()
    if nonce_used:
        raise ValidationError({"request_nonce": "Request identifier was used for another animal"})
    if listing.status != Listing.Status.ACTIVE or not chat_is_writable(offer.conversation):
        raise PermissionDenied("This animal is no longer eligible for checkout preparation")
    if offer.amount_minor > listing.price_minor or offer.amount_minor < 1:
        raise ValidationError("Listing price changed; a new reviewed agreement is required")
    if offer.currency != listing.currency:
        raise ValidationError("Listing currency changed; a new agreement is required")
    if offer.conversation.seller_id != listing.seller_id or listing.animal.owner_id != listing.seller_id:
        raise ValidationError("Animal and seller identity mismatch")

    intent = OrderIntent.objects.create(
        accepted_offer=offer, listing=listing, buyer=buyer, seller=listing.seller,
        request_nonce=request_nonce,
        animal_id_snapshot=listing.animal_id,
        animal_name_snapshot=listing.animal.name,
        listing_title_snapshot=listing.title,
        listing_region_snapshot=listing.region,
        price_minor=offer.amount_minor,
        currency=offer.currency,
        fulfillment_mode=OrderIntent.FulfillmentMode.PICKUP,
        status=OrderIntent.Status.AWAITING_PARTNER,
    )
    _audit(
        intent, buyer, "", OrderIntent.Status.AWAITING_PARTNER,
        "Buyer requested checkout preparation; no funds or animal reserved",
    )
    return intent, True


@transaction.atomic
def cancel_order_intent(*, intent_id, actor, reason):
    intent = OrderIntent.objects.select_for_update(of=("self",)).get(pk=intent_id)
    if not actor.is_active or not actor.is_email_verified:
        raise PermissionDenied("Active verified account required")
    if actor.pk not in (intent.buyer_id, intent.seller_id):
        raise PermissionDenied("Only a participant can cancel the request")
    if intent.status == OrderIntent.Status.CANCELLED:
        return intent, False
    if intent.status != OrderIntent.Status.AWAITING_PARTNER:
        raise ValidationError("Order request cannot be cancelled in this state")
    # This is only a request; cancellation cannot refund nonexistent funds.
    intent.status = OrderIntent.Status.CANCELLED
    intent.cancelled_at = timezone.now()
    intent.cancelled_by = actor
    intent.save(update_fields=("status", "cancelled_at", "cancelled_by"))
    _audit(
        intent, actor, OrderIntent.Status.AWAITING_PARTNER,
        OrderIntent.Status.CANCELLED, reason,
    )
    return intent, True
