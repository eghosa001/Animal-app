"""Listing-bound, participant-only conversations; immutable chat messages."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.PROTECT, related_name="conversations",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="buyer_conversations",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="seller_conversations",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-updated_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("listing", "buyer"), name="anima_chat_unique_listing_buyer",
            ),
            models.CheckConstraint(
                condition=~models.Q(buyer=models.F("seller")),
                name="anima_chat_distinct_participants",
            ),
        ]
        indexes = [
            models.Index(fields=("buyer", "-updated_at"), name="anima_chat_buyer_idx"),
            models.Index(fields=("seller", "-updated_at"), name="anima_chat_seller_idx"),
        ]

    def __str__(self):
        return f"Conversation {self.id}"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.PROTECT, related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="sent_chat_messages",
    )
    body = models.CharField(max_length=2000)
    client_nonce = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("conversation", "sender", "client_nonce"),
                name="anima_chat_message_nonce_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("conversation", "-created_at"), name="anima_chat_msg_recent_idx",
            ),
        ]

    def __str__(self):
        return f"Message {self.id}"
