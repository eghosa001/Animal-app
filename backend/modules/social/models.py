"""Moderated animal-only video metadata; no unreviewed upload becomes public."""
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class VideoPost(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending review"
        PUBLISHING = "publishing", "Approved by reviewer; activating playback"
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
    visibility_sync_needed = models.BooleanField(default=False)
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
        permissions = (("review_videopost", "Can moderate and publish animal videos"),)

    def __str__(self):
        return f"Video {self.id} ({self.state})"


class VideoReviewEvent(models.Model):
    """Append-only evidence of manual moderation and provider publication actions."""

    class Decision(models.TextChoices):
        APPROVE = "approve", "Approve after visual review"
        REJECT = "reject", "Reject content"
        REMOVE = "remove", "Remove published content"
        RETRY_SYNC = "retry_sync", "Retry publication or privacy sync"

    video = models.ForeignKey(
        VideoPost, on_delete=models.PROTECT, related_name="review_events"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="video_reviews_performed",
    )
    decision = models.CharField(max_length=12, choices=Decision.choices)
    previous_state = models.CharField(max_length=12)
    new_state = models.CharField(max_length=12)
    reason = models.CharField(max_length=800)
    visual_review_confirmed = models.BooleanField(default=False)
    policy_review_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.video_id}: {self.decision}"


class VideoLike(models.Model):
    """Private identity of a reaction; only aggregate counts leave the API."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(
        VideoPost, on_delete=models.PROTECT, related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="liked_animal_videos",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("video", "user"), name="anima_video_one_like_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "-created_at"), name="anima_video_likes_user_idx"),
        ]


class VideoComment(models.Model):
    """Untrusted user text remains private until an authorized staff review."""
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting review"
        APPROVED = "approved", "Published"
        REJECTED = "rejected", "Rejected"
        REMOVED = "removed", "Removed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(VideoPost, on_delete=models.PROTECT, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="animal_video_comments",
    )
    client_nonce = models.UUIDField()
    body = models.CharField(max_length=500)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="reviewed_video_comments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("author", "client_nonce"), name="anima_video_comment_nonce_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("video", "status", "-created_at"),
                name="anima_video_comments_feed_idx",
            ),
        ]
        permissions = (("review_videocomment", "Can moderate animal video comments"),)


class VideoCommentReviewEvent(models.Model):
    """Append-only record of manual comment publication or removal."""
    class Decision(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        REMOVE = "remove", "Remove"

    comment = models.ForeignKey(
        VideoComment, on_delete=models.PROTECT, related_name="review_events",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="comment_reviews_performed",
    )
    decision = models.CharField(max_length=12, choices=Decision.choices)
    previous_state = models.CharField(max_length=12)
    new_state = models.CharField(max_length=12)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
