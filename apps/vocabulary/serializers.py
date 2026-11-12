from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Vocabulary

DUPLICATE_WORD_MESSAGE = "You already have this word in your vocabulary."


def _is_duplicate_word_error(error):
    """Identify only this constraint, without hiding other database failures."""
    constraint_name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    return constraint_name == "unique_vocabulary_word_per_user" or str(error) == (
        "UNIQUE constraint failed: vocabulary_vocabulary.user_id, vocabulary_vocabulary.word"
    )


class VocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = (
            "id",
            "word",
            "meaning",
            "translation",
            "part_of_speech",
            "example_sentence",
            "mastery_level",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_word(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Word cannot be empty.")

        request = self.context.get("request")
        user = request.user if request else getattr(self.instance, "user", None)
        if user is not None and user.is_authenticated:
            duplicates = Vocabulary.objects.filter(user=user, word=value)
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError(DUPLICATE_WORD_MESSAGE, code="duplicate_record")
        return value

    def save(self, **kwargs):
        # Validation may become stale before the INSERT/UPDATE. The inner atomic
        # block rolls back its savepoint before translating a constraint error.
        try:
            with transaction.atomic():
                return super().save(**kwargs)
        except IntegrityError as error:
            if _is_duplicate_word_error(error):
                raise serializers.ValidationError(
                    {"word": [DUPLICATE_WORD_MESSAGE]}, code="duplicate_record"
                ) from error
            raise
