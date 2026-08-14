import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class StudySession(models.Model):
    class ActivityType(models.TextChoices):
        SPEAKING = "speaking", "Speaking"
        LISTENING = "listening", "Listening"
        READING = "reading", "Reading"
        WRITING = "writing", "Writing"
        VOCABULARY = "vocabulary", "Vocabulary"
        GRAMMAR = "grammar", "Grammar"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_sessions",
    )

    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
    )

    duration_minutes = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(720),
        ],
    )

    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    notes = models.TextField(blank=True)

    studied_at = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-studied_at"]

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.get_activity_type_display()} "
            f"({self.duration_minutes} min)"
        )