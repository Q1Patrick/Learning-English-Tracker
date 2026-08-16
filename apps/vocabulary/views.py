from django.shortcuts import render

# Create your views here.
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import Vocabulary
from .serializers import VocabularySerializer


class VocabularyListCreateView(ListCreateAPIView):
    serializer_class = VocabularySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vocabulary.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )


class VocabularyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = VocabularySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vocabulary.objects.filter(
            user=self.request.user
        )