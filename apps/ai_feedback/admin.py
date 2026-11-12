from django.contrib import admin

from .models import AIFeedback


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "error_code", "model_name", "created_at")
    list_filter = ("status", "error_code", "created_at")
    search_fields = ("id", "user__email")

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False
