import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(
                    choices=[("listing_photo", "Animal listing photograph"), ("seller_evidence", "Seller verification evidence")],
                    max_length=20,
                )),
                ("evidence_type", models.CharField(
                    blank=True,
                    choices=[
                        ("identity", "Identity evidence"), ("business", "Business registration"),
                        ("license", "Animal trade/breeder licence"), ("other", "Other verification evidence"),
                    ], max_length=12,
                )),
                ("state", models.CharField(
                    choices=[("pending", "Awaiting manual review"), ("approved", "Approved for public listing"), ("rejected", "Rejected")],
                    default="pending", max_length=12,
                )),
                ("storage_key", models.CharField(max_length=150, unique=True)),
                ("content_type", models.CharField(default="image/jpeg", max_length=32)),
                ("size_bytes", models.PositiveIntegerField()),
                ("width", models.PositiveIntegerField()),
                ("height", models.PositiveIntegerField()),
                ("sha256", models.CharField(max_length=64)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_note", models.CharField(blank=True, max_length=500)),
                ("listing", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="media_assets", to="listings.listing",
                )),
                ("owner", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="private_media_assets",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("reviewed_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="media_reviews_performed", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-uploaded_at",),
                "permissions": (("review_mediaasset", "Can moderate and approve animal listing photos"),),
                "indexes": [
                    models.Index(fields=("owner", "kind", "uploaded_at"), name="anima_media_owner_kind_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MediaAccessEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purpose", models.CharField(max_length=24)),
                ("accessed_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="access_events", to="animal_media.mediaasset")),
            ],
        ),
        migrations.CreateModel(
            name="MediaReviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(max_length=12)),
                ("reason", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_events", to="animal_media.mediaasset")),
            ],
        ),
    ]
