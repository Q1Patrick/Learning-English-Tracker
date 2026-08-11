from django.urls import path

from .views import (
    DailyGoalDetailView,
    DailyGoalListCreateView,
)


app_name = "goals"


urlpatterns = [
    path(
        "",
        DailyGoalListCreateView.as_view(),
        name="daily-goal-list-create",
    ),
    path(
        "<uuid:pk>/",
        DailyGoalDetailView.as_view(),
        name="daily-goal-detail",
    ),
]