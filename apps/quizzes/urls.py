from django.urls import path

from .views import (
    QuizAttemptDetailView,
    QuizAttemptListView,
    QuizDetailView,
    QuizListView,
    QuizSubmitView,
)

app_name = "quizzes"

urlpatterns = [
    path("", QuizListView.as_view(), name="list"),
    path("attempts/", QuizAttemptListView.as_view(), name="attempt-list"),
    path("history/", QuizAttemptListView.as_view(), name="history"),
    path("attempts/<uuid:pk>/", QuizAttemptDetailView.as_view(), name="attempt-detail"),
    path("<uuid:pk>/", QuizDetailView.as_view(), name="detail"),
    path("<uuid:pk>/submit/", QuizSubmitView.as_view(), name="submit"),
]
