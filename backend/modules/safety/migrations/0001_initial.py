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
        ("social", "0003_moderation"),
        ("listings", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="UserBlock",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("blocker", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="blocked_accounts", to=settings.AUTH_USER_MODEL,
                )),
                ("blocked", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="blocked_by_accounts", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "indexes": [
                    models.Index(fields=("blocker", "created_at"), name="anima_safety_blocker_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("blocker", "blocked"), name="anima_safety_unique_block",
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(blocker=models.F("blocked")),
                        name="anima_safety_no_self_block",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="SafetyReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("category", models.CharField(
                    choices=[
                        ("scam", "Scam or off-platform payment pressure"),
                        ("harassment", "Harassment or threats"),
                        ("welfare", "Animal welfare concern"),
                        ("illegal_trade", "Prohibited animal or wildlife trade"),
                        ("copyright", "Unauthorized footage or copyright"),
                        ("other", "Other policy violation"),
                    ], max_length=20,
                )),
                ("detail", models.CharField(max_length=1500)),
                ("status", models.CharField(
                    choices=[
                        ("open", "Awaiting staff review"),
                        ("in_review", "Under staff investigation"),
                        ("actioned", "Action taken"),
                        ("dismissed", "Dismissed after review"),
                    ], default="open", max_length=10,
                )),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("listing", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_reports", to="listings.listing",
                )),
                ("message", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_reports", to="chats.chatmessage",
                )),
                ("video", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_reports", to="social.videopost",
                )),
                ("reporter", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="submitted_safety_reports", to=settings.AUTH_USER_MODEL,
                )),
                ("reviewed_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_reports_reviewed", to=settings.AUTH_USER_MODEL,
                )),
                ("subject_user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_reports_about", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at",),
                "permissions": (("review_safetyreport", "Can triage animal safety reports"),),
                "constraints": [
                    models.CheckConstraint(
                        condition=(
                            models.Q(video__isnull=False, listing__isnull=True,
                                     message__isnull=True, subject_user__isnull=True)
                            | models.Q(video__isnull=True, listing__isnull=False,
                                       message__isnull=True, subject_user__isnull=True)
                            | models.Q(video__isnull=True, listing__isnull=True,
                                       message__isnull=False, subject_user__isnull=True)
                            | models.Q(video__isnull=True, listing__isnull=True,
                                       message__isnull=True, subject_user__isnull=False)
                        ), name="anima_safety_one_report_target",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="SafetyReportReviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(max_length=10)),
                ("to_status", models.CharField(max_length=10)),
                ("reason", models.CharField(max_length=800)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("reviewer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="safety_review_actions", to=settings.AUTH_USER_MODEL,
                )),
                ("report", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="review_events", to="safety.safetyreport",
                )),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
