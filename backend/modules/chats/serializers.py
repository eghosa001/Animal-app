"""Only conversation participants ever receive message or counterparty details."""
from rest_framework import serializers

from modules.accounts.models import SellerProfile
from modules.listings.models import Listing

from .models import ChatMessage, Conversation


def chat_is_writable(conversation):
    """Conversation history survives sales; new contact requires an eligible listing."""
    listing = conversation.listing
    seller_profile = getattr(conversation.seller, "seller_profile", None)
    return (
        listing.status == Listing.Status.ACTIVE
        and listing.animal.species.trade_enabled
        and conversation.buyer.is_active
        and conversation.seller.is_active
        and conversation.seller_id == listing.seller_id
        and seller_profile is not None
        and seller_profile.status == SellerProfile.Status.APPROVED
    )


class ConversationReadSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    counterparty_name = serializers.SerializerMethodField()
    can_send = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id", "listing", "listing_title", "counterparty_name",
            "can_send", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_counterparty_name(self, obj):
        user = self.context["request"].user
        return (
            obj.seller.display_name if user.pk == obj.buyer_id
            else obj.buyer.display_name
        )

    def get_can_send(self, obj):
        return chat_is_writable(obj)


class ConversationStartSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()


class ChatMessageReadSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.display_name", read_only=True)

    class Meta:
        model = ChatMessage
        fields = ("id", "sender", "sender_name", "body", "created_at", "client_nonce")
        read_only_fields = fields


class ChatMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)
    client_nonce = serializers.UUIDField()

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be blank")
        return value
