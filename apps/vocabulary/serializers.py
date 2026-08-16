from rest_framework import serializers

from .models import Vocabulary


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

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_word(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Word cannot be empty."
            )

        return value