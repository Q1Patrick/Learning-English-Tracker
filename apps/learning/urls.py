from django.urls import path

from .views import (
    StudySessionListCreateView,
    health_check,
)

app_name = "learning"
urlpatterns =[
    path("health/", health_check, name="health-check"),
        path("study-sessions/",StudySessionListCreateView.as_view(),name="study-session-list-create",),
]