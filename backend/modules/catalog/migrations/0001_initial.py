from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Species",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("category", models.CharField(choices=[("companion", "Companion animals"), ("farm", "Livestock and farm"), ("aquatic", "Aquatic animals"), ("bird", "Birds"), ("other", "Other permitted animals")], max_length=16)),
                ("trade_enabled", models.BooleanField(default=False, help_text="Enable only after applicable legal/welfare review.")),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "species"},
        ),
    ]
