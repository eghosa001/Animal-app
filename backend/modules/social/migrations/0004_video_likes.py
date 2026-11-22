import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("social", "0003_moderation"),
    ]

    operations = [
        migrations.CreateModel(
            name="VideoLike",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="liked_animal_videos", to=settings.AUTH_USER_MODEL,
                )),
                ("video", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="likes", to="social.videopost",
                )),
            ],
            options={
                "indexes": [
                    models.Index(fields=("user", "-created_at"),
                                 name="anima_video_likes_user_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("video", "user"),
                        name="anima_video_one_like_per_user",
                    ),
                ],
            },
        ),
    ]
