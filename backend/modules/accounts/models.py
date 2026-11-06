"""Custom email-first accounts and deliberately manual seller approval."""
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        email = self.normalize_email(email).lower().strip()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser requires staff and superuser permissions")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=254)
    display_name = models.CharField(max_length=100)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]
    objects = UserManager()

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    def __str__(self):
        return self.email


class EmailVerificationChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_challenges")
    token_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SellerProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="seller_profile")
    business_name = models.CharField(max_length=140)
    adult_attested = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [
            ("review_sellerprofile", "Can decide seller review cases"),
        ]

    def __str__(self):
        return f"{self.business_name} ({self.status})"


class SellerReviewEvent(models.Model):
    """Append-only record of why a seller's privilege changed."""

    class Decision(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        SUSPEND = "suspend", "Suspend"
        REOPEN = "reopen", "Reopen for review"

    seller_profile = models.ForeignKey(
        SellerProfile, on_delete=models.PROTECT, related_name="review_events"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="seller_reviews_performed"
    )
    decision = models.CharField(max_length=12, choices=Decision.choices)
    previous_status = models.CharField(max_length=12)
    new_status = models.CharField(max_length=12)
    reason = models.TextField(max_length=2000)
    # References an approved OFFLINE or future third-party review case.
    # Never put raw identity numbers, photos or sensitive documents here.
    evidence_case_reference = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Seller {self.seller_profile_id}: {self.decision}"
