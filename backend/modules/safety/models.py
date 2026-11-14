"""Owner-only blocks, evidence-safe reports and append-only staff decisions."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="blocked_accounts",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="blocked_by_accounts",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("blocker", "blocked"), name="anima_safety_unique_block",
            ),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="anima_safety_no_self_block",
            ),
        ]
        indexes = [
            models.Index(
                fields=("blocker", "created_at"), name="anima_safety_blocker_idx",
            ),
        ]


class SafetyReport(models.Model):
    class Category(models.TextChoices):
        SCAM = "scam", "Scam or off-platform payment pressure"
        HARASSMENT = "harassment", "Harassment or threats"
        WELFARE = "welfare", "Animal welfare concern"
        ILLEGAL_TRADE = "illegal_trade", "Prohibited animal or wildlife trade"
        COPYRIGHT = "copyright", "Unauthorized footage or copyright"
        OTHER = "other", "Other policy violation"

    class Status(models.TextChoices):
        OPEN = "open", "Awaiting staff review"
        IN_REVIEW = "in_review", "Under staff investigation"
        ACTIONED = "actioned", "Action taken"
        DISMISSED = "dismissed", "Dismissed after review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="submitted_safety_reports",
    )
    video = models.ForeignKey(
        "social.VideoPost", on_delete=models.PROTECT,
        null=True, blank=True, related_name="safety_reports",
    )
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.PROTECT,
        null=True, blank=True, related_name="safety_reports",
    )
    message = models.ForeignKey(
        "chats.ChatMessage", on_delete=models.PROTECT,
        null=True, blank=True, related_name="safety_reports",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="safety_reports_about",
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    detail = models.CharField(max_length=1500)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="safety_reports_reviewed",
    )

    class Meta:
        ordering = ("-created_at",)
        permissions = (("review_safetyreport", "Can triage animal safety reports"),)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(video__isnull=False, listing__isnull=True,
                             message__isnull=True, subject_user__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=False,
                               message__isnull=True, subject_user__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=True,
                               message__isnull=False, subject_user__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=True,
                               message__isnull=True, subject_user__isnull=False)
                ),
                name="anima_safety_one_report_target",
            ),
        ]


class SafetyReportReviewEvent(models.Model):
    """Human decision record; clients cannot create or update it."""

    report = models.ForeignKey(
        SafetyReport, on_delete=models.PROTECT, related_name="review_events",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="safety_review_actions",
    )
    from_status = models.CharField(max_length=10)
    to_status = models.CharField(max_length=10)
    reason = models.CharField(max_length=800)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
