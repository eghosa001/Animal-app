import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0001_initial"),
        ("social", "0005_video_comments"),
    ]

    operations = [
        migrations.AddField(
            model_name="safetyreport",
            name="comment",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="safety_reports", to="social.videocomment",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="safetyreport",
            name="anima_safety_one_report_target",
        ),
        migrations.AddConstraint(
            model_name="safetyreport",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(video__isnull=False, listing__isnull=True, message__isnull=True, subject_user__isnull=True, comment__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=False, message__isnull=True, subject_user__isnull=True, comment__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=True, message__isnull=False, subject_user__isnull=True, comment__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=True, message__isnull=True, subject_user__isnull=False, comment__isnull=True)
                    | models.Q(video__isnull=True, listing__isnull=True, message__isnull=True, subject_user__isnull=True, comment__isnull=False)
                ),
                name="anima_safety_one_report_target",
            ),
        ),
    ]
