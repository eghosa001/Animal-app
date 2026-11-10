import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
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
            name="VideoPost",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("caption", models.CharField(max_length=400)),
                ("video_uid", models.CharField(
                    max_length=32, unique=True,
                    validators=[django.core.validators.RegexValidator(
                        "^[a-fA-F0-9]{32}$", "Invalid Stream video UID"
                    )],
                )),
                ("state", models.CharField(
                    choices=[
                        ("pending", "Pending review"),
                        ("approved", "Approved for public playback"),
                        ("rejected", "Rejected"),
                        ("removed", "Removed"),
                    ], default="pending", max_length=12,
                )),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("moderated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("creator", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="animal_videos", to=settings.AUTH_USER_MODEL,
                )),
                ("listing", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="linked_videos", to="listings.listing",
                )),
                ("moderated_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="moderated_animal_videos", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [models.Index(fields=("state", "-created_at"), name="anima_video_feed_idx")],
            },
        ),
    ]
