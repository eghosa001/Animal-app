"""Every upload is owner-bound, private and non-public until separately reviewed."""
import uuid

from django.conf import settings
from django.db import models


class MediaAsset(models.Model):
    class Kind(models.TextChoices):
        LISTING_PHOTO = "listing_photo", "Animal listing photograph"
        SELLER_EVIDENCE = "seller_evidence", "Seller verification evidence"

    class State(models.TextChoices):
        PENDING = "pending", "Awaiting manual review"
        APPROVED = "approved", "Approved for public listing"
        REJECTED = "rejected", "Rejected"

    class EvidenceType(models.TextChoices):
        IDENTITY = "identity", "Identity evidence"
        BUSINESS = "business", "Business registration"
        LICENSE = "license", "Animal trade/breeder licence"
        OTHER = "other", "Other verification evidence"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="private_media_assets")
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.PROTECT, null=True, blank=True, related_name="media_assets"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    evidence_type = models.CharField(max_length=12, choices=EvidenceType.choices, blank=True)
    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    # Generated entirely by the server; never constructed from the original filename.
    storage_key = models.CharField(max_length=150, unique=True)
    content_type = models.CharField(max_length=32, default="image/jpeg")
    size_bytes = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="media_reviews_performed"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("-uploaded_at",)
        permissions = (("review_mediaasset", "Can moderate and approve animal listing photos"),)
        indexes = (
            models.Index(fields=("owner", "kind", "uploaded_at"), name="anima_media_owner_kind_idx"),
        )

    def __str__(self):
        return f"{self.kind} {self.pk}"


class MediaAccessEvent(models.Model):
    """An append-only audit for accessing any private image, especially identity evidence."""

    asset = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name="access_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=24)
    accessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_id} {self.actor_id} {self.purpose}"


class MediaReviewEvent(models.Model):
    asset = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name="review_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=12)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_id}: {self.decision}"
