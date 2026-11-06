"""Seller review audit records and an explicit staff review permission."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sellerprofile",
            options={
                "permissions": [
                    ("review_sellerprofile", "Can decide seller review cases"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SellerReviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(
                    choices=[
                        ("approve", "Approve"), ("reject", "Reject"),
                        ("suspend", "Suspend"), ("reopen", "Reopen for review"),
                    ], max_length=12,
                )),
                ("previous_status", models.CharField(max_length=12)),
                ("new_status", models.CharField(max_length=12)),
                ("reason", models.TextField(max_length=2000)),
                ("evidence_case_reference", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="seller_reviews_performed", to=settings.AUTH_USER_MODEL,
                )),
                ("seller_profile", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="review_events", to="accounts.sellerprofile",
                )),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
