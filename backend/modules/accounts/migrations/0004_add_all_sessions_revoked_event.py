from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_password_resets_and_security_events")]

    operations = [
        migrations.AlterField(
            model_name="accountsecurityevent",
            name="event",
            field=models.CharField(
                choices=[
                    ("reset_issued", "Recovery challenge issued"),
                    ("reset_completed", "Password changed using recovery"),
                    ("verify_resent", "Verification code resent"),
                    ("all_revoked", "All account sessions revoked"),
                ],
                max_length=20,
            ),
        ),
    ]
