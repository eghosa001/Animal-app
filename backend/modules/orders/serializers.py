"""Private snapshots deliberately omit addresses, bank details and payment claims."""
from rest_framework import serializers

from .models import OrderIntent


class OrderIntentCreateSerializer(serializers.Serializer):
    accepted_offer_id = serializers.UUIDField()
    request_nonce = serializers.UUIDField()
    no_payment_acknowledged = serializers.BooleanField(required=True)

    def validate_no_payment_acknowledged(self, value):
        if not value:
            raise serializers.ValidationError(
                "Confirm that no payment, escrow, reservation or delivery is provided"
            )
        return value


class OrderIntentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=20, max_length=240, trim_whitespace=True)


class OrderIntentReadSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.display_name", read_only=True)
    seller_name = serializers.CharField(source="seller.display_name", read_only=True)
    checkout_available = serializers.SerializerMethodField()
    funds_secured = serializers.SerializerMethodField()
    animal_reserved = serializers.SerializerMethodField()

    class Meta:
        model = OrderIntent
        fields = (
            "id", "accepted_offer", "listing", "animal_id_snapshot",
            "animal_name_snapshot", "listing_title_snapshot",
            "listing_region_snapshot", "buyer_name", "seller_name",
            "price_minor", "currency", "fulfillment_mode", "status",
            "checkout_available", "funds_secured", "animal_reserved",
            "created_at", "cancelled_at",
        )
        read_only_fields = fields

    def get_checkout_available(self, obj):
        return False

    def get_funds_secured(self, obj):
        return False

    def get_animal_reserved(self, obj):
        return False
