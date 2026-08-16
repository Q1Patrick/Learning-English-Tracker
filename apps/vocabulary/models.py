import uuid

from django.conf import settings
from django.db import models


class Vocabulary(models.Model):
    class PartOfSpeech(models.TextChoices):
        NOUN = "noun", "Noun"
        VERB = "verb", "Verb"
        ADJECTIVE = "adjective", "Adjective"
        ADVERB = "adverb", "Adverb"
        PHRASE = "phrase", "Phrase"
        PHRASAL_VERB = "phrasal_verb", "Phrasal Verb"
        OTHER = "other", "Other"

    class MasteryLevel(models.TextChoices):
        NEW = "new", "New"
        LEARNING = "learning", "Learning"
        FAMILIAR = "familiar", "Familiar"
        MASTERED = "mastered", "Mastered"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocabulary_items",
    )

    word = models.CharField(
        max_length=150,
    )

    meaning = models.TextField()

    translation = models.CharField(
        max_length=255,
        blank=True,
    )

    part_of_speech = models.CharField(
        max_length=20,
        choices=PartOfSpeech.choices,
        default=PartOfSpeech.OTHER,
    )

    example_sentence = models.TextField(
        blank=True,
    )

    mastery_level = models.CharField(
        max_length=20,
        choices=MasteryLevel.choices,
        default=MasteryLevel.NEW,
    )

    notes = models.TextField(
        blank=True,
    )

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
                fields=["user", "word"],
                name="unique_vocabulary_word_per_user",
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "mastery_level"],
                name="vocab_user_mastery_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.word}"