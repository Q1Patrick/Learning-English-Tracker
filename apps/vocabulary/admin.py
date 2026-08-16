from django.contrib import admin

from .models import Vocabulary


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = (
        "word",
        "user",
        "part_of_speech",
        "mastery_level",
        "created_at",
    )

    list_filter = (
        "part_of_speech",
        "mastery_level",
    )

    search_fields = (
        "word",
        "meaning",
        "translation",
        "user__email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )