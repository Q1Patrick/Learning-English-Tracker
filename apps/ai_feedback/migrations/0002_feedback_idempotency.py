from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_feedback", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="aifeedback",
            name="error_code",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="aifeedback",
            name="idempotency_key",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="aifeedback",
            name="request_fingerprint",
            field=models.CharField(blank=True, editable=False, max_length=64),
        ),
        migrations.AddConstraint(
            model_name="aifeedback",
            constraint=models.UniqueConstraint(
                fields=("user", "idempotency_key"), name="unique_ai_feedback_user_key"
            ),
        ),
    ]
