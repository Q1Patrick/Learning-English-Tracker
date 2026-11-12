"""Versioned API entry points."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.learning.urls")),
    path("api/v1/goals/", include("apps.goals.urls")),
    path("api/v1/statistic/", include("apps.statistic.urls")),
    path("api/v1/vocabulary/", include("apps.vocabulary.urls")),
    path("api/v1/ai-feedback/", include("apps.ai_feedback.urls")),
    path("api/v1/quizzes/", include("apps.quizzes.urls")),
]
