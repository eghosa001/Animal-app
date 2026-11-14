"""Row-locked offer negotiations, no checkout or payment state changes."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from modules.chats.models import Conversation
from modules.chats.serializers import chat_is_writable
from modules.listings.models import Listing

from .models import AnimalOffer, AnimalOfferEvent


def _lock_conversation(conversation_id):
    return Conversation.objects.select_for_update(of=("self",)).select_related(
        "buyer", "seller", "seller__seller_profile",
        "listing", "listing__animal__species",
    ).get(pk=conversation_id)


def _require_actor(conversation, actor):
    if not actor.is_authenticated or not actor.is_active or not actor.is_email_verified:
        raise PermissionDenied("Verify your active account before making an offer")
    if actor.pk not in (conversation.buyer_id, conversation.seller_id):
        raise PermissionDenied("Only participants can negotiate this animal")


def _require_available(conversation):
    if not chat_is_writable(conversation):
        raise PermissionDenied("This animal is not available for negotiation")


def _event(offer, actor, previous, status, reason):
    return AnimalOfferEvent.objects.create(
        offer=offer, actor=actor, from_status=previous,
        to_status=status, reason=reason,
    )


def _expire_pending(conversation, actor):
    now = timezone.now()
    for current in AnimalOffer.objects.filter(
        conversation=conversation, status=AnimalOffer.Status.PENDING,
        expires_at__lte=now,
    ):
        current.status = AnimalOffer.Status.EXPIRED
        current.responded_at = now
        current.save(update_fields=("status", "responded_at"))
        _event(current, actor, AnimalOffer.Status.PENDING,
               AnimalOffer.Status.EXPIRED, "Offer expired before action")


@transaction.atomic
def propose_offer(*, conversation_id, actor, amount_minor, client_nonce):
    conversation = _lock_conversation(conversation_id)
    _require_actor(conversation, actor)

    duplicate = AnimalOffer.objects.filter(
        conversation=conversation, proposer=actor, client_nonce=client_nonce,
    ).first()
    if duplicate is not None:
        if duplicate.amount_minor != amount_minor:
            raise ValidationError({"client_nonce": "This idempotency ID was used with a different price"})
        return duplicate, False

    _require_available(conversation)
    listing = conversation.listing
    if amount_minor > listing.price_minor:
        raise ValidationError({"amount_minor": "Offers cannot exceed the current listed price"})
    if AnimalOffer.objects.filter(
        conversation__listing=listing, status=AnimalOffer.Status.ACCEPTED,
    ).exists():
        raise ValidationError("An offer has already been accepted for this animal")

    _expire_pending(conversation, actor)
    previous = AnimalOffer.objects.filter(
        conversation=conversation, status=AnimalOffer.Status.PENDING,
    ).first()
    if previous is not None and previous.proposer_id == actor.pk:
        raise ValidationError("Wait for the counterparty to respond or the quote to expire")
    if previous is not None:
        previous.status = AnimalOffer.Status.SUPERSEDED
        previous.responded_at = timezone.now()
        previous.save(update_fields=("status", "responded_at"))
        _event(previous, actor, AnimalOffer.Status.PENDING,
               AnimalOffer.Status.SUPERSEDED, "Counterparty submitted a counterproposal")
    offer = AnimalOffer.objects.create(
        conversation=conversation, proposer=actor, client_nonce=client_nonce,
        amount_minor=amount_minor, currency=listing.currency,
        list_price_minor_at_creation=listing.price_minor,
        replaces=previous,
        expires_at=timezone.now() + timedelta(hours=72),
    )
    _event(offer, actor, "", AnimalOffer.Status.PENDING, "New price proposal")
    return offer, True


@transaction.atomic
def decide_offer(*, offer_id, actor, decision):
    # Resolve the offer ID without disclosing its details to unauthorized users.
    target = AnimalOffer.objects.select_related("conversation").get(pk=offer_id)
    conversation = _lock_conversation(target.conversation_id)
    _require_actor(conversation, actor)
    offer = AnimalOffer.objects.select_for_update(of=("self",)).get(pk=offer_id)
    if offer.proposer_id == actor.pk:
        raise PermissionDenied("You cannot accept or decline your own offer")
    if offer.status == AnimalOffer.Status.ACCEPTED and decision == "accept":
        return offer
    if offer.status != AnimalOffer.Status.PENDING:
        raise ValidationError("This offer is no longer pending")
    if offer.expires_at <= timezone.now():
        # The read serializer already displays the effective expired state;
        # a later offer will record the expiry in a separate committed
        # transaction. Raising here must not pretend a rolled-back state saved.
        raise ValidationError("This offer has expired")

    _require_available(conversation)
    if decision == "accept":
        # All acceptances for an individual animal serialize on the listing row,
        # even across different buyers' independent conversations.
        listing = Listing.objects.select_for_update(of=("self",)).get(
            pk=conversation.listing_id,
        )
        if listing.status != Listing.Status.ACTIVE:
            raise PermissionDenied("The animal listing is no longer available")
        if AnimalOffer.objects.filter(
            conversation__listing=listing, status=AnimalOffer.Status.ACCEPTED,
        ).exclude(pk=offer.pk).exists():
            raise ValidationError("Another price agreement exists for this animal")
        if offer.amount_minor > listing.price_minor:
            raise ValidationError("Listing price has changed; request a new proposal")
        new_status = AnimalOffer.Status.ACCEPTED
    elif decision == "decline":
        new_status = AnimalOffer.Status.DECLINED
    else:
        raise ValidationError({"decision": "Invalid offer decision"})
    previous = offer.status
    offer.status = new_status
    offer.responded_at = timezone.now()
    offer.save(update_fields=("status", "responded_at"))
    _event(
        offer, actor, previous, new_status,
        "Agreed to a price quote; no payment collected" if decision == "accept"
        else "Counterparty declined the price proposal",
    )
    return offer
