"""Moderated animal-only video metadata; no unreviewed upload becomes public."""
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class VideoPost(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved for public playback"
        REJECTED = "rejected", "Rejected"
        REMOVED = "removed", "Removed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="animal_videos"
    )
    caption = models.CharField(max_length=400)
    # Issued by Cloudflare Stream to the backend; never selected by the client.
    # A signed provider webhook confirms processing, not publication.
    video_uid = models.CharField(
        max_length=32, unique=True,
        validators=[RegexValidator(r"^[a-fA-F0-9]{32}$", "Invalid Stream video UID")],
    )
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.PROTECT,
        related_name="linked_videos", null=True, blank=True,
    )
    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    upload_expires_at = models.DateTimeField(null=True, blank=True)
    rights_attested = models.BooleanField(default=False)
    animal_topic_attested = models.BooleanField(default=False)
    processing_error = models.CharField(max_length=80, blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="moderated_animal_videos",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = (models.Index(fields=("state", "-created_at"), name="anima_video_feed_idx"),)

    def __str__(self):
        return f"Video {self.id} ({self.state})"
