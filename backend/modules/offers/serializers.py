"""Money is integer minor units, price/currency are server-authoritative."""
from django.utils import timezone
from rest_framework import serializers

from .models import AnimalOffer


class OfferReadSerializer(serializers.ModelSerializer):
    proposer_name = serializers.CharField(source="proposer.display_name", read_only=True)
    proposer_id = serializers.UUIDField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = AnimalOffer
        fields = (
            "id", "conversation", "proposer_id", "proposer_name",
            "amount_minor", "currency", "list_price_minor_at_creation",
            "status", "replaces", "created_at", "expires_at", "responded_at",
        )
        read_only_fields = fields

    def get_status(self, obj):
        if obj.status == AnimalOffer.Status.PENDING and obj.expires_at <= timezone.now():
            return AnimalOffer.Status.EXPIRED
        return obj.status


class OfferCreateSerializer(serializers.Serializer):
    amount_minor = serializers.IntegerField(min_value=1, max_value=10_000_000_000_000)
    client_nonce = serializers.UUIDField()


class OfferDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("accept", "decline"))
