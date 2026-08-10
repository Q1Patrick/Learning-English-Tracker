import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class DailyGoal(models.Model):
    """Represents a user's study target for one specific day."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_goals",
    )

    target_date = models.DateField()

    target_minutes = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(5),
            MaxValueValidator(480),
        ],
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-target_date"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_date"],
                name="unique_daily_goal_per_user_date",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(target_minutes__gte=5)
                    & models.Q(target_minutes__lte=480)
                ),
                name="daily_goal_target_between_5_and_480",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.target_date} - "
            f"{self.target_minutes} min"
        )