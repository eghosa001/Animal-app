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
    estimated_age_months = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1200)

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

    @transaction.atomic
    def update(self, instance, validated_data):
        from rest_framework.exceptions import PermissionDenied, ValidationError

        from modules.accounts.models import SellerProfile
        from modules.media.models import MediaAsset, MediaReviewEvent

        actor = self.context["request"].user
        if not actor.is_active or not actor.is_email_verified:
            raise PermissionDenied("An active verified account is required")
        seller_profile = getattr(actor, "seller_profile", None)
        if seller_profile is None or seller_profile.status not in (
            SellerProfile.Status.PENDING, SellerProfile.Status.APPROVED
        ):
            raise PermissionDenied("An eligible seller application is required")

        listing = Listing.objects.select_for_update().select_related("animal").get(
            pk=instance.pk, seller=actor
        )
        if listing.status != Listing.Status.DRAFT:
            raise ValidationError({"status": ["Only draft listings can be edited"]})
        animal = listing.animal
        new_species = validated_data.pop("species", animal.species)
        # A newly selected species could make already-reviewed photos misleading.
        # Require selecting the correct species before starting the photo gallery.
        if new_species.pk != animal.species_id and MediaAsset.objects.filter(
            listing=listing, kind=MediaAsset.Kind.LISTING_PHOTO,
        ).exclude(state=MediaAsset.State.REMOVED).exists():
            raise ValidationError({
                "species_id": ["Remove or resolve existing photos before changing animal species"]
            })

        animal_fields = {
            "species": new_species,
            "name": validated_data.pop("animal_name", animal.name),
            "breed_label": validated_data.pop("breed_label", animal.breed_label),
            "sex": validated_data.pop("sex", animal.sex),
            "estimated_age_months": validated_data.pop("estimated_age_months", animal.estimated_age_months),
        }
        # Changing the advertised animal identity invalidates any earlier
        # photo approval; the moderator must inspect the image again.
        identity_changed = any(
            getattr(animal, field) != value
            for field, value in animal_fields.items()
        )
        for field, value in animal_fields.items():
            setattr(animal, field, value)
        animal.save(update_fields=list(animal_fields))

        if identity_changed:
            approved_photos = list(
                MediaAsset.objects.select_for_update(of=("self",)).filter(
                    listing=listing, kind=MediaAsset.Kind.LISTING_PHOTO,
                    state=MediaAsset.State.APPROVED,
                )
            )
            for photo in approved_photos:
                photo.state = MediaAsset.State.PENDING
                photo.reviewed_by = None
                photo.reviewed_at = None
                photo.review_note = ""
                photo.save(update_fields=(
                    "state", "reviewed_by", "reviewed_at", "review_note"
                ))
                MediaReviewEvent.objects.create(
                    asset=photo, actor=actor,
                    decision="invalidate",
                    reason="Animal identifying details changed in a private draft",
                )

        allowed_listing_fields = ("title", "description", "price_minor", "currency", "region")
        changed = []
        for field in allowed_listing_fields:
            if field in validated_data:
                setattr(listing, field, validated_data[field])
                changed.append(field)
        if changed:
            listing.save(update_fields=changed)
        return listing

