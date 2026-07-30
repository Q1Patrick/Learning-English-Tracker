from django.contrib import admin
from .models import User, UserProfile
# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "english_level",
        "daily_target_minutes",
        "timezone",
        "created_at",
    )

    list_filter = (
        "english_level",
        "timezone",
        "created_at",
    )

    search_fields = (
        "user__email",
        "display_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )