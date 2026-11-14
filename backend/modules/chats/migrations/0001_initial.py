import uuid

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
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("buyer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="buyer_conversations", to=settings.AUTH_USER_MODEL,
                )),
                ("seller", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="seller_conversations", to=settings.AUTH_USER_MODEL,
                )),
                ("listing", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="conversations", to="listings.listing",
                )),
            ],
            options={
                "ordering": ("-updated_at", "-id"),
                "indexes": [
                    models.Index(fields=("buyer", "-updated_at"), name="anima_chat_buyer_idx"),
                    models.Index(fields=("seller", "-updated_at"), name="anima_chat_seller_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("listing", "buyer"), name="anima_chat_unique_listing_buyer",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(buyer=models.F("seller")),
                        name="anima_chat_distinct_participants",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body", models.CharField(max_length=2000)),
                ("client_nonce", models.UUIDField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("conversation", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="messages", to="chats.conversation",
                )),
                ("sender", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="sent_chat_messages", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=("conversation", "-created_at"),
                        name="anima_chat_msg_recent_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("conversation", "sender", "client_nonce"),
                        name="anima_chat_message_nonce_unique",
                    ),
                ],
            },
        ),
    ]
