from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True,db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    is_email_verified = models.BooleanField(
        default=False,
    )
    objects = UserManager()
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
    timezone = models.CharField(
        max_length=64,
        default="Asia/Ho_Chi_Minh",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.email} profile"