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