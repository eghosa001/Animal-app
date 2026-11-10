import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("social", "0002_upload_tickets"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="videopost",
            options={
                "ordering": ("-created_at", "-id"),
                "permissions": ((
                    "review_videopost", "Can moderate and publish animal videos"
                ),),
                "indexes": [
                    models.Index(
                        fields=("state", "-created_at"), name="anima_video_feed_idx"
                    ),
                ],
            },
        ),
        migrations.AlterField(
            model_name="videopost", name="state",
            field=models.CharField(
                choices=[
                    ("pending", "Pending review"),
                    ("publishing", "Approved by reviewer; activating playback"),
                    ("approved", "Approved for public playback"),
                    ("rejected", "Rejected"),
                    ("removed", "Removed"),
                ],
                default="pending", max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="videopost", name="visibility_sync_needed",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="VideoReviewEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("decision", models.CharField(
                    choices=[
                        ("approve", "Approve after visual review"),
                        ("reject", "Reject content"),
                        ("remove", "Remove published content"),
                        ("retry_sync", "Retry publication or privacy sync"),
                    ],
                    max_length=12,
                )),
                ("previous_state", models.CharField(max_length=12)),
                ("new_state", models.CharField(max_length=12)),
                ("reason", models.CharField(max_length=800)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("reviewer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="video_reviews_performed", to=settings.AUTH_USER_MODEL,
                )),
                ("video", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="review_events", to="social.videopost",
                )),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
