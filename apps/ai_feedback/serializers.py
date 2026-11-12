from rest_framework import serializers

from .models import AIFeedback


class AIFeedbackCreateSerializer(serializers.Serializer):
    text = serializers.CharField(
        min_length=3,
        max_length=5000,
        trim_whitespace=True,
    )


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback

        fields = (
            "id",
            "original_text",
            "corrected_text",
            "overall_feedback",
            "grammar_score",
            "vocabulary_score",
            "clarity_score",
            "mistakes",
            "suggestions",
            "status",
            "model_name",
            "error_code",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class AIFeedbackHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback

        fields = (
            "id",
            "original_text",
            "corrected_text",
            "grammar_score",
            "vocabulary_score",
            "clarity_score",
            "status",
            "created_at",
            "error_code",
        )

        read_only_fields = fields
