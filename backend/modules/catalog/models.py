"""Species policy is disabled for commerce until reviewed by operations."""
from django.db import models


class Species(models.Model):
    class Category(models.TextChoices):
        COMPANION = "companion", "Companion animals"
        FARM = "farm", "Livestock and farm"
        AQUATIC = "aquatic", "Aquatic animals"
        BIRD = "bird", "Birds"
        OTHER = "other", "Other permitted animals"

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    trade_enabled = models.BooleanField(
        default=False, help_text="Enable only after applicable legal/welfare review."
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "species"

    def __str__(self):
        return self.name
