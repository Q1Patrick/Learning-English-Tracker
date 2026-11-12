from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import DailyGoal

DUPLICATE_GOAL_MESSAGE = "You already have a goal for this date."


def _is_duplicate_goal_error(error):
    """Recognize the user/date uniqueness constraint on supported databases."""
    constraint_name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    return constraint_name == "unique_daily_goal_per_user_date" or str(error) == (
        "UNIQUE constraint failed: goals_dailygoal.user_id, goals_dailygoal.target_date"
    )


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
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_target_date(self, value):
        request = self.context.get("request")
        user = request.user if request else getattr(self.instance, "user", None)
        if user is not None and user.is_authenticated:
            duplicates = DailyGoal.objects.filter(user=user, target_date=value)
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError(DUPLICATE_GOAL_MESSAGE, code="duplicate_record")
        return value

    def save(self, **kwargs):
        try:
            with transaction.atomic():
                return super().save(**kwargs)
        except IntegrityError as error:
            if _is_duplicate_goal_error(error):
                raise serializers.ValidationError(
                    {"target_date": [DUPLICATE_GOAL_MESSAGE]}, code="duplicate_record"
                ) from error
            raise
