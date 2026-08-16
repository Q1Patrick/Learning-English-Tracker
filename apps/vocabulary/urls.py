from django.urls import path

from .views import (
    VocabularyDetailView,
    VocabularyListCreateView,
)


app_name = "vocabulary"


urlpatterns = [
    path(
        "",
        VocabularyListCreateView.as_view(),
        name="list-create",
    ),

    path(
        "<uuid:pk>/",
        VocabularyDetailView.as_view(),
        name="detail",
    ),
]