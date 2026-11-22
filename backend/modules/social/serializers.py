"""Public feed schema exposes reviewed media only and never private seller data."""
from django.conf import settings
from rest_framework import serializers

from modules.accounts.models import SellerProfile
from modules.listings.models import Listing

from .models import VideoComment, VideoPost


class VideoPostSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source="creator.display_name", read_only=True)
    creator_id = serializers.UUIDField(read_only=True)
    playback_url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()
    listing = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = VideoPost
        fields = ("id", "creator_id", "creator_name", "caption", "playback_url", "poster_url", "listing", "likes_count", "comments_count", "is_liked", "created_at")
        read_only_fields = fields

    def get_likes_count(self, obj):
        return getattr(obj, "active_likes_count", 0)

    def get_comments_count(self, obj):
        return getattr(obj, "approved_comments_count", 0)

    def get_is_liked(self, obj):
        return bool(getattr(obj, "viewer_has_liked", False))

    def get_playback_url(self, obj):
        host = settings.VIDEO_DELIVERY_HOST
        return f"https://{host}/{obj.video_uid}/manifest/video.m3u8"

    def get_poster_url(self, obj):
        host = settings.VIDEO_DELIVERY_HOST
        return f"https://{host}/{obj.video_uid}/thumbnails/thumbnail.jpg"

    def get_listing(self, obj):
        listing = obj.listing
        if not listing:
            return None
        seller_profile = getattr(listing.seller, "seller_profile", None)
        if not (
            listing.status == Listing.Status.ACTIVE
            and listing.seller.is_active
            and seller_profile is not None
            and seller_profile.status == SellerProfile.Status.APPROVED
            and listing.animal.species.trade_enabled
        ):
            return None
        return {
            "id": str(listing.pk),
            "title": listing.title,
            "price_minor": listing.price_minor,
            "currency": listing.currency,
            "region": listing.region,
        }


class VideoCommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)
    client_nonce = serializers.UUIDField()

    def validate_body(self, body):
        if not any(char.isalnum() for char in body):
            raise serializers.ValidationError("Write a meaningful comment")
        return body


class VideoCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.display_name", read_only=True)
    author_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = VideoComment
        fields = ("id", "author_id", "author_name", "body", "created_at")
        read_only_fields = fields
