from django.urls import path

from .views import AIFeedbackCreateView, AIFeedbackDetailView, AIFeedbackHistoryView

app_name = "ai-feedback"

urlpatterns = [
    path("", AIFeedbackCreateView.as_view(), name="create"),
    path("history/", AIFeedbackHistoryView.as_view(), name="history"),
    path("<uuid:pk>/", AIFeedbackDetailView.as_view(), name="detail"),
]
