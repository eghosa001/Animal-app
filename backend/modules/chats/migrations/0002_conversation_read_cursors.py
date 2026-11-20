import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chats", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="buyer_last_read_message",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="buyer_read_by_conversations",
                to="chats.chatmessage",
            ),
        ),
        migrations.AddField(
            model_name="conversation",
            name="seller_last_read_message",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="seller_read_by_conversations",
                to="chats.chatmessage",
            ),
        ),
    ]
