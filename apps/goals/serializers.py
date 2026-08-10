from rest_framework import serializers

from .models import DailyGoal


class DailyGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyGoal
        fields = (
            "id",
            "target_date",
            "target_minutes",
            "notes",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_target_minutes(self, value):
        if value < 5:
            raise serializers.ValidationError(
                "Target must be at least 5 minutes."
            )

        if value > 480:
            raise serializers.ValidationError(
                "Target cannot exceed 480 minutes."
            )

        return value