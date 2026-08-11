from rest_framework import serializers

from .models import StudySession


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = (
            "id",
            "activity_type",
            "duration_minutes",
            "score",
            "notes",
            "studied_at",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_duration_minutes(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Duration must be at least 1 minute."
            )

        if value > 720:
            raise serializers.ValidationError(
                "Duration cannot exceed 720 minutes."
            )

        return value

    def validate_score(self, value):
        if value is None:
            return value

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Score must be between 0 and 100."
            )

        return value