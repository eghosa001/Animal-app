"""Negotiated price quotes only; acceptance does not move or protect funds."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AnimalOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting counterparty"
        ACCEPTED = "accepted", "Price agreed; checkout unavailable"
        DECLINED = "declined", "Declined by counterparty"
        SUPERSEDED = "superseded", "Replaced by a counterproposal"
        EXPIRED = "expired", "Expired without acceptance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        "chats.Conversation", on_delete=models.PROTECT, related_name="offers",
    )
    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="animal_offers_proposed",
    )
    client_nonce = models.UUIDField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    list_price_minor_at_creation = models.PositiveBigIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    replaces = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="counters",
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("conversation", "proposer", "client_nonce"),
                name="anima_offer_idempotency",
            ),
            models.UniqueConstraint(
                fields=("conversation",),
                condition=models.Q(status="pending"),
                name="anima_offer_one_pending_per_chat",
            ),
            models.CheckConstraint(
                condition=models.Q(amount_minor__gt=0),
                name="anima_offer_amount_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=("conversation", "-created_at"),
                name="anima_offer_history_idx",
            ),
        ]

    def __str__(self):
        return f"Offer {self.id} ({self.status})"


class AnimalOfferEvent(models.Model):
    """Immutable audit of every proposal, counter and final decision."""

    offer = models.ForeignKey(
        AnimalOffer, on_delete=models.PROTECT, related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="animal_offer_actions",
    )
    from_status = models.CharField(max_length=12, blank=True)
    to_status = models.CharField(max_length=12)
    reason = models.CharField(max_length=180)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
