from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
## 
import uuid
from .managers import UserManager




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
    
#### Create the custom user model ####
class User(AbstractUser):
    """Application user who authenticates using an email address."""

    username = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email