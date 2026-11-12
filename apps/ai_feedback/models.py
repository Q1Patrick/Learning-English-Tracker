import uuid

from django.conf import settings
from django.db import models


class AIFeedback(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_feedbacks",
    )

    original_text = models.TextField()

    corrected_text = models.TextField(
        blank=True,
    )

    overall_feedback = models.TextField(
        blank=True,
    )

    grammar_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    vocabulary_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    clarity_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    mistakes = models.JSONField(
        default=list,
        blank=True,
    )

    suggestions = models.JSONField(
        default=list,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    # Safe metadata only; raw provider errors can contain user text or keys.
    error_code = models.CharField(max_length=64, blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True, editable=False)
    request_fingerprint = models.CharField(max_length=64, blank=True, editable=False)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                name="unique_ai_feedback_user_key",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.status}"
