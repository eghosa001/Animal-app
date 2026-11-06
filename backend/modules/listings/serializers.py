"""Species-aware draft creation; only published listings appear publicly."""
from django.db import transaction
from rest_framework import serializers

from modules.catalog.models import Species
from modules.catalog.serializers import SpeciesSerializer

from .models import Animal, Listing


class ListingReadSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer(source="animal.species", read_only=True)
    animal_name = serializers.CharField(source="animal.name", read_only=True)
    breed_label = serializers.CharField(source="animal.breed_label", read_only=True)
    sex = serializers.CharField(source="animal.sex", read_only=True)
    estimated_age_months = serializers.IntegerField(source="animal.estimated_age_months", read_only=True)
    seller_name = serializers.CharField(source="seller.display_name", read_only=True)
    photo_urls = serializers.SerializerMethodField()

    def get_photo_urls(self, obj):
        from django.urls import reverse
        from modules.media.models import MediaAsset

        return [
            reverse("media-file", kwargs={"asset_id": asset.pk})
            for asset in obj.media_assets.filter(
                kind=MediaAsset.Kind.LISTING_PHOTO, state=MediaAsset.State.APPROVED,
            ).order_by("uploaded_at")[:8]
        ]


    class Meta:
        model = Listing
        fields = (
            "id", "title", "description", "price_minor", "currency", "region",
            "status", "species", "animal_name", "breed_label", "sex",
            "estimated_age_months", "seller_name", "created_at", "photo_urls",
        )
        read_only_fields = fields


class ListingCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=8, max_length=140)
    description = serializers.CharField(min_length=20, max_length=4000)
    price_minor = serializers.IntegerField(min_value=1, max_value=10_000_000_000_000)
    currency = serializers.ChoiceField(choices=("NGN",))
    region = serializers.CharField(min_length=2, max_length=140)
    species_id = serializers.PrimaryKeyRelatedField(queryset=Species.objects.all(), source="species")
    animal_name = serializers.CharField(min_length=2, max_length=120)
    breed_label = serializers.CharField(max_length=120, required=False, allow_blank=True)
    sex = serializers.ChoiceField(choices=Animal.Sex.choices, default=Animal.Sex.UNKNOWN)
    estimated_age_months = serializers.IntegerField(required=False, min_value=0, max_value=1200)

    @transaction.atomic
    def create(self, validated_data):
        seller = validated_data.pop("seller")
        species = validated_data.pop("species")
        animal = Animal.objects.create(
            owner=seller,
            species=species,
            name=validated_data.pop("animal_name"),
            breed_label=validated_data.pop("breed_label", ""),
            sex=validated_data.pop("sex", Animal.Sex.UNKNOWN),
            estimated_age_months=validated_data.pop("estimated_age_months", None),
        )
        return Listing.objects.create(seller=seller, animal=animal, **validated_data)
