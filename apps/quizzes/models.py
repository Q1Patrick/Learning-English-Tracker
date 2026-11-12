"""Quiz content and immutable snapshots of submitted answers."""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        VOCABULARY = "vocabulary", "Vocabulary"
        GRAMMAR = "grammar", "Grammar"
        TRANSLATION = "translation", "Translation"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    text = models.TextField()

    question_type = models.CharField(
        max_length=30,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
    )

    explanation = models.TextField(
        blank=True,
    )

    order = models.PositiveSmallIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.text


class Choice(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.CharField(
        max_length=255,
    )

    is_correct = models.BooleanField(
        default=False,
    )

    order = models.PositiveSmallIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
    )

    # Historical snapshots survive edits/deletion of source quiz content.
    quiz_id_snapshot = models.UUIDField(null=True, editable=False)
    quiz_title_snapshot = models.CharField(max_length=200, editable=False)
    idempotency_key = models.UUIDField(null=True, blank=True, editable=False)
    request_fingerprint = models.CharField(max_length=64, blank=True, editable=False)

    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    correct_answers = models.PositiveSmallIntegerField(
        default=0,
    )

    total_questions = models.PositiveSmallIntegerField(
        default=0,
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-completed_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-completed_at", "-id"], name="quiz_user_completed_idx"),
            models.Index(fields=["-completed_at", "-id"], name="quiz_completed_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(score__gte=0, score__lte=100),
                name="quiz_attempt_score_0_100",
            ),
            models.CheckConstraint(
                check=models.Q(correct_answers__lte=models.F("total_questions")),
                name="quiz_attempt_correct_lte_total",
            ),
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                name="quiz_attempt_user_idem_unique",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.quiz_title_snapshot} - {self.score}%"


class QuizAttemptAnswer(models.Model):
    """Snapshots are the source of truth after a submission is scored."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_answers",
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_answers",
    )
    question_id_snapshot = models.UUIDField(editable=False)
    choice_id_snapshot = models.UUIDField(editable=False)
    correct_choice_id_snapshot = models.UUIDField(editable=False)
    question_text = models.TextField(editable=False)
    choice_text = models.TextField(editable=False)
    correct_choice_text = models.TextField(editable=False)
    explanation = models.TextField(blank=True, editable=False)
    is_correct = models.BooleanField(editable=False)
    order = models.PositiveSmallIntegerField(editable=False)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question_id_snapshot"],
                name="quiz_answer_attempt_question_unique",
            ),
        ]

    def __str__(self):
        return f"{self.attempt_id}: {self.question_id_snapshot}"
