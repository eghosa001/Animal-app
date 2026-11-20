"""Non-financial order intentions; nothing here collects, reserves or holds funds."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class OrderIntent(models.Model):
    class Status(models.TextChoices):
        AWAITING_PARTNER = "awaiting_partner", "Awaiting authorized checkout partner"
        CANCELLED = "cancelled", "Cancelled before checkout"

    class FulfillmentMode(models.TextChoices):
        PICKUP = "pickup_planned", "Buyer pickup (not scheduled)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accepted_offer = models.OneToOneField(
        "offers.AnimalOffer", on_delete=models.PROTECT, related_name="order_intent",
    )
    listing = models.OneToOneField(
        "listings.Listing", on_delete=models.PROTECT, related_name="order_intent",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="buyer_order_intents",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="seller_order_intents",
    )
    request_nonce = models.UUIDField()
    animal_id_snapshot = models.UUIDField()
    animal_name_snapshot = models.CharField(max_length=120)
    listing_title_snapshot = models.CharField(max_length=140)
    listing_region_snapshot = models.CharField(max_length=140)
    price_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    fulfillment_mode = models.CharField(
        max_length=16, choices=FulfillmentMode.choices, default=FulfillmentMode.PICKUP,
    )
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.AWAITING_PARTNER,
    )
    created_at = models.DateTimeField(default=timezone.now)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="cancelled_order_intents",
    )

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("buyer", "request_nonce"), name="anima_order_nonce_per_buyer",
            ),
            models.CheckConstraint(
                condition=models.Q(price_minor__gt=0),
                name="anima_order_positive_snapshot",
            ),
        ]
        indexes = [
            models.Index(fields=("buyer", "-created_at"), name="anima_order_buyer_idx"),
            models.Index(fields=("seller", "-created_at"), name="anima_order_seller_idx"),
        ]


class OrderIntentEvent(models.Model):
    """Append-only events controlled by the service layer; never writable by clients."""
    order = models.ForeignKey(
        OrderIntent, on_delete=models.PROTECT, related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="order_intent_actions",
    )
    from_status = models.CharField(max_length=24, blank=True)
    to_status = models.CharField(max_length=24)
    reason = models.CharField(max_length=240)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
