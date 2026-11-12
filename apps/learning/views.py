from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.filters import filter_choice, filter_dates

from .models import StudySession
from .serializers import StudySessionSerializer


@api_view(["GET"])
def health_check(request):
    return Response(
        {
            "success": True,
            "status": "healthy",
            "message": "English Learning Tracker API is running.",
        }
    )


class StudySessionListCreateView(ListCreateAPIView):
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["notes"]

    def get_queryset(self):
        queryset = StudySession.objects.filter(user=self.request.user)
        queryset = filter_dates(queryset, self.request, "studied_at", datetime_field=True)
        return filter_choice(
            queryset, self.request, "activity_type", StudySession.ActivityType.choices
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudySessionDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user)
