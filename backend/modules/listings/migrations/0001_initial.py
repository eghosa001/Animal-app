import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Animal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("breed_label", models.CharField(blank=True, max_length=120)),
                ("sex", models.CharField(choices=[("male", "Male"), ("female", "Female"), ("unknown", "Unknown")], default="unknown", max_length=8)),
                ("estimated_age_months", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="animals", to=settings.AUTH_USER_MODEL)),
                ("species", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="animals", to="catalog.species")),
            ],
        ),
        migrations.CreateModel(
            name="Listing",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=140)),
                ("description", models.TextField(max_length=4000)),
                ("price_minor", models.PositiveBigIntegerField()),
                ("currency", models.CharField(default="NGN", max_length=3)),
                ("region", models.CharField(max_length=140)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending moderator review"), ("active", "Active"), ("sold", "Sold"), ("removed", "Removed")], default="draft", max_length=12)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("animal", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="listing", to="listings.animal")),
                ("seller", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ListingEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(max_length=12)),
                ("to_status", models.CharField(max_length=12)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events", to="listings.listing")),
            ],
        ),
        migrations.AddConstraint(
            model_name="listing",
            constraint=models.CheckConstraint(condition=models.Q(price_minor__gt=0), name="anima_listing_positive_price"),
        ),
    ]
