from rest_framework import serializers

from .models import MediaAsset


class ListingPhotoUploadSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    file = serializers.FileField(allow_empty_file=False)


class SellerEvidenceUploadSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False)
    evidence_type = serializers.ChoiceField(choices=MediaAsset.EvidenceType.choices)
    consent = serializers.BooleanField()


class MediaReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    reason = serializers.CharField(min_length=20, max_length=500)


class MediaAssetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = (
            "id", "kind", "listing", "evidence_type", "state",
            "content_type", "size_bytes", "width", "height", "uploaded_at", "file_url",
        )
        read_only_fields = fields

    def get_file_url(self, obj):
        from django.urls import reverse
        return reverse("media-file", kwargs={"asset_id": obj.pk})
