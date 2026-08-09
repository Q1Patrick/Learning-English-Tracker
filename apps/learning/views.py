from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

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
#Build the List/Create API
class StudySessionListCreateView(ListCreateAPIView):
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )