import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("offers", "0001_initial"),
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderIntent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("request_nonce", models.UUIDField()),
                ("animal_id_snapshot", models.UUIDField()),
                ("animal_name_snapshot", models.CharField(max_length=120)),
                ("listing_title_snapshot", models.CharField(max_length=140)),
                ("listing_region_snapshot", models.CharField(max_length=140)),
                ("price_minor", models.PositiveBigIntegerField()),
                ("currency", models.CharField(max_length=3)),
                ("fulfillment_mode", models.CharField(
                    choices=[("pickup_planned", "Buyer pickup (not scheduled)")],
                    default="pickup_planned", max_length=16,
                )),
                ("status", models.CharField(
                    choices=[
                        ("awaiting_partner", "Awaiting authorized checkout partner"),
                        ("cancelled", "Cancelled before checkout"),
                    ], default="awaiting_partner", max_length=24,
                )),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("accepted_offer", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="order_intent", to="offers.animaloffer",
                )),
                ("listing", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="order_intent", to="listings.listing",
                )),
                ("buyer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="buyer_order_intents", to=settings.AUTH_USER_MODEL,
                )),
                ("seller", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="seller_order_intents", to=settings.AUTH_USER_MODEL,
                )),
                ("cancelled_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="cancelled_order_intents", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(fields=("buyer", "-created_at"), name="anima_order_buyer_idx"),
                    models.Index(fields=("seller", "-created_at"), name="anima_order_seller_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("buyer", "request_nonce"), name="anima_order_nonce_per_buyer",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(price_minor__gt=0), name="anima_order_positive_snapshot",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="OrderIntentEvent",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                )),
                ("from_status", models.CharField(blank=True, max_length=24)),
                ("to_status", models.CharField(max_length=24)),
                ("reason", models.CharField(max_length=240)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="order_intent_actions", to=settings.AUTH_USER_MODEL,
                )),
                ("order", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="events", to="orders.orderintent",
                )),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
