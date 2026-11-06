from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("animal_media", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="mediaasset",
            name="state",
            field=models.CharField(
                choices=[
                    ("pending", "Awaiting manual review"),
                    ("approved", "Approved for public listing"),
                    ("rejected", "Rejected"),
                    ("removed", "Removed by seller"),
                ],
                default="pending",
                max_length=12,
            ),
        ),
    ]
