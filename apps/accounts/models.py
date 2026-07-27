from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email


class UserProfile(models.Model):
    class EnglishLevel(models.TextChoices):
        BEGINNER = "A1", "A1"
        ELEMENTARY = "A2", "A2"
        INTERMEDIATE = "B1", "B1"
        UPPER_INTERMEDIATE = "B2", "B2"
        ADVANCED = "C1", "C1"
        PROFICIENT = "C2", "C2"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=100, blank=True)
    english_level = models.CharField(
        max_length=2,
        choices=EnglishLevel.choices,
        default=EnglishLevel.BEGINNER,
    )
    daily_target_minutes = models.PositiveIntegerField(default=30)
    learning_goal = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.email} profile"