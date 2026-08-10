from django.contrib import admin

from .models import DailyGoal


@admin.register(DailyGoal)
class DailyGoalAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "target_date",
        "target_minutes",
        "created_at",
    )

    list_filter = (
        "target_date",
    )

    search_fields = (
        "user__email",
        "notes",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-target_date",
    )