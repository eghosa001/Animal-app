import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnimalOffer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                         primary_key=True, serialize=False)),
                ("client_nonce", models.UUIDField()),
                ("amount_minor", models.PositiveBigIntegerField()),
                ("currency", models.CharField(max_length=3)),
                ("list_price_minor_at_creation", models.PositiveBigIntegerField()),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Awaiting counterparty"),
                        ("accepted", "Price agreed; checkout unavailable"),
                        ("declined", "Declined by counterparty"),
                        ("superseded", "Replaced by a counterproposal"),
                        ("expired", "Expired without acceptance"),
                    ],
                    default="pending", max_length=12,
                )),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("conversation", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="offers", to="chats.conversation",
                )),
                ("proposer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="animal_offers_proposed", to=settings.AUTH_USER_MODEL,
                )),
                ("replaces", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="counters", to="offers.animaloffer",
                )),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(fields=("conversation", "-created_at"),
                                 name="anima_offer_history_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("conversation", "proposer", "client_nonce"),
                        name="anima_offer_idempotency",
                    ),
                    models.UniqueConstraint(
                        fields=("conversation",), condition=models.Q(status="pending"),
                        name="anima_offer_one_pending_per_chat",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(amount_minor__gt=0),
                        name="anima_offer_amount_positive",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AnimalOfferEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(blank=True, max_length=12)),
                ("to_status", models.CharField(max_length=12)),
                ("reason", models.CharField(max_length=180)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="animal_offer_actions", to=settings.AUTH_USER_MODEL,
                )),
                ("offer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="events", to="offers.animaloffer",
                )),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
