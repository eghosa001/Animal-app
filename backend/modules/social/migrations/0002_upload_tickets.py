from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("social", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="videopost", name="upload_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="videopost", name="rights_attested",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="videopost", name="animal_topic_attested",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="videopost", name="processing_error",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
    ]
