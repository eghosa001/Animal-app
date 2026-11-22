import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0004_video_likes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VideoComment",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False, serialize=False)),
                ("client_nonce", models.UUIDField()),
                ("body", models.CharField(max_length=500)),
                ("status", models.CharField(max_length=12, default="pending",
                    choices=[("pending", "Awaiting review"),
                             ("approved", "Published"),
                             ("rejected", "Rejected"),
                             ("removed", "Removed")])),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("moderated_at", models.DateTimeField(blank=True, null=True)),
                ("author", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="animal_video_comments", to=settings.AUTH_USER_MODEL)),
                ("moderated_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="reviewed_video_comments", to=settings.AUTH_USER_MODEL)),
                ("video", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="comments", to="social.videopost")),
            ],
            options={
                "indexes": [models.Index(
                    fields=("video", "status", "-created_at"),
                    name="anima_video_comments_feed_idx")],
                "constraints": [models.UniqueConstraint(
                    fields=("author", "client_nonce"),
                    name="anima_video_comment_nonce_unique")],
                "permissions": (("review_videocomment", "Can moderate animal video comments"),),
            },
        ),
        migrations.CreateModel(
            name="VideoCommentReviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                            serialize=False, verbose_name="ID")),
                ("decision", models.CharField(max_length=12, choices=[
                    ("approve", "Approve"), ("reject", "Reject"), ("remove", "Remove")])),
                ("previous_state", models.CharField(max_length=12)),
                ("new_state", models.CharField(max_length=12)),
                ("reason", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("comment", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="review_events", to="social.videocomment")),
                ("reviewer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="comment_reviews_performed", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
