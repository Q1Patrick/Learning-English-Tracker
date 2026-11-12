"""Preserve legacy attempt history and reject invalid data before constraints."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


def validate_existing_attempts(apps, schema_editor):
    Attempt = apps.get_model("quizzes", "QuizAttempt")
    invalid = Attempt.objects.using(schema_editor.connection.alias).filter(
        models.Q(score__gt=100)
        | models.Q(correct_answers__gt=models.F("total_questions"))
    )
    invalid_count = invalid.count()
    if invalid_count:
        ids = ", ".join(str(pk) for pk in invalid.values_list("pk", flat=True)[:20])
        raise RuntimeError(
            f"Cannot migrate quiz history: {invalid_count} invalid QuizAttempt row(s). "
            f"IDs (first 20): {ids}. Correct scores to 0-100 and ensure "
            "correct_answers <= total_questions, then rerun migrate. "
            "No records have been deleted."
        )


def snapshot_legacy_quizzes(apps, schema_editor):
    Attempt = apps.get_model("quizzes", "QuizAttempt")
    db_alias = schema_editor.connection.alias
    batch = []
    for attempt in Attempt.objects.using(db_alias).select_related("quiz").iterator():
        attempt.quiz_id_snapshot = attempt.quiz_id
        attempt.quiz_title_snapshot = attempt.quiz.title if attempt.quiz_id else ""
        batch.append(attempt)
        if len(batch) == 1000:
            Attempt.objects.using(db_alias).bulk_update(
                batch, ["quiz_id_snapshot", "quiz_title_snapshot"]
            )
            batch = []
    if batch:
        Attempt.objects.using(db_alias).bulk_update(
            batch, ["quiz_id_snapshot", "quiz_title_snapshot"]
        )


class Migration(migrations.Migration):
    dependencies = [("quizzes", "0004_quizattempt")]

    operations = [
        migrations.RunPython(validate_existing_attempts, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="quizattempt", options={"ordering": ["-completed_at", "-id"]}
        ),
        migrations.AlterField(
            model_name="quizattempt", name="quiz",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="attempts", to="quizzes.quiz",
            ),
        ),
        migrations.AddField(
            model_name="quizattempt", name="quiz_id_snapshot",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="quizattempt", name="quiz_title_snapshot",
            field=models.CharField(default="", editable=False, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="quizattempt", name="idempotency_key",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="quizattempt", name="request_fingerprint",
            field=models.CharField(blank=True, default="", editable=False, max_length=64),
            preserve_default=False,
        ),
        migrations.RunPython(snapshot_legacy_quizzes, migrations.RunPython.noop),
        migrations.CreateModel(
            name="QuizAttemptAnswer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("question_id_snapshot", models.UUIDField(editable=False)),
                ("choice_id_snapshot", models.UUIDField(editable=False)),
                ("correct_choice_id_snapshot", models.UUIDField(editable=False)),
                ("question_text", models.TextField(editable=False)),
                ("choice_text", models.TextField(editable=False)),
                ("correct_choice_text", models.TextField(editable=False)),
                ("explanation", models.TextField(blank=True, editable=False)),
                ("is_correct", models.BooleanField(editable=False)),
                ("order", models.PositiveSmallIntegerField(editable=False)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="quizzes.quizattempt")),
                ("question", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submitted_answers", to="quizzes.question")),
                ("choice", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submitted_answers", to="quizzes.choice")),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="quizattempt",
            constraint=models.CheckConstraint(
                check=models.Q(score__gte=0, score__lte=100), name="quiz_attempt_score_0_100"
            ),
        ),
        migrations.AddConstraint(
            model_name="quizattempt",
            constraint=models.CheckConstraint(
                check=models.Q(correct_answers__lte=models.F("total_questions")),
                name="quiz_attempt_correct_lte_total",
            ),
        ),
        migrations.AddConstraint(
            model_name="quizattempt",
            constraint=models.UniqueConstraint(
                fields=("user", "idempotency_key"), name="quiz_attempt_user_idem_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="quizattemptanswer",
            constraint=models.UniqueConstraint(
                fields=("attempt", "question_id_snapshot"),
                name="quiz_answer_attempt_question_unique",
            ),
        ),
    ]
