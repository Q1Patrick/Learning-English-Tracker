from django.contrib import admin

from .models import StudySession


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "activity_type",
        "duration_minutes",
        "score",
        "studied_at",
    )

    list_filter = (
        "activity_type",
        "studied_at",
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
        "-studied_at",
    )