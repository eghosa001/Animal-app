"""Animal and listing are different entities: a sold animal retains its record."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.catalog.models import Species


class Animal(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        UNKNOWN = "unknown", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="animals")
    species = models.ForeignKey(Species, on_delete=models.PROTECT, related_name="animals")
    name = models.CharField(max_length=120)
    breed_label = models.CharField(max_length=120, blank=True)
    sex = models.CharField(max_length=8, choices=Sex.choices, default=Sex.UNKNOWN)
    estimated_age_months = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Listing(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending moderator review"
        ACTIVE = "active", "Active"
        SOLD = "sold", "Sold"
        REMOVED = "removed", "Removed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    animal = models.OneToOneField(Animal, on_delete=models.PROTECT, related_name="listing")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=140)
    description = models.TextField(max_length=4000)
    price_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="NGN")
    region = models.CharField(max_length=140)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price_minor__gt=0), name="anima_listing_positive_price"),
        ]

    def __str__(self):
        return self.title


class ListingEvent(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_status = models.CharField(max_length=12)
    to_status = models.CharField(max_length=12)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
